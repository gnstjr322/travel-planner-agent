"""
Streamlit UI for Travel Planner Multi-Agent System.
"""
import asyncio
import os
import sys
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from src.config.api_config import api_config
from src.core.multi_agent_system import TravelPlannerMultiAgent

# Add the project root to sys.path
# This assumes streamlit_app.py is at src/ui/streamlit_app.py
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="🌍 여행 플래너 AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


class StreamlitTravelPlanner:
    """Streamlit interface for the travel planner."""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            st.error("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            st.stop()

        # Initialize multi-agent system
        if 'multi_agent' not in st.session_state:
            st.session_state.multi_agent = TravelPlannerMultiAgent(
                self.openai_api_key
            )

        # Initialize session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'current_plan' not in st.session_state:
            st.session_state.current_plan = None

    def render_sidebar(self):
        """Render the sidebar with options and controls."""
        with st.sidebar:
            st.title("🎯 기능 선택")

            st.markdown("### 💬 대화 기록")
            if st.button("대화 기록 초기화"):
                st.session_state.messages = []
                st.session_state.current_plan = None
                st.rerun()

            st.markdown("### 📋 빠른 액션")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔍 장소 검색"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "서울의 유명한 관광지를 검색해주세요",
                        "timestamp": datetime.now()
                    })
                    st.rerun()

            with col2:
                if st.button("📅 일정 작성"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "3박 4일 제주도 여행 계획을 세워주세요",
                        "timestamp": datetime.now()
                    })
                    st.rerun()

            st.markdown("### ⚙️ 설정")
            temperature = st.slider("AI 창의성", 0.0, 1.0, 0.7, 0.1)
            max_tokens = st.slider("최대 응답 길이", 500, 2000, 1000, 100)
            st.session_state.temperature = temperature
            st.session_state.max_tokens = max_tokens

            st.markdown("### 🔗 API 연동 상태")
            api_status = {
                "OpenAI": bool(api_config.openai_api_key),
                "Kakao Map": bool(api_config.kakao_rest_api_key),
                "Kakao Calendar": bool(os.getenv("KAKAO_ACCESS_TOKEN")) and
                bool(api_config.kakao_client_id),
                "Naver Search": bool(api_config.naver_client_id) and
                bool(api_config.naver_client_secret)
            }
            for service, status in api_status.items():
                if status:
                    st.success(f"✅ {service.title()}: 연결됨")
                else:
                    st.warning(f"⚠️ {service.title()}: 미설정")

    def render_main_chat(self):
        """Render the main chat interface."""
        st.title("🌍 여행 플래너 AI 에이전트")
        st.markdown("여행 계획부터 일정 관리까지, AI가 도와드립니다! 💫")

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "timestamp" in message:
                    # 타임스탬프 문자열을 별도 변수로 분리하고 st.caption 호출을 여러 줄로 나눔
                    timestamp_str = message['timestamp'].strftime(
                        '%Y-%m-%d %H:%M:%S')
                    st.caption(
                        f"⏰ {timestamp_str}"
                    )

        # Chat input
        if prompt := st.chat_input("여행에 관해 무엇이든 물어보세요!"):
            # Add user message to session state
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now()
            })

            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
                # 타임스탬프 문자열을 별도 변수로 분리
                timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                st.caption(f"⏰ {timestamp_str}")

            # Process with multi-agent system
            with st.chat_message("assistant"):
                with st.spinner("AI 에이전트들이 작업 중입니다... 🤖"):
                    response = asyncio.run(
                        st.session_state.multi_agent.process_query(prompt)
                    )

                # Display response
                self.display_agent_response(response)

                # Add assistant message to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": self.format_response_for_display(response),
                    "timestamp": datetime.now(),
                    "response_data": response
                })

    def display_agent_response(self, response: dict):
        """Display the multi-agent response in a formatted way."""
        if not response.get("success"):
            st.error(f"❌ 오류가 발생했습니다: {response.get('error', 'Unknown error')}")
            return

        current_step = response.get("current_step", "")
        st.info(f"🎯 처리된 작업: **{current_step}**")

        # Display search results
        if response.get("search_results"):
            st.subheader("🔍 검색 결과")
            search_data = response["search_results"]
            if search_data.get("success"):
                st.success(search_data.get("message", ""))
                with st.expander("상세 검색 결과 보기"):
                    st.write(search_data.get("data", {}))

        # Display travel plan
        if response.get("travel_plan"):
            st.subheader("📋 여행 계획")
            plan_data = response["travel_plan"]
            if plan_data.get("success"):
                st.success(plan_data.get("message", ""))
                with st.expander("여행 계획 상세보기"):
                    plan_info = plan_data.get("data", {})

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("목적지", plan_info.get("destination", "N/A"))
                    with col2:
                        st.metric("출발일", plan_info.get("start_date", "N/A"))
                    with col3:
                        st.metric("종료일", plan_info.get("end_date", "N/A"))

                    if plan_info.get("itinerary"):
                        st.markdown("### 📝 상세 일정")
                        st.write(plan_info["itinerary"])

                # Store current plan for calendar integration
                st.session_state.current_plan = plan_data

        # Display calendar events
        if response.get("calendar_events"):
            st.subheader("📅 캘린더 일정")
            for event in response["calendar_events"]:
                if event.get("success"):
                    st.success(event.get("message", ""))
                    with st.expander("일정 상세보기"):
                        st.json(event.get("data", {}))

        # Display shared plan
        if response.get("shared_plan"):
            st.subheader("🔗 공유 링크")
            share_data = response["shared_plan"]
            if share_data.get("success"):
                st.success(share_data.get("message", ""))
                share_info = share_data.get("data", {})
                if share_info.get("share_url"):
                    st.code(share_info["share_url"], language="text")
                    st.button("링크 복사", key="copy_link")

    def format_response_for_display(self, response: dict) -> str:
        """Format response for chat history display."""
        if not response.get("success"):
            return f"❌ 오류: {response.get('error', 'Unknown error')}"

        current_step = response.get("current_step", "")
        # 메시지를 분리하여 가독성 및 라인 길이 준수
        completion_message = f"🎯 **{current_step}** 작업을 완료했습니다."
        formatted_response = f"{completion_message}\n\n"

        # Add summary based on the step
        if response.get("search_results"):
            # 문자열을 괄호로 묶어 여러 줄로 나누기
            formatted_response += (
                "🔍 장소 검색이 완료되었습니다.\n"
            )

        if response.get("travel_plan"):
            # 문자열을 괄호로 묶어 여러 줄로 나누기
            formatted_response += (
                "📋 여행 계획이 생성되었습니다.\n"
            )

        if response.get("calendar_events"):
            formatted_response += "📅 캘린더에 일정이 추가되었습니다.\n"

        if response.get("shared_plan"):
            # 문자열을 괄호로 묶어 여러 줄로 나누기
            formatted_response += (
                "🔗 공유 링크가 생성되었습니다.\n"
            )

        return formatted_response

    def render_status_panel(self):
        """Render system status and metrics."""
        with st.container():
            st.markdown("### 📊 시스템 상태")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("총 대화", len(st.session_state.messages))

            with col2:
                plan_count = sum(1 for msg in st.session_state.messages
                                 if msg.get("response_data", {}).get("travel_plan"))
                st.metric("생성된 계획", plan_count)

            with col3:
                search_count = sum(1 for msg in st.session_state.messages
                                   if msg.get("response_data", {}).get("search_results"))
                st.metric("장소 검색", search_count)

            with col4:
                st.metric("활성화된 에이전트", "4개")

    def run(self):
        """Run the Streamlit application."""
        self.render_sidebar()

        # Main content area
        main_col, status_col = st.columns([3, 1])

        with main_col:
            self.render_main_chat()

        with status_col:
            self.render_status_panel()


def main():
    """Main function to run the Streamlit app."""
    app = StreamlitTravelPlanner()
    app.run()


if __name__ == "__main__":
    main()
