# 검색 도구들

import asyncio
import json

from langchain_core.tools import tool

from src.services.kakao_service import KakaoMapService

kakao_map_service = KakaoMapService()


@tool
def location_search_tool(query: str) -> str:
    """
    하나의 특정 장소에 대한 상세 정보를 카카오맵에서 검색합니다.
    이 도구는 '은혜손칼국수'나 '국립중앙박물관'처럼 검색하고 싶은 장소의 이름이 명확할 때 사용해야 합니다.
    '송파구 맛집'처럼 지역과 카테고리를 조합한 포괄적인 검색에는 적합하지 않습니다.

    Args:
        query: 검색할 장소의 정확한 이름 (예: "은혜손칼국수")

    Returns:
        검색된 장소의 상세 정보 (주소, 전화번호, 카카오맵 링크 등)
    """
    try:
        # 비동기 함수를 동기적으로 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # query 자체를 검색어로 사용하여 장소 검색
            places = loop.run_until_complete(
                kakao_map_service.search_places(query, limit=5)
            )
        finally:
            loop.close()

        if not places:
            return f"'{query}'에 대한 검색 결과를 찾을 수 없습니다."

        # 첫 번째 결과만 사용하여 가장 관련성 높은 정보 제공
        place = places[0]
        result = (
            f"'{query}' 검색 결과:\n"
            f"- 이름: {place.get('name', '')}\n"
            f"- 주소: {place.get('address', '')}\n"
            f"- 전화번호: {place.get('phone', '정보없음')}\n"
            f"- 카테고리: {place.get('category', '')}\n"
            f"- 카카오맵 링크: {place.get('place_url', '')}\n"
        )
        return result

    except Exception as e:
        return f"장소 검색 중 오류가 발생했습니다: {str(e)}"


@tool
def nearby_search_tool(location: str, category: str = "FD6", radius: int = 1000) -> str:
    """특정 위치 주변의 장소를 검색하는 도구

    Args:
        location: 중심 위치 (주소나 장소명)
        category: 카카고리 코드 (FD6: 음식점, CE7: 카페, AD5: 숙박)
        radius: 검색 반경 (미터)

    Returns:
        주변 장소 정보
    """
    try:
        # 먼저 중심 위치의 좌표를 검색
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            center_places = loop.run_until_complete(
                kakao_map_service.search_places(location, limit=1)
            )

            if not center_places:
                return f"{location}의 위치를 찾을 수 없습니다."

            center = center_places[0]
            x, y = center['x'], center['y']

            # 주변 장소 검색
            nearby_places = loop.run_until_complete(
                kakao_map_service.search_nearby(
                    x, y, category, radius, limit=5)
            )
        finally:
            loop.close()

        if not nearby_places:
            return f"{location} 주변에서 해당 카테고리의 장소를 찾을 수 없습니다."

        # 카테고리 한글명 매핑
        category_names = {
            "FD6": "음식점",
            "CE7": "카페",
            "AD5": "숙박시설",
            "AT4": "관광명소"
        }
        category_name = category_names.get(category, category)

        # 결과 포맷팅
        formatted_results = []
        for i, place in enumerate(nearby_places, 1):
            distance = place.get('distance', '')
            if distance:
                distance = f" ({distance}m)"

            formatted_results.append(
                f"{i}. {place.get('name', '')}{distance}\n"
                f"   주소: {place.get('address', '')}\n"
                f"   카테고리: {place.get('category', '')}\n"
                f"   전화번호: {place.get('phone', '정보없음')}\n"
            )

        return f"{location} 주변 {category_name} 검색 결과 (반경 {radius}m):\n\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"주변 장소 검색 중 오류가 발생했습니다: {str(e)}"
