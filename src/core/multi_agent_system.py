"""
Supervisor-based Multi-Agent System using LangGraph.
"""
from typing import Any, List, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from ..agents.info_collection_agent import InfoCollectionAgent
from ..agents.planner_agent import PlannerAgent
from ..agents.search_agent import SearchAgent
from ..config.settings import settings


# Define the state for the graph
class AgentState(TypedDict):
    messages: List[BaseMessage]
    next: str
    query: Optional[str]


# Pydantic model for the supervisor's output
class SupervisorOutput(BaseModel):
    next: str
    query: Optional[str] = Field(
        description="The specific, targeted query to be passed to the SearchAgent. This should be a concrete search term like 'best restaurants in Seoul' or 'tourist attractions in Jeju'."
    )


class TravelPlannerSupervisor:
    """Supervisor for the travel planning multi-agent system."""

    def __init__(self):
        self.info_collection_agent = InfoCollectionAgent()
        self.search_agent = SearchAgent()
        self.planner_agent = PlannerAgent()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0
        )
        self.workflow = self._build_workflow()

    async def _supervisor_node(self, state: AgentState):
        """The supervisor node that routes to the next agent and generates queries."""
        supervisor_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "당신은 여행 계획을 돕는 AI 에이전트 팀의 슈퍼바이저입니다. "
                    "당신이 관리하는 에이전트는 정보 수집 'InfoCollectionAgent', 검색 'SearchAgent', 계획 수립 'PlannerAgent'가 있습니다.\n\n"
                    "**중요: 대화 기록을 주의깊게 분석하여 현재 상태를 정확히 판단하세요.**\n\n"
                    "다음 규칙을 신중하게 따르세요:\n"
                    "1. **정보 수집 단계**: 필수 정보(언제, 어디, 며칠, 여행컨셉)가 모두 없거나 일부만 있으면 'InfoCollectionAgent' 호출\n"
                    "2. **검색 단계**: '✅ 여행 정보가 수집되었습니다!' 메시지가 나타나면 정보 수집 완료로 판단하고 'SearchAgent' 호출\n"
                    "3. **계획 단계**: 검색 결과가 충분히 수집되면 'PlannerAgent' 호출\n"
                    "4. **완료**: 여행 계획이 완성되면 'FINISH'\n\n"
                    "**판단 기준:**\n"
                    "- 대화에 '✅ 여행 정보가 수집되었습니다!'가 있고 아직 검색하지 않았으면 → SearchAgent\n"
                    "- 관광지, 맛집, 숙소 등 검색 결과가 있고 아직 계획을 세우지 않았으면 → PlannerAgent\n"
                    "- 상세한 일정표나 여행 계획이 이미 완성되어 있으면 → FINISH\n"
                    "- 필수 정보(언제, 어디, 며칠, 여행컨셉) 중 하나라도 없으면 → InfoCollectionAgent\n\n"
                    "SearchAgent를 호출할 때는 수집된 정보를 바탕으로 구체적인 검색 쿼리를 생성하세요.\n"
                    "예: '서울 관광지', '부산 맛집', '제주도 호캉스 숙소' 등\n\n"
                    "당신은 반드시 'next'(호출할 에이전트 이름)와 'query'(SearchAgent에 전달할 검색어, 필요 없는 경우 빈 문자열) 두 개의 키를 가진 JSON 객체를 출력해야 합니다.",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        supervisor_chain = supervisor_prompt | self.llm.with_structured_output(
            schema=SupervisorOutput
        )
        result = await supervisor_chain.ainvoke({"messages": state["messages"]})
        # Type cast to SupervisorOutput to fix linter error
        supervisor_result = result if isinstance(
            result, SupervisorOutput) else SupervisorOutput(next="InfoCollectionAgent", query="")
        return {"next": supervisor_result.next, "query": supervisor_result.query or ""}

    async def _search_node(self, state: AgentState):
        """Node that runs the search agent with a specific query."""
        query = state.get("query")
        if not query:
            new_message = HumanMessage(
                content="Search failed: No query provided by supervisor.")
            return {"messages": state["messages"] + [new_message]}

        response = await self.search_agent.run({"query": query})

        if response.get("success"):
            content = response.get("data", "검색 결과가 없습니다.")
        else:
            content = response.get("message", "검색 중 오류가 발생했습니다.")

        new_message = HumanMessage(content=content)
        return {"messages": state["messages"] + [new_message]}

    async def _info_collection_node(self, state: AgentState):
        """Node that runs the info collection agent."""
        response = await self.info_collection_agent.run({"messages": state["messages"]})

        if response.get("success"):
            content = response.get("data", "정보 수집을 완료하지 못했습니다.")
        else:
            content = response.get("message", "정보 수집 중 오류가 발생했습니다.")

        new_message = HumanMessage(content=content)
        return {"messages": state["messages"] + [new_message]}

    async def _planner_node(self, state: AgentState):
        """Node that runs the planner agent."""
        # The planner agent now takes the whole message history.
        response = await self.planner_agent.run({"messages": state["messages"]})

        if response.get("success"):
            content = response.get("data", "계획을 생성하지 못했습니다.")
        else:
            content = response.get("message", "계획 생성 중 오류가 발생했습니다.")

        new_message = HumanMessage(content=content)
        return {"messages": state["messages"] + [new_message]}

    def _build_workflow(self):
        """Build the LangGraph workflow for the supervisor and agents."""
        graph = StateGraph(AgentState)
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("InfoCollectionAgent", self._info_collection_node)
        graph.add_node("SearchAgent", self._search_node)
        graph.add_node("PlannerAgent", self._planner_node)

        graph.add_edge("InfoCollectionAgent", "supervisor")
        graph.add_edge("SearchAgent", "supervisor")
        graph.add_edge("PlannerAgent", "supervisor")

        graph.add_conditional_edges(
            "supervisor",
            lambda state: state["next"],
            {
                "InfoCollectionAgent": "InfoCollectionAgent",
                "SearchAgent": "SearchAgent",
                "PlannerAgent": "PlannerAgent",
                "FINISH": END,
            },
        )
        graph.set_entry_point("supervisor")

        return graph.compile()

    async def process_query(self, query: str, conversation_history: Optional[List[BaseMessage]] = None) -> dict:
        """Process a user query through the multi-agent system using the supervisor."""
        if conversation_history is None:
            conversation_history = []

        # 새로운 사용자 메시지 추가
        conversation_history.append(HumanMessage(content=query))

        # 초기 상태 설정
        initial_state = {
            "messages": conversation_history,
            "next": "",
            "query": ""
        }

        try:
            # 슈퍼바이저가 관리하는 워크플로우 실행 (recursion limit 설정)
            final_state = await self.workflow.ainvoke(
                initial_state,
                config={"recursion_limit": 10}
            )

            # 최종 메시지 추출
            final_messages = final_state.get("messages", [])
            if final_messages:
                # 마지막 메시지가 응답
                last_message = final_messages[-1]
                response_content = last_message.content

                return {
                    "success": True,
                    "response": response_content,
                    "conversation_history": final_messages
                }
            else:
                return {
                    "success": False,
                    "response": "워크플로우에서 응답을 생성하지 못했습니다."
                }

        except Exception as e:
            return {
                "success": False,
                "response": f"워크플로우 실행 중 오류가 발생했습니다: {str(e)}"
            }
