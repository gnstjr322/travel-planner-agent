"""
Streamlit UI for Travel Planner Multi-Agent System.
"""
import asyncio
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from src.config.settings import settings
from src.core.multi_agent_system import TravelPlannerSupervisor

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
    page_title="여행 플래너 AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


def run_async_in_thread(coro):
    """Streamlit에서 안전하게 비동기 함수를 실행하는 헬퍼 함수"""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()


class StreamlitTravelPlanner:
    """Streamlit interface for the travel planner."""

    def __init__(self):
        # Initialize multi-agent system
        if 'multi_agent' not in st.session_state:
            try:
                st.session_state.multi_agent = TravelPlannerSupervisor()
            except Exception as e:
                st.error(f"멀티 에이전트 시스템 초기화 실패: {str(e)}")
                st.stop()

        # Initialize session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'current_plan' not in st.session_state:
            st.session_state.current_plan = None
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []

    def render_sidebar(self):
        """Render the sidebar with options and controls."""
        with st.sidebar:
            st.title("🎯 기능 선택")

            st.markdown("### 💬 대화 기록")
            if st.button("대화 기록 초기화"):
                st.session_state.messages = []
                st.session_state.current_plan = None
                st.session_state.conversation_history = []
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
                if st.button("📅 여행 계획"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "여행 계획을 세워주세요",
                        "timestamp": datetime.now()
                    })
                    st.rerun()

            st.markdown("### 💡 사용 안내")
            st.info("""
            **여행 계획 요청 시 필요한 정보:**
            
            📅 **언제**: 여행 날짜 (예: 12월 25일)
            📍 **어디**: 여행 목적지 (예: 서울, 부산, 제주도)
            ⏰ **며칠**: 여행 기간 (예: 1박2일, 2박3일)
            
            이 정보들이 없으면 AI가 먼저 질문할 거예요!
            """)

            st.markdown("### ⚙️ 설정")
            temperature = st.slider("AI 창의성", 0.0, 1.0, 0.7, 0.1)
            max_tokens = st.slider("최대 응답 길이", 500, 2000, 1000, 100)
            st.session_state.temperature = temperature
            st.session_state.max_tokens = max_tokens

            st.markdown("### 🔗 API 연동 상태")
            api_status = {
                "OpenAI": bool(settings.openai_api_key),
                "Google Search": bool(settings.google_search_api_key) and bool(settings.google_search_cx),
                "Kakao Map": bool(settings.kakao_rest_api_key),
                "Kakao Calendar": bool(settings.kakao_refresh_token)
            }
            for service, status in api_status.items():
                if status:
                    st.success(f"✅ {service}: 연결됨")
                else:
                    st.warning(f"⚠️ {service}: 미설정")

    def render_main_chat(self):
        """Render the main chat interface."""
        st.title("🌍 여행 플래너 AI")
        st.markdown("여행 정보 수집부터 계획 수립까지, 단계별로 AI가 도와드립니다! 💫")

        # 진행 단계 표시
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**1단계** 📝 정보 수집")
        with col2:
            st.markdown("**2단계** 🔍 장소 검색")
        with col3:
            st.markdown("**3단계** 📅 계획 생성")
        st.markdown("---")

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
                    try:
                        # Streamlit에서 안전한 비동기 실행
                        response = run_async_in_thread(
                            st.session_state.multi_agent.process_query(
                                prompt,
                                st.session_state.conversation_history
                            )
                        )
                    except Exception as e:
                        st.error(f"❌ 처리 중 오류가 발생했습니다: {str(e)}")
                        response = {
                            "success": False,
                            "response": f"오류가 발생했습니다: {str(e)}",
                            "conversation_history": st.session_state.conversation_history
                        }

                # Display response
                self.display_agent_response(response)

                # Update conversation history
                if response.get("conversation_history"):
                    st.session_state.conversation_history = response["conversation_history"]

                # Add assistant message to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.get("response", "No response"),
                    "timestamp": datetime.now(),
                    "response_data": response
                })

    def display_agent_response(self, response: dict):
        """Display the multi-agent response in a formatted way."""
        if not response.get("success"):
            st.error(
                f"❌ 오류가 발생했습니다: {response.get('response', 'Unknown error')}")
            return

        response_content = response.get("response", "죄송합니다, 답변을 생성하지 못했습니다.")
        st.markdown(response_content)

    def format_response_for_display(self, response: dict) -> str:
        """Formats the agent's response for display in the chat history."""
        if response.get("success"):
            return response.get("response", "No content")
        else:
            return f"Error: {response.get('response', 'Unknown error')}"

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
                st.metric("활성화된 에이전트", "3개")

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
