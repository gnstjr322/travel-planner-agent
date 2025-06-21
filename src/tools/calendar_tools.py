# 캘린더 등록 도구

import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from langchain_core.tools import tool

from src.services.kakao_calendar_service import KakaoCalendarService
from src.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def add_travel_plan_to_calendar(
    travel_plan: str,
    start_date: str = None,
    destination: str = None
) -> str:
    """
    완성된 여행 계획을 카카오 캘린더에 등록합니다.

    Args:
        travel_plan: 완성된 여행 계획 텍스트
        start_date: 여행 시작 날짜 (YYYY-MM-DD 형식, 선택적)
        destination: 여행 목적지 (선택적)

    Returns:
        캘린더 등록 결과 메시지
    """
    try:
        calendar_service = KakaoCalendarService()

        # 여행 계획에서 정보 추출
        plan_info = _parse_travel_plan(travel_plan)

        # 사용자가 제공한 정보로 덮어쓰기
        if start_date:
            plan_info['start_date'] = start_date
        if destination:
            plan_info['destination'] = destination

        # 필수 정보 확인
        if not plan_info['destination']:
            return "❌ 여행 목적지를 찾을 수 없습니다. 목적지를 명시해주세요."

        if not plan_info['start_date']:
            return "❌ 여행 시작 날짜를 찾을 수 없습니다. 날짜를 명시해주세요 (예: 2024-03-15)."

        # 날짜 파싱
        try:
            start_datetime = datetime.strptime(
                plan_info['start_date'], '%Y-%m-%d')
        except ValueError:
            return "❌ 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요."

        # 여행 기간 계산 (기본 1일, 계획에서 추출 시도)
        duration = plan_info.get('duration', 1)
        end_datetime = start_datetime + timedelta(days=duration - 1)

        # 캘린더에 여행 이벤트 생성
        event_title = f"🌏 {plan_info['destination']} 여행"

        # 활동 목록 추출
        activities = _extract_activities(travel_plan)

        # 여행 이벤트 생성
        event_id = calendar_service.create_travel_event(
            destination=plan_info['destination'],
            start_date=start_datetime,
            end_date=end_datetime,
            activities=activities,
            destination_details={
                'plan': travel_plan,
                'activities_count': len(activities)
            }
        )

        if event_id:
            logger.info(f"여행 계획이 캘린더에 등록되었습니다: {event_id}")
            return (
                f"✅ **{plan_info['destination']} 여행**이 캘린더에 성공적으로 등록되었습니다!\n\n"
                f"📅 **기간**: {plan_info['start_date']} ~ {end_datetime.strftime('%Y-%m-%d')}\n"
                f"📍 **장소**: {plan_info['destination']}\n"
                f"🎯 **활동**: {len(activities)}개 일정\n\n"
                f"카카오톡 캘린더에서 확인하실 수 있습니다."
            )
        else:
            return "❌ 캘린더 등록에 실패했습니다. 카카오 계정 연동을 확인해주세요."

    except Exception as e:
        logger.error(f"캘린더 등록 중 오류 발생: {str(e)}")
        return f"❌ 캘린더 등록 중 오류가 발생했습니다: {str(e)}"


def _parse_travel_plan(travel_plan: str) -> dict:
    """여행 계획 텍스트에서 주요 정보를 추출합니다."""
    info = {
        'destination': None,
        'start_date': None,
        'duration': 1
    }

    # 목적지 추출 (제목에서)
    destination_patterns = [
        r'### (.+?) 여행',
        r'## (.+?) 여행',
        r'# (.+?) 여행',
        r'(\w+(?:시|구|동|군|도)) (?:여행|투어|계획)',
        r'(\w+) (?:여행|투어|계획)'
    ]

    for pattern in destination_patterns:
        match = re.search(pattern, travel_plan)
        if match:
            info['destination'] = match.group(1).strip()
            break

    # 날짜 추출
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{4}\.\d{2}\.\d{2})',
        r'(\d{4}/\d{2}/\d{2})'
    ]

    for pattern in date_patterns:
        match = re.search(pattern, travel_plan)
        if match:
            date_str = match.group(1).replace('.', '-').replace('/', '-')
            info['start_date'] = date_str
            break

    # 여행 기간 추출
    duration_patterns = [
        r'(\d+)박\s*(\d+)일',
        r'(\d+)일차',
        r'Day\s*(\d+)',
        r'#### (\d+)일차'
    ]

    max_day = 1
    for pattern in duration_patterns:
        matches = re.findall(pattern, travel_plan)
        for match in matches:
            if isinstance(match, tuple):
                # N박 M일 형태
                if len(match) == 2:
                    max_day = max(max_day, int(match[1]))
                else:
                    max_day = max(max_day, int(match[0]))
            else:
                max_day = max(max_day, int(match))

    info['duration'] = max_day

    return info


def _extract_activities(travel_plan: str) -> list:
    """여행 계획에서 활동/장소 목록을 추출합니다."""
    activities = []

    # 시간별 일정 추출
    time_patterns = [
        r'- \*\*(.+?)\*\*',  # **장소명**
        r'- (.+?)(?:\n|$)',   # - 활동
        r'(?:\d{1,2}:\d{2})\s*-\s*(.+?)(?:\n|$)',  # 시간 - 활동
        r'#### (.+?)(?:\n|$)'  # #### 제목
    ]

    for pattern in time_patterns:
        matches = re.findall(pattern, travel_plan, re.MULTILINE)
        for match in matches:
            activity = match.strip()
            if activity and len(activity) > 2:  # 너무 짧은 것은 제외
                # 주소나 전화번호 부분 제거
                activity = re.sub(r'주소:.*|전화번호:.*|링크:.*', '', activity).strip()
                if activity and activity not in activities:
                    activities.append(activity)

    return activities[:10]  # 최대 10개까지만


@tool
def check_calendar_availability(date: str) -> str:
    """
    특정 날짜의 캘린더 일정을 확인합니다.

    Args:
        date: 확인할 날짜 (YYYY-MM-DD 형식)

    Returns:
        해당 날짜의 일정 정보
    """
    try:
        calendar_service = KakaoCalendarService()

        # 날짜 파싱
        check_date = datetime.strptime(date, '%Y-%m-%d')
        end_date = check_date + timedelta(days=1)

        # 해당 날짜의 일정 조회
        events = calendar_service.get_events_in_range(check_date, end_date)

        if not events:
            return f"📅 {date}에는 등록된 일정이 없습니다."

        result = f"📅 {date}의 일정:\n\n"
        for i, event in enumerate(events, 1):
            result += f"{i}. {event.get('title', '제목 없음')}\n"
            if event.get('time'):
                result += f"   ⏰ {event['time']}\n"
            if event.get('location'):
                result += f"   📍 {event['location']}\n"
            result += "\n"

        return result

    except ValueError:
        return "❌ 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요."
    except Exception as e:
        logger.error(f"캘린더 조회 중 오류 발생: {str(e)}")
        return f"❌ 캘린더 조회 중 오류가 발생했습니다: {str(e)}"


@tool
def update_travel_plan_tool(
    event_id: str,
    title: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    기존 여행 계획을 수정합니다.

    Args:
        event_id: 수정할 이벤트의 고유 ID
        title: 새로운 제목 (선택적)
        start_date: 새로운 시작 날짜 (YYYY-MM-DD 형식, 선택적)
        end_date: 새로운 종료 날짜 (YYYY-MM-DD 형식, 선택적)
        description: 새로운 설명 (선택적)

    Returns:
        수정 결과 메시지
    """
    try:
        calendar_service = KakaoCalendarService()

        # 수정할 데이터 준비
        update_data = {}
        if title:
            update_data['title'] = title

        # 날짜 처리 - datetime 객체로 변환
        if start_date or end_date:
            if start_date:
                start_datetime = datetime.strptime(
                    start_date, '%Y-%m-%d').replace(hour=9, minute=0)  # 오전 9시로 설정
                update_data['start_time'] = start_datetime
            if end_date:
                end_datetime = datetime.strptime(
                    end_date, '%Y-%m-%d').replace(hour=18, minute=0)  # 오후 6시로 설정
                update_data['end_time'] = end_datetime

        if description:
            update_data['description'] = description

        # 이벤트 업데이트
        result = calendar_service.update_event(event_id, **update_data)

        if result:
            return f"✅ 이벤트 {event_id}가 성공적으로 수정되었습니다."
        else:
            return f"❌ 이벤트 {event_id} 수정에 실패했습니다."

    except Exception as e:
        logger.error(f"여행 계획 수정 중 오류: {str(e)}")
        return f"❌ 여행 계획 수정 중 오류가 발생했습니다: {str(e)}"


@tool
def delete_travel_plan_tool(event_id: str) -> str:
    """
    특정 여행 계획을 삭제합니다.

    Args:
        event_id: 삭제할 이벤트의 고유 ID

    Returns:
        삭제 결과 메시지
    """
    try:
        calendar_service = KakaoCalendarService()

        # 이벤트 삭제
        result = calendar_service.delete_event(event_id)

        if result:
            return f"✅ 이벤트 {event_id}가 성공적으로 삭제되었습니다."
        else:
            return f"❌ 이벤트 {event_id} 삭제에 실패했습니다."

    except Exception as e:
        logger.error(f"여행 계획 삭제 중 오류: {str(e)}")
        return f"❌ 여행 계획 삭제 중 오류가 발생했습니다: {str(e)}"


@tool
def search_travel_plan_tool(query: str, include_past: bool = False) -> str:
    """
    사용자가 제공한 검색어로 여행 일정을 찾습니다.

    Args:
        query: 검색어 (목적지, 제목 등)
        include_past: 과거 일정 포함 여부 (기본값: False)

    Returns:
        검색된 일정 목록 문자열
    """
    try:
        calendar_service = KakaoCalendarService()

        # 확장 검색 사용 (과거 일정 포함 옵션)
        events = calendar_service.search_events_extended(
            query, max_results=10, include_past=include_past)

        if not events:
            search_scope = "모든 일정" if include_past else "다가오는 일정"
            return f"'{query}'와 일치하는 {search_scope}을 찾을 수 없습니다.\n\n💡 과거 일정도 검색하려면 include_past=True 옵션을 사용하세요."

        # 결과 포맷팅
        search_scope = "모든 일정" if include_past else "다가오는 일정"
        result = f"'{query}'로 검색된 {search_scope}:\n\n"
        for i, event in enumerate(events, 1):
            result += (
                f"{i}. **{event['title']}**\n"
                f"   - 이벤트 ID: `{event['id']}`\n"
                f"   - 시작: {event['start_time']}\n"
                f"   - 종료: {event['end_time']}\n"
                f"   - 설명: {event['description'] or '없음'}\n\n"
            )

        result += "💡 위 목록에서 수정하거나 삭제할 일정의 이벤트 ID를 복사하여 사용하세요."
        return result

    except Exception as e:
        logger.error(f"여행 계획 검색 중 오류: {str(e)}")
        return f"❌ 여행 계획 검색 중 오류가 발생했습니다: {str(e)}"
