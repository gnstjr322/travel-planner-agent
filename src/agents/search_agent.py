"""
Search Agent for finding travel destinations and places.
"""
import json
from typing import Any, Dict, List

import aiohttp
from langchain.schema import AIMessage, HumanMessage
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

from ..prompts.base_prompts import prompt_manager
from ..prompts.guardrails import guardrail_system
from ..services.duckduckgo_service import duckduckgo_service
from ..services.kakao_service import kakao_service
from .base_agent import AgentResponse, BaseAgent


class SearchAgent(BaseAgent):
    """Agent responsible for searching travel destinations and places."""

    def __init__(self, openai_api_key: str):
        super().__init__(
            name="SearchAgent",
            description="Searches for travel destinations, attractions, and places using various APIs"
        )
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model="gpt-4-turbo-preview",
            streaming=True,
            temperature=0.7
        )
        self.tools = self._initialize_tools()

    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize search tools."""
        # TODO: Implement Kakao Map API, Naver API tools
        return []

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process search request."""
        try:
            query = input_data.get("query", "")
            location = input_data.get("location", "")
            category = input_data.get("category", "tourist_spot")

            # Create search prompt using template system
            system_prompt = prompt_manager.render_prompt("search_system")
            user_prompt = prompt_manager.render_prompt(
                "search_user",
                query=query,
                location=location or "지역 무관",
                category=category,
                additional_conditions="없음"
            )

            # Check content with guardrails
            safety_check = guardrail_system.check_content(
                user_prompt, "SearchAgent")

            if not safety_check["is_safe"]:
                return AgentResponse(
                    success=False,
                    error="부적절한 검색 요청",
                    message=safety_check["filtered_content"],
                    agent_name=self.name
                ).dict()

            # Process with LLM
            messages = [
                HumanMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = await self.llm.ainvoke(messages)

            self.add_to_history(HumanMessage(content=query))
            self.add_to_history(response)

            return AgentResponse(
                success=True,
                data={
                    "search_results": response.content,
                    "query": query,
                    "location": location
                },
                message="검색이 완료되었습니다.",
                agent_name=self.name
            ).dict()

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                message="검색 중 오류가 발생했습니다.",
                agent_name=self.name
            ).dict()

    def get_tools(self) -> List[Any]:
        """Return search tools."""
        return self.tools

    async def search_kakao_places(self, query: str, location: str = "") -> Dict[str, Any]:
        """Search places using Kakao Map API."""
        try:
            # Use KakaoMapService for actual API call
            places = await kakao_service.search_places(
                query=query,
                location=location if location else None,
                limit=10
            )

            return {
                "success": True,
                "places": places,
                "count": len(places),
                "source": "kakao"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "places": [],
                "source": "kakao"
            }

    async def search_web_info(self, query: str) -> Dict[str, Any]:
        """Search web information using DuckDuckGo API."""
        try:
            # Use DuckDuckGo for free web search
            result = await duckduckgo_service.search_web(query)

            if result['success']:
                return {
                    "success": True,
                    "query": query,
                    "abstract": result.get('abstract', ''),
                    "instant_answer": result.get('instant_answer', ''),
                    "related_topics": result.get('related_topics', []),
                    "results": result.get('results', []),
                    "source": "duckduckgo"
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'Unknown error'),
                    "query": query,
                    "source": "duckduckgo"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "source": "duckduckgo"
            }
