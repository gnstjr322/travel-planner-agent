"""
Planner Agent for creating travel itineraries.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..prompts.base_prompts import prompt_manager
from ..prompts.guardrails import guardrail_system
from .base_agent import AgentResponse, BaseAgent


class PlannerAgent(BaseAgent):
    """Agent responsible for creating and managing travel plans."""

    def __init__(self, openai_api_key: str):
        super().__init__(
            name="PlannerAgent",
            description="Creates detailed travel itineraries and plans"
        )
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model="gpt-4-turbo-preview",
            streaming=True,
            temperature=0.3  # Lower temperature for more consistent planning
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create travel plan based on user requirements."""
        try:
            # Extract planning parameters
            destination = input_data.get("destination", "")
            start_date = input_data.get("start_date", "")
            end_date = input_data.get("end_date", "")
            budget = input_data.get("budget", "")
            preferences = input_data.get("preferences", [])
            group_size = input_data.get("group_size", 1)
            accommodation_type = input_data.get("accommodation_type", "")

            # Create planning prompt using template system
            system_prompt = prompt_manager.render_prompt("planner_system")
            user_prompt = prompt_manager.render_prompt(
                "planner_user",
                destination=destination or "목적지 미지정",
                start_date=start_date or "날짜 미지정",
                end_date=end_date or "날짜 미지정",
                budget=budget or "예산 미지정",
                group_size=group_size,
                accommodation_type=accommodation_type or "숙박 타입 미지정",
                travel_style="일반적인 여행",
                preferences=', '.join(preferences) if preferences else '없음',
                exclusions="없음"
            )

            # Check content with guardrails
            safety_check = guardrail_system.check_content(
                user_prompt, "PlannerAgent")

            if not safety_check["is_safe"]:
                return AgentResponse(
                    success=False,
                    error="부적절한 계획 요청",
                    message=safety_check["filtered_content"],
                    agent_name=self.name
                ).dict()

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            # Save to history
            self.add_to_history(HumanMessage(content=user_prompt))
            self.add_to_history(response)

            # Structure the response
            plan_data = {
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "budget": budget,
                "group_size": group_size,
                "itinerary": response.content,
                "created_at": datetime.now().isoformat()
            }

            return AgentResponse(
                success=True,
                data=plan_data,
                message="여행 계획이 성공적으로 생성되었습니다.",
                agent_name=self.name
            ).dict()

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                message="여행 계획 생성 중 오류가 발생했습니다.",
                agent_name=self.name
            ).dict()

    def get_tools(self) -> List[Any]:
        """Return planning tools."""
        return []

    async def optimize_route(self, destinations: List[str]) -> List[str]:
        """Optimize travel route between destinations."""
        # TODO: Implement route optimization logic
        pass

    async def calculate_budget(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed budget breakdown."""
        # TODO: Implement budget calculation
        pass

    async def get_weather_info(self, destination: str, dates: List[str]) -> Dict[str, Any]:
        """Get weather information for travel dates."""
        # TODO: Implement weather API integration
        pass
