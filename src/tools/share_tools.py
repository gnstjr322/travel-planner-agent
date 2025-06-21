"""
공유 관련 도구들 - 노션 페이지 생성 및 사용자 확인
"""

from datetime import datetime
from typing import Any, Dict

from langchain_core.tools import tool

from src.services.notion_service import notion_service
from src.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def create_notion_page_tool(
    title: str,
    content: str,
    destination: str = None,
    travel_date: str = None
) -> Dict[str, Any]:
    """
    노션에 여행 계획 페이지를 생성하는 도구

    Args:
        title: 페이지 제목
        content: 페이지 내용
        destination: 여행 목적지 (선택사항)
        travel_date: 여행 날짜 (선택사항)

    Returns:
        생성 결과 딕셔너리 (성공 여부, URL 등)
    """
    try:
        logger.info(f"노션 페이지 생성 시작: {title}")

        # 노션 페이지 속성 구성
        properties = {
            "이름": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        }

        # 추가 속성이 있다면 포함 (데이터베이스 구조에 따라)
        if destination:
            # 목적지 속성이 데이터베이스에 있다면 추가
            pass

        if travel_date:
            # 날짜 속성이 데이터베이스에 있다면 추가
            pass

        # 노션 페이지 생성
        page_id = notion_service.create_page(
            properties=properties,
            content=content
        )

        if page_id:
            # 노션 페이지 URL 생성 (기본 형식)
            notion_url = f"https://www.notion.so/{page_id.replace('-', '')}"

            logger.info(f"노션 페이지 생성 성공: {notion_url}")

            return {
                "success": True,
                "page_id": page_id,
                "url": notion_url,
                "message": f"✅ 노션에 여행 계획이 성공적으로 저장되었습니다!\n🔗 링크: {notion_url}"
            }
        else:
            logger.error("노션 페이지 생성 실패")
            return {
                "success": False,
                "page_id": None,
                "url": None,
                "message": "❌ 노션 페이지 생성에 실패했습니다. 다시 시도해주세요."
            }

    except Exception as e:
        error_msg = f"노션 페이지 생성 중 오류: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "page_id": None,
            "url": None,
            "message": f"❌ 노션 페이지 생성 중 오류가 발생했습니다: {str(e)}"
        }
