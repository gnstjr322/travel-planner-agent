"""
KakaoTalk Calendar API 연동 서비스
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytz
import requests
from dotenv import find_dotenv, load_dotenv, set_key

from ..config.api_config import kakao_calendar_config  # 변경 예정
from ..utils.logger import logger


class KakaoCalendarService:
    """KakaoTalk Calendar API 연동 서비스"""

    def __init__(self):
        # 서비스 초기화 시마다 .env 파일을 강제로 다시 로드하여 캐시 문제를 해결합니다.
        load_dotenv(override=True)
        self.config = kakao_calendar_config  # 변경 예정
        self.rest_api_key = os.getenv("KAKAO_REST_API_KEY")
        self.refresh_token = os.getenv("KAKAO_REFRESH_TOKEN")
        self.access_token = os.getenv("KAKAO_ACCESS_TOKEN")
        self.token_file = find_dotenv()
        # self._initialize_service() # 초기화 로직 필요시 구현

    def _refresh_access_token(self):
        """Refresh Token을 사용하여 새로운 Access Token을 발급받고 .env 파일에 저장합니다."""
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.rest_api_key,
            "refresh_token": self.refresh_token,
        }
        response = requests.post(url, data=data)
        if response.status_code != 200:
            logger.error(
                f"카카오 토큰 갱신 실패: {response.status_code} - {response.text}")
            raise Exception("카카오 토큰을 갱신할 수 없습니다.")

        token_info = response.json()
        self.access_token = token_info["access_token"]
        set_key(self.token_file, "KAKAO_ACCESS_TOKEN",
                self.access_token, quote_mode="never")
        logger.info("새로운 카카오 액세스 토큰을 발급하고 저장했습니다.")

        # Refresh Token이 갱신된 경우, 함께 저장
        if "refresh_token" in token_info:
            self.refresh_token = token_info["refresh_token"]
            set_key(self.token_file, "KAKAO_REFRESH_TOKEN",
                    self.refresh_token, quote_mode="never")
            logger.info("새로운 카카오 리프레시 토큰을 저장했습니다.")

    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        if not self.access_token:
            self._refresh_access_token()

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

    def _request_with_retry(self, method, url, **kwargs):
        """API 요청을 보내고, 401 오류 시 토큰을 갱신하여 재시도합니다."""
        try:
            headers = self._get_headers()
            kwargs["headers"] = headers
            response = requests.request(method, url, **kwargs)

            if response.status_code == 401:
                logger.warning("카카오 API 접근 토큰이 만료되어 재발급을 시도합니다.")
                self._refresh_access_token()
                # 갱신된 토큰으로 헤더 다시 설정
                kwargs["headers"] = self._get_headers()
                response = requests.request(method, url, **kwargs)

            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(
                f"카카오톡 캘린더 API 오류: {e.response.text if e.response else str(e)}")
            raise

    def check_token_info(self):
        """현재 액세스 토큰의 정보를 확인하여 스코프를 검사합니다."""
        url = "https://kapi.kakao.com/v1/user/access_token_info"
        logger.info("현재 토큰 정보 확인을 시도합니다...")
        try:
            response = self._request_with_retry("get", url)
            token_info = response.json()
            logger.info(
                f"토큰 정보: {json.dumps(token_info, indent=2, ensure_ascii=False)}")
            if "scopes" in token_info:
                logger.info(f"✅ 현재 토큰에 부여된 권한(Scopes): {token_info['scopes']}")
                if "talk_calendar" not in token_info["scopes"]:
                    logger.error(
                        "❌ 토큰에 'talk_calendar' 권한이 없습니다! 카카오 개발자 콘솔 동의항목 설정 및 사용자 재동의가 필요합니다.")
            else:
                logger.warning("토큰 정보에 'scopes' 필드가 없습니다.")
            return token_info
        except Exception as e:
            logger.error(f"토큰 정보 확인 중 오류 발생: {e}")
            return None

    def get_upcoming_events(self, calendar_id: str = "primary", max_results: int = 10) -> List[Dict[str, Any]]:
        """다가오는 일정 조회"""
        if not self.is_available():
            logger.warning("카카오톡 캘린더 서비스를 사용할 수 없습니다.")
            return []

        try:
            # 카카오 API는 UTC 기준으로 시간을 처리합니다.
            now_utc = datetime.utcnow()
            time_min = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            # 'to' 파라미터는 'from'으로부터 최대 31일 이내로 설정해야 합니다.
            time_max = (now_utc + timedelta(days=30)
                        ).strftime('%Y-%m-%dT%H:%M:%SZ')

            response = self._request_with_retry(
                "get",
                f"{self.config.api_base_url}/v2/api/calendar/events",
                params={
                    "calendar_id": calendar_id,
                    "from": time_min,
                    "to": time_max,
                    "limit": max_results,
                }
            )
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
                     calendar_id: str = "primary", rrule: Optional[str] = None,
                     reminders: Optional[List[int]] = None, color: Optional[str] = None) -> Optional[str]:
        """새 일정 생성 (일반 일정)"""
        if not self.is_available():
            logger.warning("카카오톡 캘린더 서비스를 사용할 수 없습니다.")
            return None

        try:
            # 카카오 API는 UTC 기준으로 시간을 처리합니다.
            start_utc = start_time.astimezone().astimezone(pytz.utc)
            end_utc = end_time.astimezone().astimezone(pytz.utc)

            event_data = {
                "title": title,
                "time": {
                    "start_at": start_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "end_at": end_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "time_zone": "Asia/Seoul",  # API 기본값이지만 명시적으로 설정
                    "all_day": False,
                    "lunar": False
                },
                "description": description,
            }
            if calendar_id != "primary":  # 기본 캘린더가 아니면 ID 명시
                event_data["calendar_id"] = calendar_id

            if location:  # location은 name, location_id, address, latitude, longitude 등을 포함하는 객체
                event_data["location"] = location

            if rrule:  # 반복 일정 설정 (RFC5545 RRULE 형식)
                event_data["rrule"] = rrule

            if reminders:
                event_data["reminders"] = reminders

            if color:
                event_data["color"] = color

            payload = {'event': json.dumps(event_data)}

            # 디버깅을 위해 전송 직전의 페이로드를 INFO 레벨로 강제 출력
            logger.info(f"카카오 캘린더 생성 요청 데이터: {payload}")

            response = self._request_with_retry(
                "post",
                f"{self.config.api_base_url}/v2/api/calendar/create/event",
                data=payload
            )
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
            start_utc = start_date.astimezone().astimezone(pytz.utc)
            end_utc = end_date.astimezone().astimezone(pytz.utc)
            time_min = start_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            time_max = end_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

            response = self._request_with_retry(
                "get",
                f"{self.config.api_base_url}/v2/api/calendar/events",
                params={
                    "calendar_id": calendar_id,
                    "from": time_min,
                    "to": time_max,
                    # "limit": 1000 # 필요시 최대 결과 수 지정
                }
            )
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

        # 시작 시간과 종료 시간이 같은 경우 종료 시간을 자동 조정
        if start_date == end_date:
            # 하루 종일 일정으로 처리: 시작은 오전 9시, 종료는 오후 6시
            start_date = start_date.replace(
                hour=9, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(
                hour=18, minute=0, second=0, microsecond=0)
        elif start_date.time() == end_date.time() and start_date.time().hour == 0:
            # 둘 다 자정(00:00)인 경우
            start_date = start_date.replace(
                hour=9, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(
                hour=18, minute=0, second=0, microsecond=0)

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

    def update_event(self, event_id: str, calendar_id: str = "primary", **kwargs) -> bool:
        """
        기존 일정을 수정합니다. (최신 API 명세 적용)
        kwargs: title, start_time, end_time, description, location, reminders, color 등
        """
        if not event_id:
            logger.error("일정 수정을 위한 event_id가 없습니다.")
            return False

        try:
            event_data = {}
            if "start_time" in kwargs and "end_time" in kwargs:
                start_utc = kwargs["start_time"].astimezone(
                ).astimezone(pytz.utc)
                end_utc = kwargs["end_time"].astimezone().astimezone(pytz.utc)
                event_data["time"] = {
                    "start_at": start_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "end_at": end_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                }

            for key in ["title", "description", "location", "reminders", "color"]:
                if key in kwargs:
                    event_data[key] = kwargs[key]

            if not event_data:
                logger.warning("수정할 내용이 없습니다.")
                return False

            payload = {
                'event_id': event_id,
                'calendar_id': calendar_id,
                'event': json.dumps(event_data)
            }
            logger.info(f"카카오 캘린더 수정 요청 데이터: {payload}")

            self._request_with_retry(
                "post",
                f"{self.config.api_base_url}/v2/api/calendar/update/event/host",
                data=payload
            )

            logger.info(f"일정(ID: {event_id})이 성공적으로 수정되었습니다.")
            return True

        except Exception as e:
            logger.error(f"일정 수정 중 오류 발생: {str(e)}")
            return False

    def delete_event(self, event_id: str) -> bool:
        """일정을 삭제합니다. (최신 API 명세 적용)"""
        if not event_id:
            logger.error("일정 삭제를 위한 event_id가 없습니다.")
            return False

        try:
            params = {'event_id': event_id}
            logger.info(f"카카오 캘린더 삭제 요청: {params}")

            self._request_with_retry(
                "delete",
                f"{self.config.api_base_url}/v2/api/calendar/delete/event",
                params=params
            )

            logger.info(f"일정(ID: {event_id})이 성공적으로 삭제되었습니다.")
            return True

        except Exception as e:
            logger.error(f"일정 삭제 중 오류 발생: {str(e)}")
            return False

    def search_events(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        사용자가 제공한 검색어로 일정을 찾습니다.

        Args:
            query: 검색어 (목적지, 제목 등)
            max_results: 최대 검색 결과 수

        Returns:
            검색된 일정 목록
        """
        try:
            # 카카오 API 제한사항에 맞춰 현재부터 30일 후까지만 조회
            now_utc = datetime.utcnow()
            time_min = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            time_max = (now_utc + timedelta(days=30)
                        ).strftime('%Y-%m-%dT%H:%M:%SZ')

            response = self._request_with_retry(
                "get",
                f"{self.config.api_base_url}/v2/api/calendar/events",
                params={
                    "calendar_id": "primary",
                    "from": time_min,
                    "to": time_max,
                    "limit": max_results * 2,  # 필터링 후 충분한 결과를 위해 2배로 설정
                }
            )
            events_data = response.json()

            # 검색어로 필터링
            matched_events = []
            for event in events_data.get("events", []):
                # 제목, 설명, 위치 등에서 검색어 포함 여부 확인
                if (query.lower() in event.get('title', '').lower() or
                    query.lower() in event.get('description', '').lower() or
                        query.lower() in str(event.get('location', '')).lower()):

                    formatted_event = {
                        "id": event.get('id', ''),
                        "title": event.get('title', '제목 없음'),
                        "start_time": event.get('time', {}).get('start_at', ''),
                        "end_time": event.get('time', {}).get('end_at', ''),
                        "description": event.get('description', ''),
                    }
                    matched_events.append(formatted_event)

                    # 최대 결과 수 제한
                    if len(matched_events) >= max_results:
                        break

            logger.info(f"'{query}' 검색 결과: {len(matched_events)}개 일정 발견")
            return matched_events

        except Exception as e:
            logger.error(f"일정 검색 중 오류 발생: {str(e)}")
            return []

    def search_events_extended(self, query: str, max_results: int = 10, include_past: bool = False) -> List[Dict[str, Any]]:
        """
        확장된 일정 검색 - 과거 일정도 포함 가능

        Args:
            query: 검색어
            max_results: 최대 검색 결과 수
            include_past: 과거 일정 포함 여부

        Returns:
            검색된 일정 목록
        """
        all_matched_events = []

        try:
            now_utc = datetime.utcnow()

            # 미래 일정 검색 (현재 ~ 30일 후)
            future_events = self.search_events(query, max_results)
            all_matched_events.extend(future_events)

            # 과거 일정 검색 (30일 전 ~ 현재)
            if include_past and len(all_matched_events) < max_results:
                try:
                    time_min = (now_utc - timedelta(days=30)
                                ).strftime('%Y-%m-%dT%H:%M:%SZ')
                    time_max = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

                    response = self._request_with_retry(
                        "get",
                        f"{self.config.api_base_url}/v2/api/calendar/events",
                        params={
                            "calendar_id": "primary",
                            "from": time_min,
                            "to": time_max,
                            "limit": max_results * 2,
                        }
                    )
                    events_data = response.json()

                    for event in events_data.get("events", []):
                        if (query.lower() in event.get('title', '').lower() or
                            query.lower() in event.get('description', '').lower() or
                                query.lower() in str(event.get('location', '')).lower()):

                            # 중복 제거 (ID 기준)
                            event_id = event.get('id', '')
                            if not any(e.get('id') == event_id for e in all_matched_events):
                                formatted_event = {
                                    "id": event_id,
                                    "title": event.get('title', '제목 없음'),
                                    "start_time": event.get('time', {}).get('start_at', ''),
                                    "end_time": event.get('time', {}).get('end_at', ''),
                                    "description": event.get('description', ''),
                                }
                                all_matched_events.append(formatted_event)

                                if len(all_matched_events) >= max_results:
                                    break
                except Exception as past_error:
                    logger.warning(f"과거 일정 검색 중 오류 (무시하고 계속): {past_error}")

            # 시간순 정렬 (최신순)
            all_matched_events.sort(key=lambda x: x.get(
                'start_time', ''), reverse=True)

            logger.info(
                f"'{query}' 확장 검색 결과: {len(all_matched_events)}개 일정 발견")
            return all_matched_events[:max_results]

        except Exception as e:
            logger.error(f"확장 일정 검색 중 오류 발생: {str(e)}")
            return []


# 전역 Kakao Calendar 서비스 인스턴스 (나중에 설정 클래스에서 관리하도록 변경 가능)
# kakao_calendar_service = KakaoCalendarService()
