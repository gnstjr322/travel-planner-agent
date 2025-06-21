# 여행 계획 AI Assistance - Travel Planner Agent

AI 기반 멀티 에이전트 시스템을 활용한 지능형 여행 계획 서비스입니다.

## 🌟 주요 기능

- **멀티 에이전트 시스템**: 5개의 전문 에이전트가 협력하여 최적의 여행 계획 제공
- **Agent 간 직접 통신**: Network 패턴으로 Agent들이 서로 직접 통신하며 효율적인 워크플로우 구현
- **지능형 라우팅**: 각 Agent가 작업 결과에 따라 다음 단계를 자동으로 결정
- **실시간 정보 검색**: DuckDuckGo를 통한 최신 여행 정보 수집
- **정보 검증**: 수집된 정보의 정확성을 자동으로 검증
- **캘린더 연동**: 여행 일정을 자동으로 캘린더에 등록
- **공유 기능**: 완성된 여행 계획을 쉽게 공유

## 🤖 에이전트 구조

### Network 패턴 (Agent 직접 통신)
현재 시스템은 Agent들이 서로 직접 통신할 수 있는 Network 패턴을 사용합니다:

```
Supervisor ──┬─→ Planner ──┬─→ Searcher ──┬─→ Verifier ──┬─→ Calendar ──→ Sharer ──→ END
             │             │              │              │              │
             │             └─→ Verifier   └─→ Planner    ├─→ Planner    └─→ END
             │                             │              └─→ Sharer
             ├─→ Searcher ──┬─→ Verifier   └─→ Supervisor
             │              └─→ Planner
             ├─→ Verifier ──┬─→ Planner
             │              ├─→ Calendar
             │              └─→ Sharer
             ├─→ Calendar ──┬─→ Sharer
             │              └─→ END
             └─→ Sharer ────→ END
```

### 에이전트 상세

1. **Supervisor Agent** 🎯
   - 사용자 요청을 분석하여 적절한 첫 번째 에이전트 선택
   - 전체 워크플로우 조율

2. **Planner Agent** 📋
   - 여행 계획 생성 및 수정
   - 다음 단계: 검색 → 검증 → 캘린더 → 완료

3. **Searcher Agent** 🔍
   - 여행지 정보, 맛집, 숙소 등 실시간 검색
   - 다음 단계: 검증 → 계획 수정

4. **Verifier Agent** ✅
   - 검색된 정보의 정확성 검증
   - 다음 단계: 계획 수정 → 캘린더 → 공유

5. **Calendar Agent** 📅
   - 여행 일정을 캘린더 이벤트로 변환
   - 다음 단계: 공유

6. **Sharer Agent** 📤
   - 완성된 여행 계획 포맷팅 및 공유 링크 생성
   - 다음 단계: 완료

## 🚀 지능형 라우팅 시스템

각 Agent는 작업 완료 후 다음 단계를 자동으로 결정합니다:

### 키워드 기반 라우팅
- **"검색이 필요합니다"** → Searcher Agent로 이동
- **"검증이 필요합니다"** → Verifier Agent로 이동  
- **"캘린더 등록이 필요합니다"** → Calendar Agent로 이동
- **"공유가 필요합니다"** → Sharer Agent로 이동
- **"작업 완료"** → 워크플로우 종료

### 기본 라우팅 규칙
- Planner → Searcher (기본값)
- Searcher → Verifier (기본값)
- Verifier → Calendar (기본값)
- Calendar → Sharer (기본값)
- Sharer → END (항상)

## 🛠️ 기술 스택

- **Framework**: LangGraph (Multi-Agent Orchestration)
- **LLM**: OpenAI GPT-4
- **Search**: DuckDuckGo Search API
- **UI**: Streamlit
- **Language**: Python 3.11+

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd travel-planner-agent
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가:
```bash
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
```

### 4. 애플리케이션 실행

#### Streamlit UI 실행
```bash
streamlit run src/ui/streamlit_app.py
```

#### 직접 테스트
```bash
python test_refactored_agent.py
```

## 🧪 테스트

### 라우팅 로직 테스트
```bash
python test_refactored_agent.py
# 옵션 2 선택: 라우팅 로직 테스트
```

### 대화형 테스트
```bash
python test_refactored_agent.py
# 옵션 3 선택: 대화형 테스트
```

## 📁 프로젝트 구조

```
travel-planner-agent/
├── src/
│   ├── agents/          # 에이전트 구현
│   ├── core/           # 멀티 에이전트 시스템 핵심
│   ├── tools/          # 에이전트 도구들
│   ├── services/       # 외부 서비스 연동
│   ├── prompts/        # 프롬프트 템플릿
│   ├── config/         # 설정 파일
│   └── ui/            # 사용자 인터페이스
├── design/            # 설계 문서 및 다이어그램
├── logs/             # 로그 파일
└── test_refactored_agent.py  # 테스트 스크립트
```

## 🔄 워크플로우 예시

1. **사용자**: "서울 2박 3일 여행 계획 세워주세요"
2. **Supervisor**: 요청 분석 → Planner로 라우팅
3. **Planner**: 기본 계획 생성 → "검색이 필요합니다" → Searcher로 이동
4. **Searcher**: 서울 관광지/맛집 검색 → "검증이 필요합니다" → Verifier로 이동
5. **Verifier**: 정보 검증 → "캘린더 등록이 필요합니다" → Calendar로 이동
6. **Calendar**: 일정 등록 → "공유가 필요합니다" → Sharer로 이동
7. **Sharer**: 계획 포맷팅 및 공유 → 완료

## 🎯 특징

- **자율적 의사결정**: 각 Agent가 독립적으로 다음 단계 결정
- **유연한 워크플로우**: 상황에 따라 동적으로 경로 변경
- **오류 복구**: 예외 상황 시 Supervisor로 안전한 복귀
- **확장 가능**: 새로운 Agent 추가 용이