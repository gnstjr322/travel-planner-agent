from typing import List

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field


class PlanInput(BaseModel):
    """Input schema for create_travel_plan tool."""
    query: str = Field(
        description="The user's original request for the travel plan.")
    search_results: str = Field(
        description="The context or search results to be used for creating the plan."
    )


def create_plan(query: str, search_results: str) -> str:
    """
    사용자의 요청과 검색 결과를 바탕으로 여행 계획 초안을 작성합니다.
    이 함수는 상세한 일정을 생성하기보다는, 주어진 정보를 요약하고 구조화하여
    Planner 에이전트가 최종 계획을 수립하는 데 사용할 기본 틀을 제공합니다.

    Args:
        query: 사용자의 원래 요청 (예: "제주도 3박 4일 여행 계획 세워줘")
        search_results: Search 에이전트가 찾은 관련 정보 (장소, 활동 등)

    Returns:
        구조화된 여행 계획 초안 문자열
    """
    if not search_results:
        search_results = "관련 검색 결과 없음. 사용자의 요청에만 기반하여 계획을 세워야 함."

    plan_prompt = f"""
    # 여행 계획 초안 작성

    ## 사용자 요청
    {query}

    ## 사전 조사 내용
    {search_results}

    ## 지시사항
    위 사용자 요청과 사전 조사 내용을 바탕으로, 여행의 기본 개요를 포함하는 계획 초안을 작성해주세요.
    - 여행 목적지
    - 여행 기간
    - 추천 활동 및 방문 장소 목록
    - 기타 고려사항

    이 정보들을 바탕으로 최종 계획을 세울 수 있도록 명확하고 간결하게 정리합니다.
    """

    # 실제로는 이 프롬프트를 LLM에 전달하여 계획을 생성하겠지만,
    # 여기서는 도구의 기본 구조를 보여주기 위해 프롬프트 자체를 반환합니다.
    # PlannerAgent가 이 내용을 바탕으로 최종 계획을 생성하게 됩니다.
    return plan_prompt


create_plan_tool = StructuredTool.from_function(
    func=create_plan,
    name="create_travel_plan",
    description="사용자의 요청과 검색 결과를 바탕으로 여행 계획 초안을 작성하는 데 사용됩니다.",
    args_schema=PlanInput,
)

planner_tools: List[StructuredTool] = [create_plan_tool]
