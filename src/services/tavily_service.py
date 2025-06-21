"""
Tavily API 연동 서비스
"""

import os
from typing import Any, Dict

from tavily import TavilyClient

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TavilyService:
    """Tavily API를 사용하여 웹 검색을 수행하는 서비스 클래스"""

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY 환경 변수가 설정되지 않았습니다.")
        self.client = TavilyClient(api_key=self.api_key)

    def _format_result(self, result: Dict) -> Dict:
        """Tavily 검색 결과를 일관된 형식으로 변환"""
        return {
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "description": result.get("content", ""),
        }

    def search_web(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",  # 'basic' 또는 'advanced'
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
    ) -> Dict[str, Any]:
        """
        Tavily 웹 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            max_results: 반환할 최대 결과 수
            search_depth: 검색 깊이 ('basic' 또는 'advanced')
            include_answer: 검색 결과에 답변 포함 여부
            include_raw_content: 원시 HTML 콘텐츠 포함 여부
            include_images: 이미지 URL 포함 여부

        Returns:
            검색 결과 딕셔너리
        """
        if not query:
            return self._empty_result(query, "검색어가 비어있습니다.")

        try:
            response = self._search_sync(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                include_images=include_images,
            )

            search_results = [self._format_result(
                r) for r in response.get("results", [])]
            answer = response.get("answer")

            return {
                "success": True,
                "query": query,
                "answer": answer,  # Tavily에서 제공하는 요약 답변
                "results": search_results,
            }

        except Exception as e:
            logger.error(f"Tavily 검색 중 예기치 않은 오류: {e}")
            return self._empty_result(query, f"예기치 않은 오류: {e}")

    def _search_sync(
        self,
        query: str,
        max_results: int,
        search_depth: str,
        include_answer: bool,
        include_raw_content: bool,
        include_images: bool,
    ) -> Dict[str, Any]:
        """
        Tavily API를 사용하여 동기적으로 웹 검색을 수행합니다.
        """
        return self.client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
            include_images=include_images,
        )

    def _empty_result(self, query: str, error_message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "query": query,
            "error": error_message,
            "answer": None,
            "results": [],
        }


# 전역 Tavily 서비스 인스턴스
tavily_service = TavilyService()
