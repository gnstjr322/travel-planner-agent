# 여행 계획 도구들

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from langchain_core.tools import tool

from src.services.duckduckgo_service import DuckDuckGoService
from src.services.google_search_service import GoogleSearchService
from src.services.tavily_service import TavilyService

duckduckgo_service = DuckDuckGoService()
google_search_service = GoogleSearchService()
tavily_service = TavilyService()


@tool
def create_travel_plan_tool(
    destination: str,
    duration: int,
    theme: str = "일반",
    travelers: int = 1
) -> str:
    """여행 계획을 생성하는 도구

    Args:
        destination: 여행 목적지
        duration: 여행 일수
        theme: 여행 테마 (일반, 맛집, 자연, 문화, 가족 등)
        travelers: 여행자 수

    Returns:
        생성된 여행 계획 JSON 문자열
    """
    try:
        # 기본 여행 계획 구조 생성
        travel_plan = {
            "destination": destination,
            "duration": duration,
            "theme": theme,
            "travelers": travelers,
            "created_at": datetime.now().isoformat(),
            "itinerary": []
        }

        # 일수별 기본 일정 틀 생성
        for day in range(1, duration + 1):
            day_plan = {
                "day": day,
                "date": (datetime.now() + timedelta(days=day-1)).strftime("%Y-%m-%d"),
                "activities": [
                    {"time": "09:00", "activity": f"{destination} 여행 {day}일차 시작",
                        "location": "숙소"},
                    {"time": "12:00", "activity": "점심 식사", "location": "미정"},
                    {"time": "15:00", "activity": "관광 활동", "location": "미정"},
                    {"time": "18:00", "activity": "저녁 식사", "location": "미정"},
                    {"time": "21:00", "activity": "휴식", "location": "숙소"}
                ]
            }
            travel_plan["itinerary"].append(day_plan)

        return json.dumps(travel_plan, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"여행 계획 생성 중 오류가 발생했습니다: {str(e)}"


@tool
def modify_travel_plan_tool(plan_json: str, modifications: str) -> str:
    """기존 여행 계획을 수정하는 도구

    Args:
        plan_json: 기존 여행 계획 JSON 문자열
        modifications: 수정 사항 설명

    Returns:
        수정된 여행 계획 JSON 문자열
    """
    try:
        plan = json.loads(plan_json)
        plan["modified_at"] = datetime.now().isoformat()
        plan["modifications"] = modifications

        return json.dumps(plan, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"여행 계획 수정 중 오류가 발생했습니다: {str(e)}"


@tool
def validate_travel_plan_tool(plan_json: str) -> str:
    """여행 계획의 유효성을 검증하는 도구

    Args:
        plan_json: 검증할 여행 계획 JSON 문자열

    Returns:
        검증 결과 메시지
    """
    try:
        plan = json.loads(plan_json)

        # 필수 필드 확인
        required_fields = ["destination", "duration", "itinerary"]
        missing_fields = [
            field for field in required_fields if field not in plan]

        if missing_fields:
            return f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}"

        # 일정 검증
        if len(plan["itinerary"]) != plan["duration"]:
            return f"일정 일수({len(plan['itinerary'])})와 설정된 기간({plan['duration']})이 일치하지 않습니다."

        return "여행 계획이 유효합니다."

    except json.JSONDecodeError:
        return "유효하지 않은 JSON 형식입니다."
    except Exception as e:
        return f"계획 검증 중 오류가 발생했습니다: {str(e)}"


@tool
def web_search_tool(query: str) -> str:
    """웹에서 정보를 검색하는 도구. 처음 초안 작성할때 사용하는 도구 입니다. 최종 계획 작성할때는 사용하지 마세요.
    Args:
        query:  질문

    Returns:
        검색 결과 텍스트
    """
    try:
        # Tavily Service를 사용하여 실제 웹 검색 수행
        results = tavily_service.search_web(query, max_results=5)

        # 결과 포맷팅
        if results and results.get('success') and results.get('results'):
            formatted_results = []
            for i, result in enumerate(results['results'], 1):
                formatted_results.append(
                    f"{i}. {result.get('title', '')}\n"
                    f"   URL: {result.get('url', '')}\n"
                    f"   설명: {result.get('description', '')}\n"
                )
            return f"'{query}' 검색 결과:\n\n" + "\n".join(formatted_results)
        else:
            error_msg = results.get(
                'error', '알 수 없는 오류') if results else '검색 결과 없음'
            return f"'{query}' 검색 중 오류가 발생했습니다: {error_msg}"

    except Exception as e:
        return f"검색 중 오류가 발생했습니다: {str(e)}"
