# LangGraph를 이용한 여행 계획 멀티 에이전트 시스템

from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import InjectedToolCallId, tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.types import Command

from src.prompts.agent_prompts import AgentPrompts
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
        """더 이상 사용되지 않는 메서드"""
        pass

    def _create_location_search_agent(self):
        """더 이상 사용되지 않는 메서드"""
        pass

    def _create_calendar_agent(self):
        """더 이상 사용되지 않는 메서드"""
        pass

    def _create_share_agent(self):
        """더 이상 사용되지 않는 메서드"""
        pass

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
            prompt=AgentPrompts.get_prompt("supervisor"),
            name="supervisor",
        )

        # 3. Worker 에이전트 생성
        planner_agent = create_react_agent(
            model=self.llm,
            tools=[web_search_tool],
            prompt=AgentPrompts.get_prompt("planner_agent"),
            name="planner_agent"
        )
        location_search_agent = create_react_agent(
            model=self.llm,
            tools=[location_search_tool, nearby_search_tool],
            prompt=AgentPrompts.get_prompt("location_search_agent"),
            name="location_search_agent"
        )
        calendar_agent = create_react_agent(
            model=self.llm,
            tools=[
                add_travel_plan_to_calendar,
                check_calendar_availability,
                update_travel_plan_tool,
                delete_travel_plan_tool,
                search_travel_plan_tool
            ],
            prompt=AgentPrompts.get_prompt("calendar_agent"),
            name="calendar_agent"
        )
        share_agent = create_react_agent(
            model=self.llm,
            tools=[create_notion_page_tool],
            prompt=AgentPrompts.get_prompt("share_agent"),
            name="share_agent"
        )

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
