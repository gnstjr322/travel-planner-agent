"""
여행 계획 AI 어시스턴트 - 심플 채팅 인터페이스
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.core.multi_agent_system import TravelMultiAgentSystem

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


# 환경 변수 로드
load_dotenv(override=True)

# 페이지 설정
st.set_page_config(
    page_title="여행 AI 어시스턴트",
    page_icon="🌏",
    layout="centered"
)

# CSS 스타일
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #2E86AB;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .ai-message {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        max-width: 100%;
        margin-right: auto;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .message-time {
        font-size: 0.8rem;
        opacity: 0.7;
        margin-top: 5px;
    }
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #e9ecef;
        padding: 10px 20px;
    }
    .stButton > button {
        border-radius: 25px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        font-weight: bold;
        padding: 10px 30px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """세션 상태 초기화"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "multi_agent_system" not in st.session_state:
        st.session_state.multi_agent_system = None


def get_multi_agent_system():
    """멀티 에이전트 시스템 가져오기 (캐싱)"""
    if st.session_state.multi_agent_system is None:
        try:
            # API 키 확인
            if not os.getenv("OPENAI_API_KEY"):
                st.error("⚠️ OpenAI API 키가 설정되지 않았습니다.")
                st.stop()

            # 시스템 초기화
            with st.spinner("🤖 AI 에이전트 팀을 준비하고 있습니다..."):
                system = TravelMultiAgentSystem()
                system.build_graph()
                st.session_state.multi_agent_system = system

        except Exception as e:
            st.error(f"❌ 시스템 초기화 실패: {str(e)}")
            st.stop()

    return st.session_state.multi_agent_system


def display_chat_messages():
    """채팅 메시지 표시"""
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align: center; color: #888; padding: 50px; font-style: italic;">
            💬 안녕하세요! 여행 계획에 대해 무엇이든 물어보세요.<br><br>
            예시: "서울 2박 3일 여행 계획 짜줘", "부산 맛집 투어 추천해줘"
        </div>
        """, unsafe_allow_html=True)
        return

    # 메시지 표시
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You</strong><br>
                {message["content"]}
                <div class="message-time">{message["timestamp"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="ai-message">
                <strong>🤖 Travel Planner </strong><br>
                {message["content"]}
                <div class="message-time">{message["timestamp"]}</div>
            </div>
            """, unsafe_allow_html=True)

            # AI 응답에 캘린더 등록 버튼 추가 (최신 메시지에만)
            if i == len(st.session_state.messages) - 1 and "여행" in message["content"]:
                add_calendar_button(message["content"], i)


def add_calendar_button(travel_plan: str, message_index: int):
    """캘린더 등록 버튼과 날짜 입력 UI 추가"""
    st.markdown("---")

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("📅 캘린더에 등록", key=f"calendar_btn_{message_index}"):
            st.session_state[f"show_calendar_form_{message_index}"] = True

    with col2:
        if st.button("🔄 새로운 계획 요청", key=f"new_plan_btn_{message_index}"):
            # 입력창으로 포커스 이동 (새로운 요청 유도)
            # 새 계획을 위해 메시지 기록 초기화. 이것만으로도 rerun이 트리거됩니다.
            st.session_state.messages = []

    # 캘린더 등록 폼 표시
    if st.session_state.get(f"show_calendar_form_{message_index}", False):
        with st.expander("📅 캘린더 등록 정보 입력", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                start_date = st.date_input(
                    "여행 시작 날짜",
                    key=f"start_date_{message_index}",
                    help="여행을 시작할 날짜를 선택해주세요"
                )

            with col2:
                destination = st.text_input(
                    "여행 목적지",
                    key=f"destination_{message_index}",
                    placeholder="예: 서울, 부산, 제주도",
                    help="여행 목적지를 입력해주세요"
                )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("✅ 등록", key=f"confirm_calendar_{message_index}"):
                    register_to_calendar(
                        travel_plan, start_date, destination, message_index)

            with col2:
                if st.button("❌ 취소", key=f"cancel_calendar_{message_index}"):
                    st.session_state[f"show_calendar_form_{message_index}"] = False
                    # 상태 변경 후 자동 rerun 됩니다.


def register_to_calendar(travel_plan: str, start_date, destination: str, message_index: int):
    """캘린더에 여행 계획 등록"""
    try:
        from src.tools.calendar_tools import add_travel_plan_to_calendar

        # 날짜를 문자열로 변환
        start_date_str = start_date.strftime(
            '%Y-%m-%d') if start_date else None

        # 캘린더 등록 도구 호출
        result = add_travel_plan_to_calendar(
            travel_plan=travel_plan,
            start_date=start_date_str,
            destination=destination
        )

        # 결과 표시
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)

        # 폼 숨기기
        st.session_state[f"show_calendar_form_{message_index}"] = False
        # 상태 변경 후 자동 rerun 됩니다.

    except Exception as e:
        st.error(f"❌ 캘린더 등록 중 오류가 발생했습니다: {str(e)}")


def process_user_input(user_input: str):
    """사용자 입력 처리"""
    if not user_input.strip():
        return

    # 사용자 메시지 추가
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })

    # AI 응답 생성
    try:
        system = get_multi_agent_system()

        # 로딩 상태 표시
        with st.spinner("🤖 AI 에이전트들이 최적의 여행 계획을 준비하고 있습니다..."):
            # 멀티 에이전트 시스템 실행
            full_response = ""
            for chunk in system.stream(user_input):
                # 각 단계의 응답을 수집
                for node_name, node_data in chunk.items():
                    if "messages" in node_data and node_data["messages"]:
                        last_message = node_data["messages"][-1]
                        if hasattr(last_message, 'content'):
                            full_response = last_message.content

            # 최종 응답이 없는 경우 기본 메시지
            if not full_response:
                full_response = "죄송합니다. 응답을 생성하는데 문제가 발생했습니다."

        # AI 응답 추가
        ai_timestamp = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "timestamp": ai_timestamp
        })

        # 강제로 페이지 새로고침
        st.rerun()

    except Exception as e:
        st.error(f"❌ 오류가 발생했습니다: {str(e)}")
        # 강제로 페이지 새로고침
        st.rerun()


def main():
    """메인 애플리케이션 실행"""
    st.markdown("<h1 class='main-title'>🌏 여행 AI 어시스턴트</h1>",
                unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>궁금한 여행 계획을 물어보세요! Travel Planner Agent가 도와드릴게요.</p>",
                unsafe_allow_html=True)

    initialize_session_state()

    # AI 에이전트 시스템 로드
    system = get_multi_agent_system()
    if not system:
        st.stop()

    # --- 사이드바 ---
    with st.sidebar:
        st.header("⚙️ 옵션")
        if st.button("🗑️ 채팅 기록 초기화", use_container_width=True):
            st.session_state.messages = []
            # st.rerun() # 불필요, 버튼 클릭 시 자동 rerun

        # 예시 질문 추가
        st.header("💡 예시 질문")
        if st.button("서울 2박 3일 여행", use_container_width=True):
            process_user_input("서울 2박 3일 여행 계획 짜줘")

        if st.button("부산 맛집 투어", use_container_width=True):
            process_user_input("부산 맛집 투어 일정 추천해줘")

        if st.button("제주도 가족 여행", use_container_width=True):
            process_user_input("제주도 가족 여행 계획 세워줘")

        # 캘린더 이벤트 관리 섹션 추가
        st.header("📅 캘린더 이벤트 관리")

        # 이벤트 조회
        if st.button("📋 내 일정 조회", use_container_width=True):
            try:
                from datetime import datetime, timedelta

                from src.services.kakao_calendar_service import \
                    KakaoCalendarService

                calendar_service = KakaoCalendarService()
                now = datetime.now()
                events = calendar_service.get_events_in_range(
                    now,
                    now + timedelta(days=30)
                )

                if events:
                    st.write("### 다가오는 일정")
                    for event in events:
                        st.markdown(f"""
                        **{event.get('title', '제목 없음')}**
                        - 시작: {event.get('start_time', '정보 없음')}
                        - 종료: {event.get('end_time', '정보 없음')}
                        - 이벤트 ID: `{event.get('id', '정보 없음')}`
                        """)
                else:
                    st.info("조회된 일정이 없습니다.")
            except Exception as e:
                st.error(f"일정 조회 중 오류: {e}")

        # 이벤트 수정
        st.subheader("🔧 일정 수정")
        update_event_id = st.text_input("수정할 이벤트 ID", key="update_event_id")
        update_title = st.text_input("새 제목 (선택)", key="update_title")
        update_start_date = st.date_input(
            "새 시작 날짜 (선택)", key="update_start_date")
        update_end_date = st.date_input("새 종료 날짜 (선택)", key="update_end_date")
        update_description = st.text_area(
            "새 설명 (선택)", key="update_description")

        if st.button("✏️ 일정 수정", use_container_width=True):
            try:
                from src.tools.calendar_tools import update_travel_plan_tool

                # 날짜를 문자열로 변환 (선택적)
                start_date_str = update_start_date.strftime(
                    '%Y-%m-%d') if update_start_date else None
                end_date_str = update_end_date.strftime(
                    '%Y-%m-%d') if update_end_date else None

                result = update_travel_plan_tool(
                    event_id=update_event_id,
                    title=update_title or None,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    description=update_description or None
                )
                st.success(result)
            except Exception as e:
                st.error(f"일정 수정 중 오류: {e}")

        # 이벤트 삭제
        st.subheader("🗑️ 일정 삭제")
        delete_event_id = st.text_input("삭제할 이벤트 ID", key="delete_event_id")

        if st.button("❌ 일정 삭제", use_container_width=True):
            try:
                from src.tools.calendar_tools import delete_travel_plan_tool

                result = delete_travel_plan_tool(event_id=delete_event_id)
                st.success(result)
            except Exception as e:
                st.error(f"일정 삭제 중 오류: {e}")

    # --- 메인 채팅 인터페이스 ---
    display_chat_messages()

    # 사용자 입력 처리
    if user_input := st.chat_input("여행 계획을 입력해주세요..."):
        process_user_input(user_input)
        # process_user_input 실행 후 자동으로 rerun되어 메시지가 표시됩니다.
        # 따라서 여기서는 아무것도 할 필요가 없습니다.


if __name__ == "__main__":
    main()
