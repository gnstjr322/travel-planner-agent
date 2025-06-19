import os
from typing import Any, Dict

from dotenv import load_dotenv
from googleapiclient.discovery import build

from src.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


class GoogleSearchService:
    """Google Custom Search API를 사용하는 서비스 클래스"""

    def __init__(self):
        """서비스를 초기화하고 API 키와 CX를 로드합니다."""
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cx = os.getenv("GOOGLE_SEARCH_CX")
        if not self.api_key or not self.cx:
            raise ValueError("Google API 키 또는 CX ID가 .env 파일에 설정되지 않았습니다.")
        self.service = build("customsearch", "v1", developerKey=self.api_key)

    def _format_result(self, item: Dict) -> Dict:
        """API 응답 항목을 일관된 형식으로 변환합니다."""
        return {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "description": item.get("snippet", ""),
        }

    async def search_web(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Google Custom Search API를 사용하여 웹을 검색합니다.
        """
        if not query:
            return self._empty_result(query, "검색어가 비어있습니다.")

        try:
            res = (
                self.service.cse()
                .list(q=query, cx=self.cx, num=num_results)
                .execute()
            )
            search_results = [
                self._format_result(item) for item in res.get("items", [])
            ]

            return {
                "success": True,
                "query": query,
                "results": search_results,
            }
        except Exception as e:
            logger.error(f"Google 검색 중 예기치 않은 오류: {e}")
            return self._empty_result(query, f"예기치 않은 오류: {e}")

    def _empty_result(self, query: str, error_message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "query": query,
            "error": error_message,
            "results": [],
        }


# 전역 Google Search 서비스 인스턴스
google_search_service = GoogleSearchService()
