"""
캘린더 에이전트 - KakaoTalk Calendar API 연동
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..services.kakao_calendar_service import KakaoCalendarService
from ..utils.logger import logger
from .base_agent import AgentResponse, BaseAgent


class CalendarAgent(BaseAgent):
    """캘린더 관리 에이전트"""

    def __init__(self):
        super().__init__("calendar", "캘린더 일정 관리")
        self.calendar_service = KakaoCalendarService()

    def get_tools(self) -> List[Any]:
        """CalendarAgent는 LangChain Tool을 직접 사용하지 않으므로 빈 리스트를 반환합니다."""
        return []

    def process(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """캘린더 관련 요청 처리"""
        try:
            logger.info(f"캘린더 에이전트 처리 시작: {query}")

            if not self.calendar_service.is_available():
                return AgentResponse(
                    success=False,
                    message=(
                        "⚠️ 카카오톡 캘린더 서비스에 연결할 수 없습니다. "
                        "설정을 확인해주세요."
                    ),
                    error="calendar_service_unavailable",
                    agent_name=self.name,
                )

            travel_info = context.get("travel_info", {}) if context else {}
            destination_details = travel_info.get("destination_details")

            if self._is_schedule_creation_request(query):
                return self._create_travel_schedule(
                    query, travel_info, destination_details
                )
            elif self._is_availability_check_request(query):
                return self._check_availability(query)
            elif self._is_schedule_inquiry_request(query):
                return self._get_schedule_info(query)
            else:
                return self._provide_calendar_guidance(query)

        except Exception as e:
            logger.error(f"캘린더 에이전트 처리 중 오류: {str(e)}")
            return AgentResponse(
                success=False,
                message=f"캘린더 처리 중 오류가 발생했습니다: {str(e)}",
                error=str(e),
                agent_name=self.name,
            )

    def _is_schedule_creation_request(self, query: str) -> bool:
        keywords = [
            "일정 추가", "캘린더에 등록", "스케줄 생성", "일정 만들어",
            "캘린더 저장", "예약", "등록해줘", "추가해줘", "톡캘린더에 추가"
        ]
        return any(keyword in query for keyword in keywords)

    def _is_availability_check_request(self, query: str) -> bool:
        keywords = [
            "비어있나", "가능한가", "일정 확인", "시간 확인",
            "겹치는지", "충돌", "여유 있나"
        ]
        return any(keyword in query for keyword in keywords)

    def _is_schedule_inquiry_request(self, query: str) -> bool:
        keywords = [
            "일정 보여줘", "스케줄 확인", "무슨 일정", "언제 뭐가",
            "캘린더 보기", "예정된 일정", "톡캘린더 일정"
        ]
        return any(keyword in query for keyword in keywords)

    def _create_travel_schedule(
        self,
        query: str,
        travel_info: Dict[str, Any],
        destination_details: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """여행 일정 생성"""
        try:
            destination = travel_info.get("destination", "여행지 미정")
            dates = self._extract_dates_from_query(query)

            if not dates or len(dates) < 2:
                start_dt = datetime.now().replace(
                    hour=9, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                end_dt = start_dt.replace(hour=18, minute=0) + timedelta(
                    days=2
                )
            else:
                start_dt = dates[0].replace(
                    hour=9, minute=0, second=0, microsecond=0
                )
                end_dt = dates[-1].replace(
                    hour=18, minute=0, second=0, microsecond=0
                )
                if start_dt > end_dt:
                    end_dt = start_dt.replace(
                        hour=18, minute=0
                    ) + timedelta(days=1)

            activities = travel_info.get("activities", [])

            event_id = self.calendar_service.create_travel_event(
                destination=destination,
                start_date=start_dt,
                end_date=end_dt,
                activities=activities,
                destination_details=destination_details,
            )

            if event_id:
                start_str = start_dt.strftime("%Y년 %m월 %d일 %H:%M")
                end_str = end_dt.strftime("%Y년 %m월 %d일 %H:%M")
                content_msg = (
                    f"📅 **여행 일정이 카카오톡 캘린더에 등록되었습니다!**\\n\\n"
                    f"🎯 **여행지**: {destination}\\n"
                    f"📅 **기간**: {start_str} ~ {end_str}\\n"
                    f"🆔 **일정 ID**: {event_id}\\n\\n"
                    f"✅ **등록 완료 사항**:\\n"
                    f"- 카카오톡 캘린더에 자동 등록\\n"
                    f"- 여행 기간 중 시간 블록 예약\\n"
                    f"- 주요 활동 정보 포함\\n\\n"
                    f"🔔 **알림 설정 (카카오톡 캘린더 앱 내에서 확인 가능)**:\\n"
                    f"- 카카오톡 캘린더의 기본 알림 설정을 따릅니다.\\n\\n"
                    f"📱 **추가 권장사항**:\\n"
                    f"- 카카오톡 캘린더 앱에서 세부 일정 확인 및 수정 가능\\n"
                    f"- 동행자와 톡캘린더 공유 기능 활용 권장"
                )
                return AgentResponse(
                    success=True,
                    message=content_msg,
                    data={
                        "event_id": event_id,
                        "destination": destination,
                        "start_date": start_dt.isoformat(),
                        "end_date": end_dt.isoformat(),
                        "calendar_action": "create_success_kakao",
                    },
                    agent_name=self.name,
                )
            else:
                return AgentResponse(
                    success=False,
                    message=(
                        "❌ 카카오톡 캘린더 일정 생성에 실패했습니다. "
                        "권한이나 설정을 확인해주세요."
                    ),
                    error="create_failed_kakao",
                    agent_name=self.name,
                )
        except Exception as e:
            logger.error(f"여행 일정 생성 중 오류: {str(e)}")
            return AgentResponse(
                success=False,
                message=f"여행 일정 생성 중 오류가 발생했습니다: {str(e)}",
                error=str(e),
                agent_name=self.name,
            )

    def _check_availability(
        self, query: str
    ) -> AgentResponse:
        """일정 가용성 확인"""
        try:
            dates = self._extract_dates_from_query(query)
            if not dates:
                start_dt = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=7)
                end_dt = start_dt + timedelta(
                    days=7, hours=23, minutes=59, seconds=59
                )
            else:
                start_dt = dates[0].replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                end_dt = (
                    dates[-1] if len(dates) > 1 else dates[0]
                ) + timedelta(hours=23, minutes=59, seconds=59)

            existing_events = (
                self.calendar_service.get_events_in_range(
                    start_dt, end_dt
                )
            )

            start_str = start_dt.strftime("%Y년 %m월 %d일")
            end_str = end_dt.strftime("%Y년 %m월 %d일")

            is_available = not existing_events
            if is_available:
                content_msg = (
                    f"✅ **카카오톡 캘린더에 해당 기간 일정이 비어있습니다!**\\n\\n"
                    f"📅 **확인 기간**: {start_str} ~ {end_str}\\n\\n"
                    f"🎉 **좋은 소식**:\\n"
                    f"- 해당 기간에 기존 일정이 없습니다.\\n"
                    f"- 여행 계획을 세우기에 완벽한 시기입니다.\\n"
                    f"- 바로 일정 등록이 가능합니다.\\n\\n"
                    f"💡 **다음 단계 제안**:\\n"
                    f"- 여행지와 세부 일정 확정\\n"
                    f"- 카카오톡 캘린더에 여행 일정 등록\\n"
                    f"- 필요한 예약 및 준비사항 체크"
                )
            else:
                event_list_str = []
                for event in existing_events:
                    time_display = (
                        event["start_time"].strftime("%m/%d %H:%M")
                        if not event.get("all_day")
                        else event["start_time"].strftime("%m/%d (종일)")
                    )
                    event_list_str.append(
                        f"• {event['title']} ({time_display})"
                    )

                events_str = "\\n".join(event_list_str)
                content_msg = (
                    f"⚠️ **카카오톡 캘린더에 기존 일정이 있습니다**\\n\\n"
                    f"📅 **확인 기간**: {start_str} ~ {end_str}\\n\\n"
                    f"📋 **기존 일정 목록**:\\n{events_str}\\n\\n"
                    f"🤔 **권장사항**:\\n"
                    f"- 기존 일정과 겹치지 않는 다른 날짜 고려\\n"
                    f"- 기존 일정 조정 가능 여부 확인\\n"
                    f"- 짧은 여행으로 일정 변경 검토"
                )

            return AgentResponse(
                success=True,
                message=content_msg,
                data={
                    "start_date": start_dt.isoformat(),
                    "end_date": end_dt.isoformat(),
                    "existing_events_count": len(existing_events),
                    "is_available": is_available,
                    "calendar_type": "kakao",
                },
                agent_name=self.name,
            )
        except Exception as e:
            logger.error(f"일정 가용성 확인 중 오류: {str(e)}")
            return AgentResponse(
                success=False,
                message=f"일정 확인 중 오류가 발생했습니다: {str(e)}",
                error=str(e),
                agent_name=self.name,
            )

    def _get_schedule_info(self, query: str) -> AgentResponse:
        """예약된 일정 정보 조회"""
        try:
            dates = self._extract_dates_from_query(query)
            if not dates:
                # 날짜가 지정되지 않으면, 오늘부터 한 달간의 일정을 조회
                start_dt = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                end_dt = start_dt + timedelta(days=30)
            else:
                start_dt = dates[0]
                end_dt = (
                    dates[-1] if len(dates) > 1 else start_dt
                ) + timedelta(hours=23, minutes=59, seconds=59)

            events = self.calendar_service.get_events_in_range(
                start_dt, end_dt
            )
            start_str = start_dt.strftime("%Y년 %m월 %d일")
            end_str = end_dt.strftime("%Y년 %m월 %d일")

            if not events:
                content_msg = (
                    f"📅 **조회 기간 내 카카오톡 캘린더 일정이 없습니다.**\\n\\n"
                    f"🗓️ **기간**: {start_str} ~ {end_str}"
                )
            else:
                event_list_str = []
                for event in events:
                    time_display = (
                        f"{event['start_time'].strftime('%H:%M')} ~ "
                        f"{event['end_time'].strftime('%H:%M')}"
                        if not event.get("all_day")
                        else "(하루 종일)"
                    )
                    event_list_str.append(
                        f"• **{event['title']}**: "
                        f"{event['start_time'].strftime('%Y-%m-%d')} {time_display}"
                    )
                events_str = "\\n".join(event_list_str)
                content_msg = (
                    f"📅 **카카오톡 캘린더 일정 조회 결과입니다.**\\n\\n"
                    f"🗓️ **기간**: {start_str} ~ {end_str}\\n\\n"
                    f"📋 **일정 목록**:\\n{events_str}"
                )

            return AgentResponse(
                success=True,
                message=content_msg,
                data={"events": events, "calendar_type": "kakao"},
                agent_name=self.name,
            )
        except Exception as e:
            logger.error(f"일정 정보 조회 중 오류: {str(e)}")
            return AgentResponse(
                success=False,
                message=f"일정 조회 중 오류가 발생했습니다: {str(e)}",
                error=str(e),
                agent_name=self.name,
            )

    def _provide_calendar_guidance(self, query: str) -> AgentResponse:
        """일반적인 캘린더 관련 안내 제공"""
        guidance_text = (
            "**📅 카카오톡 캘린더 에이전트입니다.**\\n\\n"
            "제가 도와드릴 수 있는 일은 다음과 같습니다:\\n"
            "- **일정 등록**: '제주도 3박 4일 여행 일정 등록해줘' 와 같이 "
            "말씀해보세요.\\n"
            "- **일정 확인**: '다음 주 내 스케줄 보여줘' 와 같이 문의할 수 있습니다.\\n"
            "- **빈 시간 조회**: '다음 달에 여행 가능한 날짜 알려줘' 와 같이 "
            "물어보세요.\\n\\n"
            "궁금한 점이 있으시면 언제든지 다시 물어보세요! 😊"
        )
        return AgentResponse(
            success=True,
            message=guidance_text,
            data={"guidance_type": "general"},
            agent_name=self.name,
        )

    def _extract_dates_from_query(self, query: str) -> List[datetime]:
        """쿼리에서 날짜 정보 추출 (간단한 예시)
        실제로는 더 정교한 NLP 또는 LLM 기반 정보 추출 필요.
        """
        parsed_dates: List[datetime] = []

        # YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD
        matches_ymd = re.findall(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})', query)
        for m in matches_ymd:
            try:
                year, month, day = int(m[0]), int(m[1]), int(m[2])
                parsed_dates.append(datetime(year, month, day))
            except ValueError:
                pass  # 잘못된 날짜 형식 무시

        # MM/DD, MM-DD (YYYY 패턴이 없을 때만 시도)
        if not matches_ymd:
            matches_md = re.findall(r'(\d{1,2})[-/](\d{1,2})', query)
            for m in matches_md:
                try:
                    month, day = int(m[0]), int(m[1])
                    current_year = datetime.now().year
                    # 간단하게 현재 연도로 가정. 필요시 더 정교한 로직 추가.
                    parsed_dates.append(datetime(current_year, month, day))
                except ValueError:
                    pass

        if "내일" in query:
            parsed_dates.append(datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
        if "오늘" in query:
            parsed_dates.append(datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0))

        if parsed_dates:
            parsed_dates.sort()
            logger.info(f"추출된 날짜: {parsed_dates}")
            return parsed_dates

        logger.info("쿼리에서 날짜 정보를 추출하지 못했습니다.")
        return []
