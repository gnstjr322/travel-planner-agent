"""
카카오맵 API 연동 서비스

이 모듈은 카카오맵 API를 통해 다음 기능을 제공합니다:
- 장소 검색
- 위치 기반 주변 검색  
- 길찾기
- 지도 정보
"""

from typing import Any, Dict, List, Optional

import aiohttp

from ..config.api_config import api_config
from ..utils.logger import logger


class KakaoMapService:
    """카카오맵 API 서비스 클래스"""

    def __init__(self):
        self.base_url = "https://dapi.kakao.com"
        self.api_key = api_config.kakao_rest_api_key

    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더를 생성합니다."""
        if not self.api_key:
            raise ValueError("카카오 REST API 키가 설정되지 않았습니다.")
        return {"Authorization": f"KakaoAK {self.api_key}"}

    async def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        radius: int = 20000,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        키워드로 장소 검색

        Args:
            query: 검색 키워드
            location: 중심 좌표 (x,y 형태)
            radius: 반경(미터) 
            limit: 검색 결과 개수

        Returns:
            장소 정보 리스트
        """
        if not self.api_key:
            logger.warning("카카오 API 키가 설정되지 않았습니다.")
            return []

        try:
            params = {
                'query': query,
                'size': limit
            }

            if location:
                x, y = location.split(',')
                params.update({
                    'x': x.strip(),
                    'y': y.strip(),
                    'radius': radius
                })

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v2/local/search/keyword.json",
                    headers=self._get_headers(),
                    params=params
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        places = []

                        for item in data.get('documents', []):
                            place_info = {
                                'name': item.get('place_name', ''),
                                'address': item.get(
                                    'road_address_name', item.get(
                                        'address_name', '')
                                ),
                                'phone': item.get('phone', ''),
                                'category': item.get('category_name', ''),
                                'x': float(item.get('x', 0)),  # 경도
                                'y': float(item.get('y', 0)),  # 위도
                                'place_url': item.get('place_url', ''),
                                'distance': item.get('distance', '')
                            }
                            places.append(place_info)

                        logger.info(f"카카오맵에서 '{query}' 검색 결과: {len(places)}개")
                        return places
                    else:
                        logger.error(f"카카오맵 API 오류: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"카카오맵 장소 검색 오류: {str(e)}")
            return []

    async def search_nearby(
        self,
        x: float,
        y: float,
        category: str = "FD6",
        radius: int = 1000,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        좌표 기반 주변 검색

        Args:
            x: 경도
            y: 위도
            category: 카테고리 코드 (FD6: 음식점, CE7: 카페 등)
            radius: 반경(미터)
            limit: 검색 결과 개수

        Returns:
            주변 장소 정보 리스트
        """
        if not self.api_key:
            return []

        try:
            params = {
                'category_group_code': category,
                'x': x,
                'y': y,
                'radius': radius,
                'size': limit
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v2/local/search/category.json",
                    headers=self._get_headers(),
                    params=params
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        return self._parse_places(data.get('documents', []))
                    else:
                        logger.error(f"카카오맵 주변 검색 오류: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"카카오맵 주변 검색 오류: {str(e)}")
            return []

    async def get_directions(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        길찾기 정보 조회

        Args:
            origin: 출발지 좌표 (x,y)
            destination: 목적지 좌표 (x,y) 
            waypoints: 경유지 좌표 리스트

        Returns:
            길찾기 정보
        """
        # 카카오 내비 API 사용 (별도 인증 필요)
        # 현재는 기본 정보만 반환
        return {
            'origin': origin,
            'destination': destination,
            'distance': 0,
            'duration': 0,
            'route': [],
            'status': 'not_implemented'
        }

    def _parse_places(self, documents: List[Dict]) -> List[Dict[str, Any]]:
        """장소 정보 파싱 헬퍼 메서드"""
        places = []
        for item in documents:
            place_info = {
                'name': item.get('place_name', ''),
                'address': item.get(
                    'road_address_name', item.get('address_name', '')
                ),
                'phone': item.get('phone', ''),
                'category': item.get('category_name', ''),
                'x': float(item.get('x', 0)),
                'y': float(item.get('y', 0)),
                'place_url': item.get('place_url', ''),
                'distance': item.get('distance', '')
            }
            places.append(place_info)
        return places


# 전역 카카오맵 서비스 인스턴스
kakao_service = KakaoMapService()
