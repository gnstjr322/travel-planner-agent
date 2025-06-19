# 🌍 Travel Planner Multi-Agent

여행 일정을 계획해주는 멀티 에이전트 시스템입니다. LangChain과 LangGraph를 활용하여 대화형 여행 계획 서비스를 제공합니다.

## 🚀 주요 기능

- **🔍 여행 장소 검색**: 에이전트와의 대화를 통한 여행지 검색
- **📋 여행 계획서 작성**: AI 기반 맞춤형 여행 일정 생성
- **📅 캘린더 연동**: 여행 일정 등록, 조회, 수정, 삭제
- **📤 계획서 공유**: 외부 공유 기능
- **🛡️ 신뢰성 보장**: 거짓 정보 방지 시스템

## 🛠️ 기술 스택

- **LLM Framework**: LangChain, LangGraph
- **UI**: Streamlit
- **LLM Model**: OpenAI GPT-4
- **External APIs**: Kakao Map, Naver Search, Google Calendar
- **Development**: Docker, DevContainer

## 🏗️ 프로젝트 구조

```
travel-planner-agent/
├── .devcontainer/          # DevContainer 설정
│   ├── devcontainer.json
│   └── Dockerfile
├── src/                    # 소스 코드
│   ├── agents/            # 멀티 에이전트
│   ├── models/            # 데이터 모델
│   ├── services/          # 외부 API 서비스
│   ├── utils/             # 유틸리티
│   └── ui/                # Streamlit UI
├── tests/                 # 테스트 코드
├── docs/                  # 문서
├── config/                # 설정 파일
├── requirements.txt       # Python 의존성
├── docker-compose.yml     # Docker Compose 설정
└── README.md
```

## 🐳 개발 환경 설정

### 1. DevContainer 사용 (권장)

```bash
# VS Code에서 프로젝트 열기
code .

# Command Palette (Ctrl+Shift+P)에서
# "Dev Containers: Reopen in Container" 선택
```

### 2. Docker Compose 사용

```bash
# 컨테이너 빌드 및 실행
docker-compose up -d

# 컨테이너 접속
docker-compose exec travel-planner bash
```

### 3. 로컬 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

## 🔧 환경 설정

### 1. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 필요에 따라 추가하세요:

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Kakao APIs
KAKAO_REST_API_KEY=your_kakao_rest_api_key_here # 주로 지도, 로컬 검색용
KAKAO_CLIENT_ID=your_kakao_client_id_here     # OAuth 인증용 (톡캘린더 등 사용자 정보 기반 API)
# KAKAO_REDIRECT_URI=your_kakao_redirect_uri_here # OAuth 리다이렉트 URI
# KAKAO_APP_ADMIN_KEY=your_kakao_app_admin_key_here # 일부 공개 API용 (필요시)
# KAKAO_ACCESS_TOKEN=user_kakao_access_token # 개발 및 테스트 시 직접 발급한 액세스 토큰 (OAuth 흐름 구현 전)

# Naver API (선택사항)
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# 기타 API 키 (Amadeus, Google Maps 등 대체재 또는 추가 기능용)
# GOOGLE_MAPS_API_KEY=your_google_maps_api_key # 카카오맵 대신 사용 시
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_api_secret
BOOKING_API_KEY=your_booking_api_key

# Application Settings
APP_TIMEZONE=Asia/Seoul
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Streamlit configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### 2. 카카오 API 설정

#### 2.1 카카오 개발자 등록 및 앱 생성
1.  [카카오 개발자 (Kakao Developers)](https://developers.kakao.com/) 사이트에 접속하여 로그인 또는 회원가입합니다.
2.  "내 애플리케이션"에서 "애플리케이션 추가하기"를 선택합니다.
3.  앱 아이콘, 앱 이름을 입력하고 사업자명(개인일 경우 개인)을 입력하여 앱을 생성합니다.

#### 2.2 앱 키 확인
-   생성된 애플리케이션 선택 > 앱 설정 > 요약 정보에서 **REST API 키**를 확인하여 `.env` 파일의 `KAKAO_REST_API_KEY`에 설정합니다. (주로 카카오맵, 로컬 API 등에 사용)

#### 2.3 플랫폼 설정
-   앱 설정 > 플랫폼 > Web 플랫폼 등록: 서비스할 웹 주소를 등록합니다 (예: `http://localhost:8501` для Streamlit 로컬 테스트).
-   OAuth 리다이렉트 URI를 사용할 경우, 여기에 등록해야 합니다. (예: `http://localhost:8501/oauth`)

#### 2.4 카카오 로그인 및 동의 항목 설정
-   제품 설정 > 카카오 로그인: "활성화 설정"을 ON으로 변경합니다.
-   **Redirect URI 등록**: 카카오 로그인을 통해 액세스 토큰을 발급받을 리다이렉트 URI를 등록합니다. (구현 방식에 따라 필요)
-   **동의항목**:
    -   개인정보: 닉네임, 프로필 사진 (선택)
    -   **카카오 서비스**: **카카오톡 캘린더 (필수)** - "일정 만들기", "일정 읽기", "캘린더 읽기" 등의 필요한 모든 권한을 설정하고 동의를 받도록 합니다. "동의 화면 미리보기"로 확인 가능.
    -   필요한 동의항목을 설정하고, "필수 동의" 또는 "선택 동의" 여부를 결정합니다. (개인정보보호법 준수)

#### 2.5 톡캘린더 API 사용을 위한 추가 정보
-   카카오톡 캘린더 API는 주로 OAuth 2.0 기반의 사용자 토큰을 사용하여 호출합니다.
-   `.env` 파일의 `KAKAO_CLIENT_ID`는 앱 설정 > 요약 정보의 "네이티브 앱 키" 또는 "REST API 키"가 아닌, 카카오 로그인 설정 시 사용되는 클라이언트 ID 개념입니다. (REST API 키를 Client ID로 사용하는 경우도 있음 - 카카오 문서 확인 필요)
-   사용자로부터 OAuth 동의를 받고 액세스 토큰을 발급받는 로직이 애플리케이션에 구현되어야 합니다. 개발 초기에는 [카카오 개발자 도구의 토큰 발급](https://developers.kakao.com/tool/token) 기능을 사용하여 테스트용 토큰을 발급받아 `KAKAO_ACCESS_TOKEN` 환경변수에 설정 후 사용할 수 있습니다.

### 3. (구글 캘린더 설정 부분 삭제)

# 🚀 실행 방법

```bash
# Streamlit 앱 실행
streamlit run src/ui/main.py

# 또는 Docker 환경에서
docker-compose exec travel-planner streamlit run src/ui/main.py
```

## 📝 API 키 발급 가이드

### OpenAI API
1. [OpenAI Platform](https://platform.openai.com/) 접속
2. API Keys 메뉴에서 새 키 생성

### Kakao API
1. [Kakao Developers](https://developers.kakao.com/) 접속
2. 애플리케이션 생성 후 REST API 키 확인

### Naver API
1. [Naver Developers](https://developers.naver.com/) 접속
2. 애플리케이션 등록 후 Client ID/Secret 확인

## 🧪 테스트 실행

```bash
# 단위 테스트
pytest tests/

# 커버리지 포함
pytest --cov=src tests/
```

## 📚 개발 가이드

- **코드 스타일**: Black, isort, flake8 사용
- **커밋 컨벤션**: Conventional Commits
- **브랜치 전략**: Git Flow


## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.