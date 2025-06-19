"""
Multi-Agent System using LangGraph for Travel Planning.
"""
from typing import Any, Dict, List, Optional

from langchain.schema import HumanMessage
from langgraph.graph import END, StateGraph
# LangGraph의 상태를 위한 Pydantic 모델 정의
from pydantic import BaseModel

from ..agents.base_agent import AgentResponse
from ..agents.calendar_agent import CalendarAgent
from ..agents.planner_agent import PlannerAgent
from ..agents.search_agent import SearchAgent
from ..agents.share_agent import ShareAgent
from ..utils.logger import logger


class TravelPlannerState(BaseModel):
    messages: List[Any] = []
    current_step: str = "start"
    user_query: str = ""
    search_results: Optional[Dict[str, Any]] = None
    travel_plan: Optional[Dict[str, Any]] = None
    calendar_events: Optional[List[Dict[str, Any]]] = None
    shared_plan: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed: bool = False


class TravelPlannerMultiAgent:
    """Multi-Agent system for travel planning using LangGraph."""

    def __init__(self, openai_api_key: str):
        if not openai_api_key:
            raise ValueError("OpenAI API 키가 필요합니다.")
        self.openai_api_key = openai_api_key

        # Initialize agents
        self.search_agent = SearchAgent(openai_api_key=self.openai_api_key)
        self.planner_agent = PlannerAgent(openai_api_key=self.openai_api_key)
        self.calendar_agent = CalendarAgent()
        self.share_agent = ShareAgent(openai_api_key=self.openai_api_key)

        # Build the workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(TravelPlannerState)  # Pydantic 모델을 스키마로 사용

        # Define nodes
        workflow.add_node("router", self._router_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("planner", self._plan_node)
        workflow.add_node("calendar", self._calendar_node)
        workflow.add_node("share", self._share_node)

        # Define edges
        workflow.set_entry_point("router")

        conditional_map = {
            "search": "search",
            "planner": "planner",
            "calendar": "calendar",
            "share": "share",
            "end": END,
        }
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            conditional_map,
        )

        workflow.add_edge("search", END)
        workflow.add_edge("planner", END)
        workflow.add_edge("calendar", END)
        workflow.add_edge("share", END)

        return workflow.compile()

    async def _router_node(self, state: TravelPlannerState) -> TravelPlannerState:
        """Determine the next step based on the user query."""
        user_query = state.user_query.lower()
        next_step = self._route_query(state)
        state.current_step = next_step
        log_message = (
            f"Routing to: {next_step} for query: '{user_query}'"
        )
        logger.info(log_message)
        return state

    def _route_decision(self, state: TravelPlannerState) -> str:
        """Decide which node to route to next based on current_step."""
        current_step = state.current_step
        logger.info(f"Decision: Routing to '{current_step}'")
        if current_step in ["search", "planner", "calendar", "share"]:
            return current_step
        return "end"

    async def _search_node(self, state: TravelPlannerState) -> TravelPlannerState:
        """Handle search requests."""
        try:
            user_query = state.user_query
            logger.info(f"Search node processing query: '{user_query}'")

            result_dict = await self.search_agent.process(
                input_data={"query": user_query, "context": None}
            )

            response = AgentResponse(**result_dict)
            state.search_results = response.data
            state.completed = True
            logger.info("Search node completed.")
        except Exception as e:
            error_msg = f"Search operation failed: {str(e)}"
            logger.error(f"Search node execution failed: {str(e)}")
            state.error = error_msg
            state.completed = True
        return state

    async def _plan_node(self, state: TravelPlannerState) -> TravelPlannerState:
        """Handle travel planning requests."""
        try:
            user_query = state.user_query
            search_results = state.search_results
            logger.info(f"Planner node processing query: '{user_query}'")

            context_data = {
                "user_query": user_query,
                "search_results": search_results,
            }

            result_dict = await self.planner_agent.process(
                input_data={"query": user_query, "context": context_data}
            )

            response = AgentResponse(**result_dict)
            state.travel_plan = response.data
            state.completed = True
            logger.info("Planner node completed.")
        except Exception as e:
            error_msg = f"Planning operation failed: {str(e)}"
            logger.error(f"Planner node execution failed: {str(e)}")
            state.error = error_msg
            state.completed = True
        return state

    def _calendar_node(self, state: TravelPlannerState) -> TravelPlannerState:
        """Handle calendar operations."""
        try:
            user_query = state.user_query
            logger.info(f"Calendar node processing query: '{user_query}'")

            travel_plan = state.travel_plan
            search_results = state.search_results

            context_data = {
                "travel_info": travel_plan,
                "destination_details": search_results
            }

            response = self.calendar_agent.process(
                query=user_query, context=context_data
            )

            state.calendar_events = [response.data] if response.data else []
            state.completed = True
            logger.info("Calendar node completed.")

        except Exception as e:
            error_msg = f"Calendar operation failed: {str(e)}"
            logger.error(f"Calendar node execution failed: {str(e)}")
            state.error = error_msg
            state.completed = True
        return state

    async def _share_node(self, state: TravelPlannerState) -> TravelPlannerState:
        """Handle sharing requests."""
        try:
            user_query = state.user_query
            logger.info(f"Share node processing query: '{user_query}'")

            travel_plan = state.travel_plan
            if not travel_plan:
                logger.warning("No travel plan found to share.")
                state.error = "No travel plan to share."
                state.completed = True
                return state

            context_data = {
                "plan_data": travel_plan,
                "share_method": "kakao"
            }

            result_dict = await self.share_agent.process(
                input_data={"query": user_query, "context": context_data}
            )

            response = AgentResponse(**result_dict)
            state.shared_plan = response.data
            state.completed = True
            logger.info("Share node completed.")

        except Exception as e:
            error_msg = f"Share operation failed: {str(e)}"
            logger.error(f"Share node execution failed: {str(e)}")
            state.error = error_msg
            state.completed = True
        return state

    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process a user query through the multi-agent system."""
        initial_state = TravelPlannerState(
            messages=[HumanMessage(content=user_query)],
            user_query=user_query,
            current_step="start"
        )

        final_state = await self.workflow.ainvoke(initial_state.dict())

        return final_state

    def _route_query(self, state: TravelPlannerState) -> str:
        """
        Determines the next step based on user query analysis.
        This is a simplified keyword-based router.
        A more advanced implementation would use an LLM call.
        """
        query = state.user_query.lower()

        if "검색" in query or "찾아줘" in query or "알려줘" in query:
            return "search"
        if "계획" in query or "세워줘" in query or "짜줘" in query:
            return "planner"
        if "캘린더" in query or "일정" in query or "등록" in query:
            return "calendar"
        if "공유" in query or "보내줘" in query:
            return "share"

        # Default to planner if no specific keyword is found
        # but there is a substantive query
        if len(query.split()) > 2:
            return "planner"

        return "end"
