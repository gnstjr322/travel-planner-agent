import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.services.kakao_calendar_service import KakaoCalendarService
from src.tools.calendar_tools import CalendarTools


class CalendarAgent:
    def __init__(self):
        """
        캘린더 관리 및 일정 등록을 담당하는 에이전트
        """
        self.logger = logging.getLogger(__name__)
        self.kakao_calendar_service = KakaoCalendarService()
        self.calendar_tools = CalendarTools()

    def prepare_calendar_registration(self, verified_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        캘린더 등록을 위한 일정 준비

        Args:
            verified_plan (Dict[str, Any]): 검증된 여행 계획

        Returns:
            Dict[str, Any]: 캘린더 등록 준비 정보
        """
        self.logger.info("캘린더 등록 준비 시작")

        calendar_events = self._convert_plan_to_calendar_events(verified_plan)

        registration_info = {
            'total_events': len(calendar_events),
            'events': calendar_events,
            'registration_status': '대기 중'
        }

        return registration_info

    def _convert_plan_to_calendar_events(self, verified_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        여행 계획을 캘린더 이벤트로 변환

        Args:
            verified_plan (Dict[str, Any]): 검증된 여행 계획

        Returns:
            List[Dict[str, Any]]: 캘린더 이벤트 목록
        """
        calendar_events = []
        daily_itinerary = verified_plan.get('daily_itinerary', [])

        for day_plan in daily_itinerary:
            # 목적지 이벤트
            destination_event = {
                'title': f"{day_plan['destination']} 여행",
                'start_time': day_plan['date'],
                'end_time': day_plan['date'],
                'description': f"{day_plan['destination']} 도착 및 일정"
            }
            calendar_events.append(destination_event)

            # 활동 이벤트
            for activity in day_plan.get('activities', []):
                activity_event = {
                    'title': activity,
                    'start_time': self._calculate_activity_time(day_plan['date']),
                    # 기본 2시간
                    'end_time': self._calculate_activity_time(day_plan['date'], duration=2),
                    'description': f"{day_plan['destination']} 여행 중 {activity} 활동"
                }
                calendar_events.append(activity_event)

        return calendar_events

    def _calculate_activity_time(self, base_date: str, duration: int = 2) -> str:
        """
        활동 시작 시간 계산

        Args:
            base_date (str): 기준 날짜
            duration (int): 활동 지속 시간 (시간)

        Returns:
            str: 계산된 활동 시작 시간
        """
        base_datetime = datetime.strptime(base_date, '%Y-%m-%d')
        activity_time = base_datetime.replace(hour=10, minute=0)  # 기본 오전 10시

        return activity_time.strftime('%Y-%m-%d %H:%M')

    def register_to_calendar(self, verified_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        여행 계획을 카카오 캘린더에 등록

        Args:
            verified_plan (Dict[str, Any]): 검증된 여행 계획

        Returns:
            Dict[str, Any]: 캘린더 등록 결과
        """
        self.logger.info("카카오 캘린더 등록 시작")

        calendar_events = self._convert_plan_to_calendar_events(verified_plan)
        registration_results = []

        for event in calendar_events:
            try:
                result = self.kakao_calendar_service.create_event(
                    title=event['title'],
                    start_time=event['start_time'],
                    end_time=event['end_time'],
                    description=event['description']
                )
                registration_results.append({
                    'event': event['title'],
                    'status': '성공' if result else '실패'
                })
            except Exception as e:
                self.logger.error(f"캘린더 이벤트 등록 실패: {event['title']}, 오류: {e}")
                registration_results.append({
                    'event': event['title'],
                    'status': '실패',
                    'error': str(e)
                })

        registration_summary = {
            'total_events': len(calendar_events),
            'successful_events': sum(1 for result in registration_results if result['status'] == '성공'),
            'failed_events': sum(1 for result in registration_results if result['status'] == '실패'),
            'registration_results': registration_results
        }

        self.logger.info("카카오 캘린더 등록 완료")
        return registration_summary

    def sync_with_notion(self, verified_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        여행 계획을 Notion과 동기화

        Args:
            verified_plan (Dict[str, Any]): 검증된 여행 계획

        Returns:
            Dict[str, Any]: Notion 동기화 결과
        """
        self.logger.info("Notion과 캘린더 동기화 시작")

        # Notion 서비스 연동 및 동기화 로직 구현
        # 실제 구현 시 Notion 서비스를 통해 여행 계획 페이지 생성 및 업데이트

        sync_result = {
            'status': '대기 중',
            'notion_page_id': None,
            'sync_details': {}
        }

        return sync_result

    def execute(self, verified_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        캘린더 에이전트의 주요 실행 메서드

        Args:
            verified_plan (Dict[str, Any]): 검증된 여행 계획

        Returns:
            Dict[str, Any]: 캘린더 관리 결과
        """
        calendar_registration = self.prepare_calendar_registration(
            verified_plan)
        calendar_sync_result = self.register_to_calendar(verified_plan)
        notion_sync_result = self.sync_with_notion(verified_plan)

        return {
            'calendar_registration': calendar_registration,
            'calendar_sync_result': calendar_sync_result,
            'notion_sync_result': notion_sync_result
        }
