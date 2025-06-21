"""
Notion API 연동 서비스

이 모듈은 Notion API를 통해 다음 기능을 제공합니다:
- 데이터베이스 조회
- 페이지 생성
- 페이지 수정
- 페이지 삭제
"""

import os
from typing import Any, Dict, List, Optional

from notion_client import Client

from ..utils.logger import get_logger

logger = get_logger(__name__)


class NotionService:
    """Notion API 서비스 클래스"""

    def __init__(self):
        """
        Notion 클라이언트 초기화
        .env 파일에서 API 키와 데이터베이스 ID 로드
        """
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")

        if not self.api_key:
            raise ValueError("NOTION_API_KEY 환경 변수가 설정되지 않았습니다.")

        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID 환경 변수가 설정되지 않았습니다.")

        # Notion 클라이언트 생성
        self.client = Client(auth=self.api_key)

    def get_database_info(self) -> Dict[str, Any]:
        """
        데이터베이스 정보 조회

        Returns:
            데이터베이스 메타데이터
        """
        try:
            database = self.client.databases.retrieve(self.database_id)
            return {
                "id": database['id'],
                "title": database['title'][0]['plain_text'] if database['title'] else "제목 없음",
                "properties": list(database['properties'].keys())
            }
        except Exception as e:
            logger.error(f"데이터베이스 정보 조회 중 오류: {e}")
            return {}

    def query_database(self, filter_params: Optional[Dict] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        데이터베이스 쿼리

        Args:
            filter_params: 선택적 필터 파라미터
            max_results: 최대 결과 수

        Returns:
            쿼리 결과 리스트
        """
        try:
            query_params = {"database_id": self.database_id,
                            "page_size": max_results}

            if filter_params:
                query_params["filter"] = filter_params

            results = self.client.databases.query(**query_params)

            formatted_results = []
            for page in results['results']:
                formatted_page = self._format_page(page)
                if formatted_page:
                    formatted_results.append(formatted_page)

            return formatted_results
        except Exception as e:
            logger.error(f"데이터베이스 쿼리 중 오류: {e}")
            return []

    def create_page(self, properties: Dict[str, Any], content: Optional[str] = None) -> Optional[str]:
        """
        새 페이지 생성

        Args:
            properties: 페이지 속성
            content: 선택적 페이지 내용

        Returns:
            생성된 페이지 ID
        """
        try:
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties
            }

            # 내용이 있다면 children 추가
            if content:
                page_data["children"] = [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]

            new_page = self.client.pages.create(**page_data)
            logger.info(f"새 페이지 생성 완료: {new_page['id']}")
            return new_page['id']
        except Exception as e:
            logger.error(f"페이지 생성 중 오류: {e}")
            return None

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> bool:
        """
        기존 페이지 업데이트

        Args:
            page_id: 업데이트할 페이지 ID
            properties: 업데이트할 속성

        Returns:
            업데이트 성공 여부
        """
        try:
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            logger.info(f"페이지 업데이트 완료: {page_id}")
            return True
        except Exception as e:
            logger.error(f"페이지 업데이트 중 오류: {e}")
            return False

    def delete_page(self, page_id: str) -> bool:
        """
        페이지 삭제 (아카이브)

        Args:
            page_id: 삭제할 페이지 ID

        Returns:
            삭제 성공 여부
        """
        try:
            self.client.pages.update(
                page_id=page_id,
                archived=True
            )
            logger.info(f"페이지 삭제(아카이브) 완료: {page_id}")
            return True
        except Exception as e:
            logger.error(f"페이지 삭제 중 오류: {e}")
            return False

    def _format_page(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Notion 페이지를 일관된 형식으로 변환

        Args:
            page: Notion API에서 반환된 페이지 객체

        Returns:
            포맷팅된 페이지 정보
        """
        try:
            # 다양한 제목 속성에 대응
            title_prop = page['properties'].get('이름', {})
            title = '제목 없음'

            # title 속성이 있는 경우
            if 'title' in title_prop:
                titles = title_prop['title']
                if titles and isinstance(titles, list) and len(titles) > 0:
                    first_title = titles[0]
                    if isinstance(first_title, dict):
                        title = (
                            first_title.get('plain_text') or
                            first_title.get('text', {}).get('content') or
                            '제목 없음'
                        )

            # rich_text 속성이 있는 경우 (백업)
            elif 'rich_text' in title_prop:
                rich_texts = title_prop['rich_text']
                if rich_texts and isinstance(rich_texts, list) and len(rich_texts) > 0:
                    first_text = rich_texts[0]
                    if isinstance(first_text, dict):
                        title = (
                            first_text.get('plain_text') or
                            first_text.get('text', {}).get('content') or
                            '제목 없음'
                        )

            return {
                "id": page['id'],
                "title": title,
                "url": page.get('url', ''),
                "created_time": page.get('created_time', ''),
                "last_edited_time": page.get('last_edited_time', '')
            }
        except Exception as e:
            logger.error(f"페이지 포맷팅 중 오류: {e}")
            # 오류 발생 시 기본 정보라도 반환
            return {
                "id": page.get('id', ''),
                "title": "제목 없음",
                "url": page.get('url', ''),
                "created_time": page.get('created_time', ''),
                "last_edited_time": page.get('last_edited_time', '')
            }

    def search_web(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Notion 데이터베이스 내 페이지 검색

        Args:
            query: 검색어
            max_results: 최대 검색 결과 수

        Returns:
            검색 결과 딕셔너리
        """
        if not query:
            return self._empty_result(query, "검색어가 비어있습니다.")

        try:
            # 제목에서 검색
            filter_params = {
                "property": "이름",
                "title": {
                    "contains": query
                }
            }

            results = self.query_database(filter_params, max_results)

            return {
                "success": True,
                "query": query,
                "results": [
                    {
                        "title": result["title"],
                        "url": result["url"],
                        "description": ""  # Notion은 기본적으로 설명 제공 안 함
                    } for result in results
                ]
            }
        except Exception as e:
            logger.error(f"Notion 검색 중 예기치 않은 오류: {e}")
            return self._empty_result(query, f"예기치 않은 오류: {e}")

    def _empty_result(self, query: str, error_message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "query": query,
            "error": error_message,
            "results": [],
        }


# 전역 Notion 서비스 인스턴스
notion_service = NotionService()
