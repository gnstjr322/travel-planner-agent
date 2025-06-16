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

## ⚙️ 환경 변수 설정

1. `env.example` 파일을 `.env`로 복사
2. 필요한 API 키들을 설정

```bash
cp env.example .env
# .env 파일을 편집하여 API 키 입력
```

## 🚀 실행 방법

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

### Google Calendar API
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. Calendar API 활성화 후 서비스 계정 생성

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

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요. 