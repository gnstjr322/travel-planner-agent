# Python 3.11 기반 이미지 사용
FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

# 시스템 패키지 업데이트 및 필요한 도구 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    vim \
    tree \
    htop \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /workspace

# Python 패키지 관리를 위한 pip 업그레이드
RUN pip install --upgrade pip

# 기본 Python 패키지들 미리 설치 (캐시 최적화)
RUN pip install \
    streamlit \
    langchain \
    langgraph \
    langchain-openai \
    langchain-community \
    python-dotenv \
    requests \
    pandas \
    numpy \
    pydantic \
    fastapi \
    uvicorn \
    pytest \
    black \
    flake8 \
    isort

# 포트 노출
EXPOSE 8501 8000 5000

# 기본 명령어
CMD ["bash"] 