import logging
from typing import Any, Dict, List

from src.services.notion_service import NotionService
from src.tools.share_tools import ShareTools


class ShareAgent:
    def __init__(self):
        """
        여행 계획 공유를 담당하는 에이전트
        """
        self.logger = logging.getLogger(__name__)
        self.notion_service = NotionService()
        self.share_tools = ShareTools()

    def share_to_notion(self, verified_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        여행 계획을 Notion에 공유

        Args:
            verified_plan (Dict[str, Any]): 검증된 여행 계획

        Returns:
            Dict[str, Any]: Notion 공유 결과
        """
        self.logger.info("Notion에 여행 계획 공유 시작")

        # Notion 페이지 생성을 위한 여행 계획 포맷팅
        notion_page_content = self._format_plan_for_notion(verified_plan)

        try:
            # Notion 페이지 생성
            page_id = self.notion_service.create_page(
                title=f"{verified_plan['destinations'][0]} 여행 계획",
                content=notion_page_content
            )

            share_result = {
                'status': '성공',
                'notion_page_id': page_id,
                'shared_content': notion_page_content
            }
        except Exception as e:
            self.logger.error(f"Notion 공유 중 오류 발생: {e}")
            share_result = {
                'status': '실패',
                'error': str(e),
                'notion_page_id': None
            }

        self.logger.info("Notion에 여행 계획 공유 완료")
        return share_result

    def _format_plan_for_notion(self, verified_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        여행 계획을 Notion 페이지 형식으로 포맷팅

        Args:
            verified_plan (Dict[str, Any]): 검증된 여행 계획

        Returns:
            List[Dict[str, Any]]: Notion 페이지 콘텐츠
        """
        notion_content = []

        # 여행 개요
        notion_content.append({
            'type': 'heading_2',
            'text': '여행 개요'
        })
        notion_content.append({
            'type': 'paragraph',
            'text': f"목적지: {', '.join(verified_plan.get('destinations', []))}"
        })
        notion_content.append({
            'type': 'paragraph',
            'text': f"여행 기간: {verified_plan.get('trip_duration', {}).get('start_date')} ~ {verified_plan.get('trip_duration', {}).get('end_date')}"
        })

        # 예산 정보
        notion_content.append({
            'type': 'heading_2',
            'text': '예산 정보'
        })
        budget_estimate = verified_plan.get('budget_estimate', {})
        notion_content.append({
            'type': 'paragraph',
            'text': f"총 예산: {budget_estimate.get('total_budget', 0)}원"
        })
        notion_content.append({
            'type': 'paragraph',
            'text': f"1일 평균 예산: {budget_estimate.get('daily_budget', 0)}원"
        })

        # 일정
        notion_content.append({
            'type': 'heading_2',
            'text': '일정'
        })

        for day_plan in verified_plan.get('daily_itinerary', []):
            notion_content.append({
                'type': 'heading_3',
                'text': f"{day_plan['date']} - {day_plan['destination']}"
            })

            # 활동
            activities_text = ', '.join(day_plan.get('activities', []))
            notion_content.append({
                'type': 'paragraph',
                'text': f"활동: {activities_text}"
            })

        # 안전 및 날씨 정보
        notion_content.append({
            'type': 'heading_2',
            'text': '안전 및 날씨 정보'
        })

        safety_assessment = verified_plan.get('safety_assessment', {})
        notion_content.append({
            'type': 'paragraph',
            'text': f"안전 수준: {safety_assessment.get('overall_safety_level', '정보 없음')}"
        })

        weather_compatibility = verified_plan.get('weather_compatibility', {})
        notion_content.append({
            'type': 'paragraph',
            'text': f"날씨 호환성: {weather_compatibility.get('overall_compatibility', '정보 없음')}"
        })

        return notion_content

    def request_user_confirmation(self, share_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자에게 공유 확인 요청

        Args:
            share_result (Dict[str, Any]): Notion 공유 결과

        Returns:
            Dict[str, Any]: 사용자 확인 결과
        """
        self.logger.info("사용자 공유 확인 요청")

        # 실제 구현 시 사용자 인터페이스나 메시징 서비스를 통해 확인
        confirmation_result = {
            'status': '대기 중',
            'user_response': None,
            'shared_page_id': share_result.get('notion_page_id')
        }

        return confirmation_result

    def execute(self, verified_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        공유 에이전트의 주요 실행 메서드

        Args:
            verified_plan (Dict[str, Any]): 검증된 여행 계획

        Returns:
            Dict[str, Any]: 공유 결과
        """
        notion_share_result = self.share_to_notion(verified_plan)
        user_confirmation = self.request_user_confirmation(notion_share_result)

        return {
            'notion_share_result': notion_share_result,
            'user_confirmation': user_confirmation
        }
