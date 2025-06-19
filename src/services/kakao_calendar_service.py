"""
KakaoTalk Calendar API 연동 서비스
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from ..config.api_config import kakao_calendar_config  # 변경 예정
from ..utils.logger import logger


class KakaoCalendarService:
    """KakaoTalk Calendar API 연동 서비스"""

    def __init__(self):
        self.config = kakao_calendar_config  # 변경 예정
        self.access_token = None  # OAuth 토큰 또는 앱 어드민 키
        # self._initialize_service() # 초기화 로직 필요시 구현

    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        if not self.access_token:
            # TODO: 토큰 발급/갱신 로직 필요
            # 우선 환경변수에서 읽어오도록 임시 처리
            self.access_token = os.getenv(
                "KAKAO_ACCESS_TOKEN")  # 예시, 실제로는 OAuth 과정 필요
            if not self.access_token:
                logger.error("카카오 API 액세스 토큰이 설정되지 않았습니다.")
                raise ValueError("Kakao API access token is not set.")

        return {
            "Authorization": f"Bearer {self.access_token}",
            # 대부분의 카카오 API는 이 Content-Type을 사용
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def _get_admin_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성 (앱 어드민 키 사용)"""
        # TODO: 실제 앱 어드민 키 사용 로직으로 변경
        app_admin_key = os.getenv("KAKAO_APP_ADMIN_KEY")
        if not app_admin_key:
            logger.error("카카오 앱 어드민 키가 설정되지 않았습니다.")
            raise ValueError("Kakao App Admin Key is not set.")
        return {
            "Authorization": f"KakaoAK {app_admin_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def is_available(self) -> bool:
        """서비스 사용 가능 여부 확인 (기본적으로 True, 필요시 로직 추가)"""
        # TODO: 실제 서비스 가능 상태 확인 로직 (예: 토큰 유효성 검사)
        return True

    def get_upcoming_events(self, calendar_id: str = "primary", max_results: int = 10) -> List[Dict[str, Any]]:
        """다가오는 일정 조회"""
        if not self.is_available():
            logger.warning("카카오톡 캘린더 서비스를 사용할 수 없습니다.")
            return []

        try:
            # 카카오 캘린더 API는 '일정 목록 가져오기'를 사용
            # 시간 범위 설정 필요 (예: 지금부터 7일 후까지)
            now = datetime.now()
            # 카카오 API는 from, to 파라미터를 UTC RFC5545 형식으로 받음
            # 예: "2024-07-01T00:00:00Z"
            # 카카오 톡캘린더 API의 from, to 파라미터는 최대 31일 범위
            time_min = now.strftime('%Y-%m-%dT%H:%M:%SZ')
            # max_results는 카카오 API에서 limit 파라미터로 조절

            # 일반 일정 목록 가져오기 API 사용
            # GET https://kapi.kakao.com/v2/api/calendar/events
            # 파라미터: calendar_id, from, to, limit 등

            # 이 부분은 실제 API 문서에 맞춰 파라미터 및 URL 수정 필요
            response = requests.get(
                f"{self.config.api_base_url}/v2/api/calendar/events",
                headers=self._get_headers(),
                params={
                    "calendar_id": calendar_id,
                    "from": time_min,
                    # "to" 파라미터도 적절히 설정해야 함
                    # "limit": max_results  # API 스펙 확인 필요
                }
            )
            response.raise_for_status()  # 오류 발생 시 예외 발생
            events_data = response.json()

            formatted_events = []
            for event in events_data.get("events", []):
                formatted_event = self._format_event(event)
                if formatted_event:
                    formatted_events.append(formatted_event)

            logger.info(f"다가오는 일정 {len(formatted_events)}개를 조회했습니다.")
            return formatted_events

        except requests.exceptions.RequestException as e:
            logger.error(f"카카오톡 캘린더 API 오류: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"일정 조회 중 오류 발생: {str(e)}")
            return []

    def create_event(self, title: str, start_time: datetime, end_time: datetime,
                     description: str = "", location: Dict[str, Any] = None,
                     calendar_id: str = "primary", rrule: Optional[str] = None) -> Optional[str]:
        """새 일정 생성 (일반 일정)"""
        if not self.is_available():
            logger.warning("카카오톡 캘린더 서비스를 사용할 수 없습니다.")
            return None

        try:
            # 시간 정보 포맷팅 (RFC3339, 예: "2024-07-01T10:00:00Z")
            # 카카오 API는 UTC 기준으로 시간을 받으므로, 필요시 시간대 변환
            # datetime 객체를 UTC로 변환 후 .isoformat() + 'Z'

            event_data = {
                "event": {
                    "title": title,
                    "time": {
                        # UTC로 변환 필요
                        "start_at": start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        # UTC로 변환 필요
                        "end_at": end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "time_zone": "Asia/Seoul",  # 또는 사용자 설정
                        "all_day": False,  # 종일 일정 여부
                        "lunar": False  # 음력 여부
                    },
                    "description": description,
                }
            }
            if calendar_id != "primary":  # 기본 캘린더가 아니면 ID 명시
                event_data["calendar_id"] = calendar_id

            if location:  # location은 name, location_id, address, latitude, longitude 등을 포함하는 객체
                event_data["event"]["location"] = location

            if rrule:  # 반복 일정 설정 (RFC5545 RRULE 형식)
                event_data["event"]["rrule"] = rrule

            # POST https://kapi.kakao.com/v2/api/calendar/create/event
            response = requests.post(
                f"{self.config.api_base_url}/v2/api/calendar/create/event",
                headers=self._get_headers(),
                # API 스펙에 따라 json.dumps 또는 직접 구성
                data={"event": str(event_data["event"])}
            )
            # 카카오 API는 종종 form-data로 event 객체를 문자열화하여 전달해야 함. 확인 필요.
            # requests.post의 data 파라미터는 dict를 form-urlencoded로 보내거나,
            # json 파라미터는 application/json으로 보냄.
            # 카카오 문서에는 -d 'event={...}' 형태로 되어 있으므로, data에 문자열화된 JSON을 전달해야 할 수 있음.

            response.raise_for_status()
            event_result = response.json()
            event_id = event_result.get("event_id")

            logger.info(f"새 일정이 카카오톡 캘린더에 생성되었습니다: {title} (ID: {event_id})")
            return event_id

        except requests.exceptions.RequestException as e:
            logger.error(f"카카오톡 캘린더 API 오류: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"일정 생성 중 오류 발생: {str(e)}")
            return None

    def get_events_in_range(self, start_date: datetime, end_date: datetime, calendar_id: str = "primary") -> List[Dict[str, Any]]:
        """특정 기간의 일정 조회"""
        if not self.is_available():
            logger.warning("카카오톡 캘린더 서비스를 사용할 수 없습니다.")
            return []

        try:
            # 시간 포맷팅 (RFC5545 UTC)
            time_min = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')  # UTC 변환 필요
            time_max = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')   # UTC 변환 필요

            # GET https://kapi.kakao.com/v2/api/calendar/events
            response = requests.get(
                f"{self.config.api_base_url}/v2/api/calendar/events",
                headers=self._get_headers(),
                params={
                    "calendar_id": calendar_id,
                    "from": time_min,
                    "to": time_max,
                    # "limit": 1000 # 필요시 최대 결과 수 지정
                }
            )
            response.raise_for_status()
            events_data = response.json()

            formatted_events = []
            for event in events_data.get("events", []):
                formatted_event = self._format_event(event)
                if formatted_event:
                    formatted_events.append(formatted_event)

            logger.info(f"기간 내 일정 {len(formatted_events)}개를 조회했습니다.")
            return formatted_events

        except requests.exceptions.RequestException as e:
            logger.error(f"카카오톡 캘린더 API 오류: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"기간별 일정 조회 중 오류 발생: {str(e)}")
            return []

    def _format_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """카카오톡 캘린더 일정 데이터 포맷팅"""
        try:
            # 카카오 API 응답 형식에 맞춰 파싱
            # 'time' 객체에서 start_at, end_at, time_zone, all_day 등 추출
            time_info = event_data.get("time", {})
            start_at_str = time_info.get("start_at")  # "2022-10-27T03:00:00Z"
            end_at_str = time_info.get("end_at")

            if not start_at_str or not end_at_str:
                return None

            # UTC 문자열을 datetime 객체로 변환
            start_time = datetime.fromisoformat(
                start_at_str.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(
                end_at_str.replace('Z', '+00:00'))

            # location 정보 파싱
            location_info = event_data.get("location", {})
            location_name = location_info.get("name")
            # 주소라도 있으면 사용
            if not location_name and location_info.get("address"):
                location_name = location_info.get("address")

            return {
                "id": event_data.get("id"),
                "title": event_data.get("title", "제목 없음"),
                "description": event_data.get("description", ""),
                "location": location_name or "",  # 단순 문자열로 우선 처리
                "start_time": start_time,
                "end_time": end_time,
                "all_day": time_info.get("all_day", False),
                # 카카오 API는 참석자, 생성자 정보를 일반 일정 조회에서 기본 제공하지 않을 수 있음.
                # 필요시 상세 조회 API 사용 또는 응답 스펙 확인.
                "html_link": "",  # 카카오 API는 htmlLink를 직접 제공하지 않음
                # 'created_at', 'updated_at' 등 메타데이터는 API 스펙 확인 필요
            }

        except Exception as e:
            logger.error(f"카카오톡 일정 포맷팅 중 오류 발생: {str(e)}")
            return None

    def create_travel_event(self, destination: str, start_date: datetime,
                            end_date: datetime, activities: List[str] = None,
                            destination_details: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """여행 일정 생성 (카카오톡 캘린더용)"""
        if not activities:
            activities = []

        title = f"🧳 {destination} 여행"

        description_parts = [
            f"📍 목적지: {destination}",
            f"📅 여행 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
        ]
        if activities:
            description_parts.append("🎯 주요 활동:")
            for i, activity in enumerate(activities, 1):
                description_parts.append(f"  {i}. {activity}")
        description_parts.append("\n✈️ Travel Planner Agent로 생성된 일정입니다.")
        description = "\n".join(description_parts)

        # 카카오맵 API에서 받은 장소 정보를 location 객체로 변환
        # 예: destination_details = {'name': '카카오판교오피스', 'address': '경기 성남시 분당구 판교역로 166', 'latitude': 37.402056, 'longitude': 127.108212}
        kakao_location = None
        if destination_details:
            kakao_location = {
                # 장소명
                "name": destination_details.get("place_name", destination),
                "address": destination_details.get("address_name", ""),  # 주소
                # 카카오 캘린더 API는 위경도 직접 지원 여부 확인 필요, location_id가 있을 수 있음
                "location_id": destination_details.get("id"),  # 카카오맵 장소 ID
                "latitude": float(destination_details.get("y")) if destination_details.get("y") else None,
                "longitude": float(destination_details.get("x")) if destination_details.get("x") else None,
            }
            # 위경도 필드가 없는 경우 제거
            if kakao_location["latitude"] is None or kakao_location["longitude"] is None:
                kakao_location.pop("latitude", None)
                kakao_location.pop("longitude", None)

        return self.create_event(
            title=title,
            start_time=start_date,  # 시간 정보 포함한 datetime 객체여야 함
            end_time=end_date,     # 시간 정보 포함한 datetime 객체여야 함
            description=description,
            location=kakao_location,
            # 종일 일정으로 처리할 경우 start_date, end_date의 시간을 00:00:00, 23:59:59 등으로 설정하고 all_day=True
            # 카카오 API에서 start_at, end_at은 필수. 종일이면 해당 날짜의 시작과 끝 시간으로.
        )


# 전역 Kakao Calendar 서비스 인스턴스 (나중에 설정 클래스에서 관리하도록 변경 가능)
# kakao_calendar_service = KakaoCalendarService()
