# 여행 AI Assistance - Travel Planner Agent

AI 기반 멀티 에이전트 시스템을 활용한 지능형 여행 계획 서비스입니다.

## 주요 기능

- **멀티 에이전트 시스템**: 5개의 전문 에이전트가 협력하여 최적의 여행 계획 제공
- **Supervisor-Worker 구조**: 중앙 Supervisor가 Worker 에이전트에게 작업을 위임하는 워크플로우
- **Handoff 기반 라우팅**: `Command`를 사용한 명시적 제어권 전달로 에이전트 간 통신
- **실시간 정보 검색**: Tavily, 카카오맵 API를 통한 최신 여행 정보 수집
- **캘린더 연동**: 여행 일정을 카카오 캘린더에 자동으로 등록
- **공유 기능**: 완성된 여행 계획을 Notion 페이지로 생성하여 쉽게 공유

## 에이전트 구조

### 아키텍처
중앙 `Supervisor`가 사용자 요청을 받아 분석한 후, 가장 적합한 `Worker` 에이전트에게 작업을 위임합니다. 각 Worker는 작업 완료 후 제어권을 다시 Supervisor에게 반환하는 '중앙 집중형' 구조입니다.

### 에이전트 구조 트리
```
Travel Multi-Agent System
│
├── Supervisor Agent (중앙 관리자)
│   ├── transfer_to_planner_agent
│   ├── transfer_to_location_search_agent
│   ├── transfer_to_calendar_agent
│   └── transfer_to_share_agent
│
├── PlannerAgent (여행 계획)
│   ├── web_search_tool
│   ├── create_travel_plan_tool
│   ├── modify_travel_plan_tool
│   └── validate_travel_plan_tool
│
├── LocationSearchAgent (장소 검색)
│   ├── location_search_tool
│   └── nearby_search_tool
│
├── VerifierAgent (정보 검증)
│   └── [구현 대기]
│
├── CalendarAgent (캘린더 연동)
│   ├── add_travel_plan_to_calendar
│   ├── check_calendar_availability
│   ├── update_travel_plan_tool
│   ├── delete_travel_plan_tool
│   └── search_travel_plan_tool
│
└── ShareAgent (공유)
    └── create_notion_page_tool
```

### 에이전트 상세

1. **Supervisor Agent**
   - 사용자 요청을 분석하여 적절한 Worker 에이전트 선택
   - 전체 워크플로우 조율 및 상태 관리

2. **Planner Agent**
   - 여행 계획 생성, 수정, 제안
   - 웹 검색을 통해 초기 정보 수집 및 계획 구조화

3. **LocationSearchAgent**
   - 카카오맵 API를 통해 특정 장소 정보 및 주변 시설 검색

4. **Calendar Agent**
   - 확정된 여행 계획을 카카오 캘린더에 등록 및 관리

5. **Share Agent**
   - 완성된 여행 계획을 Notion 페이지로 변환 및 공유 링크 생성

6. **Verifier Agent (미구현)**
   - 정보의 신뢰성을 검증하여 '환각'을 최소화하는 역할 (v2.0 구현 예정)

## Handoff 기반 라우팅 시스템

본 시스템은 LangGraph의 `Command` 객체를 활용한 'Handoff' 방식으로 에이전트 간 통신을 수행합니다.

Supervisor는 `create_handoff_tool`을 통해 각 Worker에게 작업을 명시적으로 위임하는 도구를 가집니다. Worker 에이전트가 호출되면, `Command`가 Supervisor의 상태를 업데이트하고 제어권을 해당 Worker로 넘겨줍니다. 이 방식은 키워드 기반의 모호한 라우팅 대신, 명확하고 안정적인 워크플로우를 보장합니다.

### 워크플로우 구조
```
사용자 입력
    ↓
Supervisor Agent
    ↓ (Handoff 라우팅)
    ├── PlannerAgent ──→ Supervisor
    ├── LocationSearchAgent ──→ Supervisor  
    ├── CalendarAgent ──→ Supervisor
    └── ShareAgent ──→ Supervisor
    ↓
최종 응답 또는 END
```

## 확장성 설계: LLM 및 프롬프트 관리

LLM 모델과 프롬프트를 코드에서 분리하여 중앙에서 관리하는 구조를 가집니다. 이를 통해 모델 교체, 프롬프트 버전 관리, A/B 테스트 등을 코드 수정 없이 설정 파일 변경만으로 수행이 가능합니다.

### 1. 설정 기반 LLM 로딩

- **관리**: `src/config/models.yml` 파일에서 사용 가능한 모든 LLM(OpenAI, Google 등)의 정보(모델명, 속성 등)와 각 에이전트에 할당할 모델을 정의
- **로딩**: `ModelProvider`가 이 설정 파일을 읽어, 각 에이전트에 맞는 LangChain 모델 객체를 동적으로 생성하여 주입합니다. 이를 통해 에이전트별로 다른 LLM을 할당하거나, 'gpt-4o-mini'에서 'gpt-4o'로의 전환이 가능합니다.

```yaml
# 예시: src/config/models.yml
models:
  - alias: "fast_model"
    provider: "openai"
    name: "gpt-4o-mini"
  - alias: "smart_model"
    provider: "openai"
    name: "gpt-4o"

agent_model_mapping:
  default: "fast_model"
  supervisor: "smart_model"
```

### 2. 프롬프트 버전 관리

- **외부 파일 분리**: 모든 프롬프트는 `src/prompts/` 디렉토리 내에 버전별(`v1`, `v2`...)/에이전트별(`supervisor.yml`...)로 관리되도록 설계했습니다
- **프롬프트 매니저**: `PromptManager`가 버전과 에이전트 이름을 받아 해당 프롬프트 파일을 동적으로 로드합니다. 

```
# 프롬프트 파일 구조
src/prompts/templates/
└── v1/
    ├── supervisor.yml
    └── planner_agent.yml
```

## 기술 스택

- **Framework**: LangGraph (Multi-Agent Orchestration)
- **LLM**: OpenAI GPT-4o-mini
- **Search**: Tavily, Kakao Maps API
- **Calendar**: Kakao Calendar API
- **Sharing**: Notion API
- **UI**: Streamlit
- **Language**: Python 3.11+

## 설치 및 실행

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
`.env` 파일을 생성하고 다음 내용을 추가합니다.
- 카카오 API 는 [카카오 개발자 사이트](https://developers.kakao.com)에서 앱을 생성하고 REST API 키를 발급받아야 합니다. 
- 노션 API 또한 [노션 개발자 사이트](https://www.notion.so/my-integrations)에서 발급받을 수 있습니다.
- TavilyAPI 는 [Tavily 개발자 사이트](https://app.tavily.com/home)에서 회원가입 후 API 키를 발급받습니다.

```bash
# OpenAI
OPENAI_API_KEY="your_openai_api_key"

# Kakao
KAKAO_REST_API_KEY="your_kakao_rest_api_key"
KAKAO_REDIRECT_URI="https://localhost:3000/callback"

# Notion
NOTION_API_KEY="your_notion_api_key"
NOTION_DATABASE_ID="your_notion_database_id"
```

### 4. 애플리케이션 실행
```bash
python app.py
```

## 프로젝트 구조

```
travel-planner-agent/
├── src/
│   ├── agents/          # 에이전트 구현
│   ├── core/            # 멀티 에이전트 시스템 핵심 (LangGraph)
│   ├── tools/           # 에이전트 도구들
│   ├── services/        # 외부 서비스 연동 (카카오, 노션 등)
│   ├── prompts/         # 프롬프트 템플릿
│   ├── config/          # 설정 파일
│   └── ui/              # Streamlit 사용자 인터페이스
├── design/              # 설계 문서 및 다이어그램
└── logs/                # 로그 파일
```

## 워크플로우 예시

1. **사용자**: "서울 2박 3일 여행 계획 세워주세요"
2. **Supervisor**: 요청 분석 → `transfer_to_planner_agent` 호출
3. **PlannerAgent**: 웹 검색으로 기본 계획 생성 → Supervisor에게 결과 보고
4. **Supervisor**: 추가 정보 필요 시 → `transfer_to_location_search_agent` 호출
5. **LocationSearchAgent**: 맛집, 명소 정보 검색 → Supervisor에게 결과 보고
6. **Supervisor**: 계획 완성 후 → `transfer_to_calendar_agent` 호출
7. **CalendarAgent**: 카카오 캘린더에 일정 등록 → Supervisor에게 보고
8. **Supervisor**: 최종 단계 → `transfer_to_share_agent` 호출
9. **ShareAgent**: Notion 페이지 생성 및 링크 반환 → 최종 완료

## 결과

- **/screenshot**: 해당 프로젝트의 결과를 보시려면 /screenshot 폴더를 확인하시면 됩니다. 
