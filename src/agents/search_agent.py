import logging
from typing import Any, Dict, List

from src.services.duckduckgo_service import DuckDuckGoService
from src.services.google_search_service import GoogleSearchService
from src.services.tavily_service import TavilyService


class SearchAgent:
    def __init__(self):
        """
        여행 정보 검색을 담당하는 에이전트
        """
        self.logger = logging.getLogger(__name__)
        self.duckduckgo_service = DuckDuckGoService()
        self.google_service = GoogleSearchService()
        self.tavily_service = TavilyService()

    def search_travel_info(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        다양한 검색 서비스를 통해 여행 정보 수집

        Args:
            query (str): 검색 쿼리
            max_results (int): 최대 검색 결과 수

        Returns:
            List[Dict[str, Any]]: 수집된 여행 정보 목록
        """
        self.logger.info(f"여행 정보 검색 시작: {query}")

        search_results = []

        # DuckDuckGo 검색
        duckduckgo_results = self.duckduckgo_service.search(query, max_results)
        search_results.extend(duckduckgo_results)

        # Google 검색
        google_results = self.google_service.search(query, max_results)
        search_results.extend(google_results)

        # Tavily 검색 (AI 기반 검색)
        tavily_results = self.tavily_service.search(query, max_results)
        search_results.extend(tavily_results)

        # 중복 제거 및 정제
        unique_results = self._deduplicate_results(search_results)

        self.logger.info(f"총 {len(unique_results)}개의 여행 정보 수집 완료")
        return unique_results

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        검색 결과 중복 제거 및 정제

        Args:
            results (List[Dict[str, Any]]): 원본 검색 결과

        Returns:
            List[Dict[str, Any]]: 중복 제거된 검색 결과
        """
        unique_results = []
        seen_urls = set()

        for result in results:
            if result.get('link') not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result.get('link'))

        return unique_results

    def extract_travel_details(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        검색 결과에서 여행 관련 상세 정보 추출

        Args:
            search_results (List[Dict[str, Any]]): 검색 결과 목록

        Returns:
            Dict[str, Any]: 추출된 여행 상세 정보
        """
        travel_details = {
            'destinations': [],
            'attractions': [],
            'recommended_routes': [],
            'travel_tips': []
        }

        for result in search_results:
            # 결과에서 여행 관련 정보 추출 로직
            # 실제 구현 시 NLP 기술이나 규칙 기반 추출 방식 사용
            pass

        return travel_details

    def execute(self, user_request: str) -> Dict[str, Any]:
        """
        검색 에이전트의 주요 실행 메서드

        Args:
            user_request (str): 사용자 요청

        Returns:
            Dict[str, Any]: 검색 결과 및 여행 정보
        """
        search_results = self.search_travel_info(user_request)
        travel_details = self.extract_travel_details(search_results)

        return {
            'search_results': search_results,
            'travel_details': travel_details
        }



