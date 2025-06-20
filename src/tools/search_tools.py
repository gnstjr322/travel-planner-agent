from typing import List

from langchain.tools import Tool

from ..services.google_search_service import google_search_service
from ..services.kakao_service import kakao_service


async def search_web_info(query: str) -> str:
    """Search web information using Google Search API and return a formatted string."""
    try:
        result = await google_search_service.search_web(query, num_results=5)
        if not result['success'] or not result['results']:
            return f"웹 검색 결과가 없습니다. 오류: {result.get('error', 'Unknown')}"

        # Format results into a string for the LLM
        formatted_results = []
        for r in result['results']:
            formatted_results.append(
                f"- 제목: {r.get('title', 'N/A')}\n"
                f"  - 내용: {r.get('description', 'N/A')}\n"
                f"  - URL: {r.get('url', 'N/A')}"
            )
        return "\n".join(formatted_results)
    except Exception as e:
        return f"웹 검색 중 오류 발생: {str(e)}"


async def search_kakao_places(query: str) -> str:
    """Search places using Kakao Map API and return a formatted string."""
    try:
        places = await kakao_service.search_places(query=query, limit=5)
        if not places:
            return "검색된 장소가 없습니다."

        # Format results into a string for the LLM
        formatted_results = []
        for p in places:
            formatted_results.append(
                f"- 장소명: {p.get('name', 'N/A')}\n"
                f"  - 주소: {p.get('address', 'N/A')}\n"
                f"  - 카테고리: {p.get('category', 'N/A')}\n"
                f"  - 전화번호: {p.get('phone', 'N/A')}\n"
                f"  - 정보 링크: {p.get('place_url', 'N/A')}"
            )
        return "\n".join(formatted_results)
    except Exception as e:
        return f"카카오 장소 검색 중 오류 발생: {str(e)}"


web_search_tool = Tool(
    name="web_search",
    func=None,
    coroutine=search_web_info,
    description="일반적인 최신 정보, 뉴스, 특정 주제에 대한 설명 등 웹 검색이 필요할 때 사용합니다. 여행 장소, 식당, 숙소 이름 등을 직접 검색할 수 있습니다."
)

place_search_tool = Tool(
    name="place_search",
    func=None,
    coroutine=search_kakao_places,
    description="'강남역 맛집', '제주도 관광지'와 같이 특정 지역의 장소를 카테고리별로 검색할 때 사용합니다. 사용자의 요청에 지역과 장소 종류(맛집, 관광지, 숙소 등)가 명확히 드러날 때 유용합니다."
)

search_tools: List[Tool] = [web_search_tool, place_search_tool]
