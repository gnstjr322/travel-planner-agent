"""
DuckDuckGo API 연동 서비스 (duckduckgo-search 라이브러리 사용)

이 모듈은 duckduckgo-search 라이브러리를 통해 다음 기능을 제공합니다:
- 웹 검색
- 뉴스 검색
- 이미지 검색 등 (라이브러리가 지원하는 기능)
"""
from typing import Any, Dict

from duckduckgo_search import DDGS  # 동기 버전 DDGS를 사용

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DuckDuckGoService:
    """duckduckgo-search 라이브러리를 사용하는 서비스 클래스"""

    def __init__(self):
        # Ratelimit에 대응하기 위해 프록시 설정 (현재는 비활성화)
        # TODO: 필요시 .env 등에서 프록시 서버 목록을 불러와 설정
        # 예: {"http": "http://user:pass@host:port", "https": ...}
        self.proxies = None
        self.timeout = 10  # 요청 타임아웃 (초)

    def _format_result(self, result: Dict) -> Dict:
        """라이브러리 검색 결과를 일관된 형식으로 변환"""
        return {
            "title": result.get("title", ""),
            "url": result.get("href", ""),
            "description": result.get("body", ""),
        }

    async def search_web(
        self,
        query: str,
        max_results: int = 5,
        region: str = "wt-wt",
        safesearch: str = "moderate"  # safesearch 파라미터 추가
    ) -> Dict[str, Any]:
        """
        DuckDuckGo 웹 검색.
        async 메서드 내에서 동기 라이브러리를 호출합니다.
        성능에 민감한 경우 asyncio.to_thread 사용을 고려해야 합니다.
        """
        if not query:
            return self._empty_result(query, "검색어가 비어있습니다.")

        try:
            # 동기 메서드 호출, 프록시 및 타임아웃 설정 추가
            with DDGS(proxies=self.proxies, timeout=self.timeout) as ddgs:
                results = ddgs.text(
                    query,
                    region=region,
                    safesearch=safesearch,  # safesearch 전달
                    max_results=max_results
                )
                search_results = [self._format_result(r) for r in results]

            return {
                "success": True,
                "query": query,
                "results": search_results
            }

        except Exception as e:
            logger.error(f"DuckDuckGo 검색 중 예기치 않은 오류: {e}")
            return self._empty_result(query, f"예기치 않은 오류: {e}")

    def _empty_result(self, query: str, error_message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "query": query,
            "error": error_message,
            "results": [],
        }

    # 기존 search_travel_info, search_news 등은 search_web을 호출하므로
    # search_web의 반환 구조 변경에 따라 수정이 필요할 수 있습니다.
    # 우선 search_web을 중심으로 수정합니다.


# 전역 DuckDuckGo 서비스 인스턴스
duckduckgo_service = DuckDuckGoService()
