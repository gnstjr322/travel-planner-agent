#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
디버그 테스트 스크립트 - 전체 과정 확인
"""

import os
import sys
from pathlib import Path

from langchain_core.messages import convert_to_messages

from src.core.multi_agent_system import TravelMultiAgentSystem

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def safe_print_messages(update, last_message=False):
    """안전한 메시지 출력 함수"""
    try:
        is_subgraph = False
        if isinstance(update, tuple):
            ns, update = update
            if len(ns) == 0:
                return

            graph_id = ns[-1].split(":")[0]
            print(f"🔄 서브그래프 {graph_id}:")
            is_subgraph = True

        for node_name, node_update in update.items():
            update_label = f"📝 노드 {node_name}:"
            if is_subgraph:
                update_label = "  " + update_label

            print(update_label)

            if "messages" in node_update:
                messages = convert_to_messages(node_update["messages"])
                if last_message and messages:
                    messages = messages[-1:]

                for m in messages:
                    content = str(m.content)

                    if is_subgraph:
                        print(f"    {content}")
                    else:
                        print(f"  {content}")
            print()
    except Exception as e:
        print(f"  ⚠️ 메시지 출력 중 오류: {e}")


def main():
    """메인 함수"""
    print("🚀 여행 계획 에이전트 전체 과정 테스트")
    print("=" * 60)

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경 변수를 설정해주세요.")
        return

    try:
        # 시스템 초기화
        print("📋 시스템 초기화 중...")
        system = TravelMultiAgentSystem()
        print("✅ 시스템 초기화 완료")

        # 테스트 쿼리
        query = "속초 여행 주말에 갔다올 계획 세워줘. 시작은 토요일 오후3시부터하고. 최종 결과물은 노션에 등록."
        print(f"\n🔍 테스트 쿼리: {query}")
        print("-" * 60)

        # 스트림 실행
        step_count = 0
        max_steps = 50  # 최대 단계 제한

        for chunk in system.stream(query):
            step_count += 1
            print(f"\n--- 단계 {step_count} ---")

            safe_print_messages(chunk, last_message=True)

            # 무한 루프 방지
            if step_count >= max_steps:
                print("⚠️ 최대 단계 수에 도달했습니다. 테스트를 종료합니다.")
                break

        print("\n✅ 테스트 완료!")

    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
