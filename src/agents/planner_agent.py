"""
Planner Agent for creating travel itineraries.
"""
from typing import Any, Dict, List

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from ..config.settings import settings
from ..tools.planner_tools import planner_tools


class PlannerAgent:
    """Agent responsible for creating and managing travel plans."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            streaming=True,
            temperature=settings.openai_temperature
        )
        self.tools = planner_tools
        # OpenAI Tools Agent에 맞는 프롬프트를 생성합니다.
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 유능한 여행 계획 전문가입니다. "
             "사용자의 요청과 제공된 전체 대화 내용을 바탕으로 상세한 여행 계획을 세워주세요. "
             "당신의 결과물을 구조화하기 위해 'create_travel_plan' 도구를 사용하세요."),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        # OpenAI Tools Agent를 생성합니다.
        self.agent = create_openai_tools_agent(
            self.llm, self.tools, self.prompt)
        # AgentExecutor를 생성합니다.
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a travel plan using the OpenAI Tools agent."""
        try:
            # 에이전트 입력을 메시지 리스트로 구성합니다.
            messages = input_data.get("messages", [])

            response = await self.agent_executor.ainvoke({
                "messages": messages
            })

            return {
                "success": True,
                "data": response.get("output"),
                "message": "Travel plan created successfully."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred during planning."
            }

    def get_tools(self):
        """Returns the tools used by the agent."""
        return self.tools

    async def optimize_route(self, destinations: List[str]) -> List[str]:
        """Optimize travel route between destinations."""
        # TODO: Implement route optimization logic
        return destinations  # 임시로 입력을 그대로 반환

    async def calculate_budget(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed budget breakdown."""
        # TODO: Implement budget calculation
        return {}  # 임시로 빈 딕셔너리 반환

    async def get_weather_info(self, destination: str, dates: List[str]) -> Dict[str, Any]:
        """Get weather information for travel dates."""
        # TODO: Implement weather API integration
        return {}  # 임시로 빈 딕셔너리 반환
