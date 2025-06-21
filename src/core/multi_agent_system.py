# LangGraph를 이용한 여행 계획 멀티 에이전트 시스템

from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import InjectedToolCallId, tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.types import Command

from src.tools.calendar_tools import (add_travel_plan_to_calendar,
                                      check_calendar_availability,
                                      delete_travel_plan_tool,
                                      search_travel_plan_tool,
                                      update_travel_plan_tool)
from src.tools.planner_tools import web_search_tool
from src.tools.search_tools import location_search_tool, nearby_search_tool
from src.tools.share_tools import create_notion_page_tool
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_handoff_tool(*, agent_name: str, description: str | None = None):
    """
    특정 에이전트에게 제어권을 넘겨주는 handoff 도구를 생성합니다.
    이 도구를 호출하면, 그래프는 지정된 에이전트로 이동합니다.
    """
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        # Command.PARENT를 사용하여 부모 그래프(supervisor)의 상태를 업데이트하고 이동합니다.
        return Command(
            goto=agent_name,
            update={**state, "messages": state["messages"] + [tool_message]},
            graph=Command.PARENT,
        )

    return handoff_tool


class TravelMultiAgentSystem:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.app = None

    def _get_agent_name(self, messages: list) -> str | None:
        """메시지에서 라우팅할 에이전트 이름을 가져옵니다."""
        last_message = messages[-1]
        # ToolMessage에는 tool_calls 속성이 없으므로, 확인 후 접근해야 합니다.
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_name = last_message.tool_calls[0]['name']
            if tool_name.startswith("transfer_to_"):
                return tool_name.replace("transfer_to_", "")
        return None

    def route_to_next_agent(self, state: MessagesState):
        """다음 에이전트로 라우팅하거나 대화를 종료합니다."""
        agent_name = self._get_agent_name(state["messages"])
        if agent_name:
            # handoff 도구가 호출된 경우 해당 에이전트로 이동
            return agent_name
        # Supervisor가 도구를 호출하지 않고 메시지만 생성한 경우, 종료
        return END

    def _create_planner_agent(self):
        """PlannerAgent 생성 - 여행 일정 초안 작성 및 최종 완성 담당"""
        system_prompt = (
            "당신은 여행 일정 계획 전문가이며, 당신의 임무는 두 단계로 나뉩니다.\n\n"
            "**1단계: 초기 계획 수립 (첫 번째 호출 시)**\n"
            "- **필수 행동:** 사용자의 요청을 받으면, **반드시 `web_search_tool`을 사용**하여 관련 정보를 검색해야 합니다. **절대 당신의 기존 지식에 의존해서 계획을 세우면 안 됩니다.**\n"
            "- **목표:** 웹 검색 결과를 바탕으로, 방문할 장소, 맛집, 카페 등이 포함된 기본적인 여행 일정의 틀(초안)을 만듭니다.\n"
            "- **중요:** 검색 결과에 나온 장소들의 이름과 특징을 명확하게 포함하여 초안을 작성하세요.\n\n"
            "**2단계: 최종 계획 완성 (두 번째 호출 시)**\n"
            "- **조건:** `location_search_agent`로부터 상세한 장소 정보(주소, 전화번호 등)를 전달받았을 때 이 단계를 수행합니다.\n"
            "- **금지 행동:** 이 단계에서는 **절대 `web_search_tool`을 다시 사용하지 마세요.**\n"
            "- **목표:** 전달받은 상세 정보를 기존 초안에 통합하여, 완전하고 실행 가능한 최종 여행 계획을 완성합니다.\n\n"
            "현재 대화 기록을 보고 1단계와 2단계 중 어떤 작업을 수행해야 할지 판단한 후, 규칙에 따라 임무를 완수하고 Supervisor에게 보고하세요."
        )
        return create_react_agent(
            model=self.llm,
            tools=[web_search_tool],
            prompt=system_prompt,
            name="planner_agent"
        )

    def _create_location_search_agent(self):
        """LocationSearchAgent 생성 - 카카오맵 기반 장소 정보 검색 담당"""
        system_prompt = (
            "당신은 카카오맵 API를 사용하여 장소의 상세 정보를 **정확하게** 검색하는 전문가입니다.\n\n"
            "**절대적으로 따라야 할 규칙:**\n"
            "1. Supervisor로부터 받은 여행 계획 초안에서 **장소 이름**(예: '일산 호수공원', '행주산성')을 정확히 추출합니다.\n"
            "2. `location_search_tool`을 사용할 때, `query` 인자에는 추출한 장소 이름 **'그 자체'**만 넣어야 합니다.\n"
            "   - **절대, 절대로** `query`에 '관광지', '맛집', '고양시' 등 부가적인 단어를 임의로 추가하지 마세요.\n"
            "   - 예시 (올바른 사용): `location_search_tool(query='일산 호수공원')`\n"
            "   - 예시 (잘못된 사용): `location_search_tool(query='일산 호수공원 관광지')` 또는 `location_search_tool(query='고양시 일산 호수공원')`\n"
            "3. 초안에 있는 모든 장소에 대해, 이 규칙을 지켜 **하나씩** 검색을 수행해야 합니다.\n"
            "4. 모든 검색이 끝나면, 수집된 정보를 정리하여 Supervisor에게 보고하세요."
            "주의: 사용자가 의뢰한 지역이 아닌 다른 지역의 장소는 제외시켜야합니다."
        )
        return create_react_agent(
            model=self.llm,
            tools=[location_search_tool, nearby_search_tool],
            prompt=system_prompt,
            name="location_search_agent"
        )

    def _create_calendar_agent(self):
        """CalendarAgent 생성 - 완성된 여행 계획을 캘린더에 등록 담당"""
        system_prompt = (
            "당신은 여행 계획을 카카오 캘린더에 등록, 수정, 삭제하는 전문가입니다.\n\n"
            "**임무:**\n"
            "1. Supervisor로부터 완성된 여행 계획을 전달받습니다.\n"
            "2. 계획에서 여행 목적지, 날짜, 활동 등의 정보를 파악합니다.\n"
            "3. 다음 도구들을 상황에 맞게 사용할 수 있습니다:\n"
            "   - `add_travel_plan_to_calendar`: 새 여행 계획 등록\n"
            "   - `update_travel_plan_tool`: 기존 여행 계획 수정\n"
            "   - `delete_travel_plan_tool`: 여행 계획 삭제\n"
            "   - `check_calendar_availability`: 일정 조회(충돌 확인)\n"
            "   - `search_travel_plan_tool`: 여행 일정 검색\n"
            "4. 작업 결과와 임무 종료를 Supervisor에게 보고합니다.\n\n"
            "**추가 시나리오 처리 가이드:**\n"
            "- 사용자가 이미 등록된 일정에 대해 수정을 요청하는 경우:\n"
            "  1. `search_travel_plan_tool`을 사용하여 일정을 검색하고 이벤트 ID를 안내합니다.\n"
            "  2. 이벤트 ID를 확인한 후, `update_travel_plan_tool`을 사용하여 수정합니다.\n"
            "  3. 수정 가능한 항목: 제목, 날짜, 설명 등\n"
            "- 사용자가 일정 삭제를 요청하는 경우:\n"
            "  1. `search_travel_plan_tool`로 삭제할 일정을 찾도록 안내합니다.\n"
            "  2. `delete_travel_plan_tool`을 사용하여 해당 일정을 삭제합니다.\n\n"
            "**중요 사항:**\n"
            "- 사용자가 명시적으로 날짜를 제공했거나, 계획에 구체적인 날짜가 포함된 경우에만 캘린더 등록을 시도하세요.\n"
            "- 날짜 정보가 부족한 경우, 사용자에게 추가 정보를 요청하는 메시지를 제공하세요.\n"
            "- `check_calendar_availability` 도구로 일정 충돌을 미리 확인할 수 있습니다.\n"
            "- 사용자가 년도를 명시하지 않은 경우, 2025년이라고 인식하세요.\n"
            "- 모든 작업 시 사용자에게 명확하고 친절한 안내 메시지를 제공하세요."
        )
        return create_react_agent(
            model=self.llm,
            tools=[
                add_travel_plan_to_calendar,
                check_calendar_availability,
                update_travel_plan_tool,
                delete_travel_plan_tool,
                search_travel_plan_tool
            ],
            prompt=system_prompt,
            name="calendar_agent"
        )

    def _create_share_agent(self):
        """ShareAgent 생성 - 완성된 여행 계획을 노션에 공유하고 캘린더 등록 여부 확인"""
        system_prompt = (
            "당신은 완성된 여행 계획을 노션에 공유하고 사용자의 추가 요청을 처리하는 전문가입니다.\n\n"
            "**주요 임무:**\n"
            "1. Supervisor로부터 완성된 여행 계획을 전달받습니다.\n"
            "2. `create_notion_page_tool`을 사용하여 여행 계획을 노션 페이지로 생성합니다.\n"
            "3. 노션 공유 완료 후 사용자에게 '이 계획을 카카오 캘린더에 등록하시겠습니까?' 질문을 합니다.\n"
            "4. 사용자의 응답에 따라 적절한 안내를 제공합니다.\n\n"
            "**노션 페이지 포맷팅:**\n"
            "- 제목: '[목적지] 여행 계획 - [날짜]' 형식으로 생성\n"
            "- 내용: 여행 계획을 구조화하여 읽기 쉽게 정리\n"
            "- 이모지를 활용하여 시각적 효과 추가\n\n"
            "**중요 사항:**\n"
            "- 노션 페이지 생성 성공 시 반드시 링크를 사용자에게 제공\n"
            "- 친근하고 도움이 되는 톤으로 응답\n"
            "- 캘린더 등록 질문은 노션 공유 완료 후에만 진행\n"
            "- 작업 완료 후 Supervisor에게 결과를 보고"
        )
        return create_react_agent(
            model=self.llm,
            tools=[create_notion_page_tool],
            prompt=system_prompt,
            name="share_agent"
        )

    def build_graph(self):
        """Handoff 통신 방식을 사용한 멀티 에이전트 그래프 구성"""

        # 1. Handoff 도구 생성
        assign_to_planner_agent = create_handoff_tool(
            agent_name="planner_agent",
            description="여행 계획 초안을 만들거나 최종 계획을 완성하도록 planner_agent에게 작업을 할당합니다.",
        )
        assign_to_location_search_agent = create_handoff_tool(
            agent_name="location_search_agent",
            description="계획에 필요한 장소의 상세 정보를 찾아오도록 location_search_agent에게 작업을 할당합니다.",
        )
        assign_to_calendar_agent = create_handoff_tool(
            agent_name="calendar_agent",
            description="완성된 여행 계획을 카카오 캘린더에 등록하도록 calendar_agent에게 작업을 할당합니다.",
        )
        assign_to_share_agent = create_handoff_tool(
            agent_name="share_agent",
            description="완성된 여행 계획을 노션에 공유하고 캘린더 등록 여부를 확인하도록 share_agent에게 작업을 할당합니다.",
        )

        # 2. Supervisor 에이전트 생성 (Handoff 도구 사용)
        supervisor_agent = create_react_agent(
            model=self.llm,
            tools=[assign_to_planner_agent,
                   assign_to_location_search_agent,
                   assign_to_calendar_agent,
                   assign_to_share_agent],
            prompt=(
                "당신은 여행 계획 프로젝트를 총괄하는 Supervisor입니다.\n"
                "당신의 팀은 `planner_agent`, `location_search_agent`, `calendar_agent`, `share_agent`로 구성되어 있습니다.\n\n"
                "**기본 작업 흐름:**\n"
                "1. 사용자가 요청하면 `planner_agent`에게 작업을 할당하여 여행 초안을 만드세요.\n"
                "2. `planner_agent`가 초안을 완성하면, 그 내용을 `location_search_agent`에게 할당하여 장소의 상세 정보를 검색하게 하세요.\n"
                "3. `location_search_agent`가 정보를 수집하면, 다시 `planner_agent`에게 할당하여 최종 계획을 완성하게 하세요.\n"
                "4. `planner_agent`가 최종 계획을 보고하면, **그 계획을 절대 수정하거나 요약하지 말고, 원문 그대로 사용자에게 전달해야 합니다.**\n\n"
                "**캘린더 관련 작업 처리 가이드:**\n"
                "5. 사용자의 요청이 캘린더 관련 작업(수정, 삭제 등)인 경우:\n"
                "   - 요청을 `calendar_agent`에게 즉시 할당합니다.\n"
                "   - `calendar_agent`는 다음과 같은 도구들을 사용할 수 있습니다:\n"
                "     a. `search_travel_plan_tool`: 일정 검색\n"
                "     b. `update_travel_plan_tool`: 일정 수정\n"
                "     c. `delete_travel_plan_tool`: 일정 삭제\n"
                "   - `calendar_agent`의 응답을 그대로 사용자에게 전달합니다.\n\n"
                "**요청 분류 규칙:**\n"
                "- 새로운 여행 계획 요청: `planner_agent`에게 할당\n"
                "- 장소 상세 정보 필요: `location_search_agent`에게 할당\n"
                "- 캘린더 관련 작업(조회/수정/삭제): `calendar_agent`에게 할당\n"
                "- 여행 계획 공유 요청: `share_agent`에게 할당\n\n"
                "**최종 보고 규칙 (가장 중요):**\n"
                "- `planner_agent`로부터 최종 계획을 받으면, 당신의 마지막 임무는 그것을 사용자에게 전달하는 것입니다.\n"
                "- 당신의 최종 메시지는 **반드시 `planner_agent`가 작성한 여행 계획 전체 내용을 포함**해야 합니다.\n"
                "- 그 계획 아래에 '이 계획을 **캘린더**나 **노션**에 등록하시겠습니까?' 라는 질문을 덧붙여야 합니다.\n\n"
                "**규칙:**\n"
                "- 당신은 직접 작업을 수행하지 않고, 오직 도구를 사용하여 작업을 할당해야 합니다.\n"
                "- 최종 보고 단계 이전에는 한 번에 하나의 에이전트에게만 작업을 할당하세요.\n"
                "- `planner_agent`가 최종 계획을 보고한 후에는, **절대 다른 도구를 호출하지 말고**, 위 최종 보고 규칙에 따라 사용자에게 답변하며 작업을 종료하세요."
            ),
            name="supervisor",
        )

        # 3. Worker 에이전트 생성
        planner_agent = self._create_planner_agent()
        location_search_agent = self._create_location_search_agent()
        calendar_agent = self._create_calendar_agent()
        share_agent = self._create_share_agent()

        # 4. 멀티 에이전트 그래프 생성
        supervisor_graph = StateGraph(MessagesState)

        supervisor_graph.add_node("supervisor", supervisor_agent)
        supervisor_graph.add_node("planner_agent", planner_agent)
        supervisor_graph.add_node(
            "location_search_agent", location_search_agent)
        supervisor_graph.add_node("calendar_agent", calendar_agent)
        supervisor_graph.add_node("share_agent", share_agent)

        # 5. 에이전트 간의 작업 흐름 정의
        supervisor_graph.add_edge(START, "supervisor")

        # Supervisor의 출력에 따라 다음 노드를 결정하는 조건부 엣지
        supervisor_graph.add_conditional_edges(
            "supervisor",
            self.route_to_next_agent,
            {
                "planner_agent": "planner_agent",
                "location_search_agent": "location_search_agent",
                "calendar_agent": "calendar_agent",
                "share_agent": "share_agent",
                END: END,
            },
        )

        # 각 Worker 에이전트는 작업 완료 후 항상 Supervisor에게 제어권을 반환합니다.
        supervisor_graph.add_edge("planner_agent", "supervisor")
        supervisor_graph.add_edge("location_search_agent", "supervisor")
        supervisor_graph.add_edge("calendar_agent", "supervisor")
        supervisor_graph.add_edge("share_agent", "supervisor")

        # Supervisor는 handoff 도구를 사용하여 다른 노드로 제어권을 넘겨줍니다.
        # Graph는 END 상태에 도달하거나, Supervisor가 더 이상 도구를 호출하지 않을 때 종료됩니다.

        self.app = supervisor_graph.compile(checkpointer=MemorySaver())
        return self.app

    def stream(self, user_input: str, config: dict = None):
        """사용자 입력을 받아 멀티 에이전트 시스템을 스트림으로 실행"""
        if not self.app:
            self.build_graph()

        inputs = {"messages": [HumanMessage(content=user_input)]}
        if config is None:
            config = {"configurable": {"thread_id": "travel-chat-handoff"}}

        # LangGraph 튜토리얼의 'from scratch' 방식에 따라 subgraphs=True 옵션을 사용하지 않습니다.
        for chunk in self.app.stream(inputs, config):
            yield chunk
