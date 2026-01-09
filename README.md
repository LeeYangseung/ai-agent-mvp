# AI Agent MVP

> LangGraph 기반의 유연하고 확장 가능한 AI 에이전트 플랫폼

[![License](https://img.shields.io/badge/license-Internal-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)

---

## 📖 목차

- [프로젝트 소개](#-프로젝트-소개)
- [주요 기능](#-주요-기능)
- [빠른 시작](#-빠른-시작)
- [사용 가이드](#-사용-가이드)
- [문서](#-문서)
- [로드맵](#-로드맵)

---

## 🎯 프로젝트 소개

AI Agent MVP는 **LangGraph**를 기반으로 구축된 그래프 기반 AI 에이전트 플랫폼입니다. 복잡한 AI 워크플로우를 시각적으로 설계하고 실행할 수 있으며, RAG(Retrieval-Augmented Generation) 기반의 지식 관리 시스템을 통합하여 문서 기반 질의응답을 지원합니다.

### 💡 LangGraph 철학

- **그래프 기반 워크플로우**: AI 에이전트의 로직을 노드(Node)와 엣지(Edge)로 구성된 방향성 그래프로 표현
- **상태 관리(State Management)**: 공유 상태를 통해 컨텍스트가 전체 워크플로우에 걸쳐 유지
- **유연한 제어 흐름**: 조건 분기, 루프, 병렬 처리 등 복잡한 제어 흐름을 자연스럽게 표현
- **모듈화와 재사용성**: 독립적인 노드 단위 설계로 다양한 그래프에서 재사용 가능
- **추적 가능성**: 모든 실행 과정과 상태 변화를 기록하여 디버깅과 분석 용이

### 🎨 설계 원칙

1. **시각적 직관성**: 드래그 앤 드롭 방식의 그래프 에디터로 쉽게 AI 워크플로우 설계
2. **확장 가능성**: 새로운 노드 타입을 추가하여 기능 확장이 가능한 플러그인 아키텍처

### 🏗️ 기술 스택

- **Frontend**: Next.js 15, React 19, React Flow, TailwindCSS
- **Backend**: FastAPI, LangChain, LangGraph, SQLAlchemy
- **Database**: PostgreSQL, ChromaDB
- **Infrastructure**: Docker, Kubernetes, Nginx Ingress

> 📚 **상세 아키텍처**: [시스템 아키텍처 문서](./docs/architecture.md)

---

## ✨ 주요 기능

### 1. 그래프 에디터 (Graph Editor)

드래그 앤 드롭 방식으로 AI 워크플로우를 시각적으로 설계합니다.

**지원 노드:**
- **InputNode**: 워크플로우 시작점, 초기 상태 설정
- **PromptNode**: LLM 호출, 템플릿 기반 프롬프트 생성
- **RetrievalNode**: 벡터 검색, 관련 문서 조회
- **ConditionNode**: 조건 분기, 동적 경로 결정
- **MergeNode**: 여러 경로 합류, 상태 병합
- **OutputNode**: 최종 결과 포맷팅

> 📚 **상세 가이드**: [그래프 에디터 문서](./docs/features/graph-editor.md)

### 2. Agent 관리

저장된 그래프(Agent)를 관리하고 버전을 추적합니다.

**기능:**
- 그래프 목록/검색/정렬
- 그래프 편집/삭제
- 버전 관리 및 이력 확인

### 3. 지식 관리 (RAG)

문서를 업로드하고 벡터 검색으로 AI가 답변할 수 있는 지식 베이스를 구축합니다.

**주요 기능:**
- **컬렉션 관리**: 문서를 논리적으로 그룹화
- **문서 업로드**: PDF, TXT 파일 지원
- **청킹 전략**: Length, Semantic, Hybrid, Paragraph
- **벡터 검색**: 컬렉션별 독립적인 검색 범위

> 📚 **상세 가이드**: [지식 관리 문서](./docs/features/knowledge-management.md)

---

## 🚀 빠른 시작 (로컬 실행)

### 사전 요구사항

- Docker 20.10+
- Minikube 1.25+
- kubectl 1.25+
- OpenAI API Key

### Minikube로 로컬 실행 (권장)

```bash
# 1. Minikube 시작
cd k8s
./minikube.sh start

# 2. Docker 이미지 빌드
cd ../docker
./docker_build.sh

# 3. Minikube에 이미지 로드
cd ../k8s
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest

# 4. Secret 설정 (OpenAI API 키)
cp secret.example.yaml secret.yaml
vim secret.yaml  # API 키 입력

# 5. 애플리케이션 배포
./deploy.sh

# 6. 접속 설정
sudo sh -c 'echo "127.0.0.1 aiagent.local" >> /etc/hosts'

# 7. 브라우저에서 접속
open http://aiagent.local/
```

**소요 시간**: 약 10-15분

> 📚 **상세 가이드**: [Minikube 배포 가이드](./docs/deployment/minikube.md)

### 로컬 개발 환경 (Backend + Frontend 개별 실행)

```bash
# Backend
cd backend
uv sync --frozen
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/ai_agent_db" # 별도 Postgres 필요
export OPENAI_SECRET_KEY="your-openai-api-key"
./run.sh

# Frontend (다른 터미널)
cd frontend
npm install
npm run dev
```

---

## 📘 사용 가이드

### 시작하기

1. **로그인**: 현재 인증 없음 (향후 추가 예정)
2. **화면 이동**: 좌측 사이드바에서 원하는 메뉴 선택
   - **Graph Editor**: 그래프 설계 및 실행
   - **Agent Management**: 저장된 그래프 관리
   - **Knowledge Management**: 문서 및 컬렉션 관리

### 예제 워크플로우: 문서 기반 Q&A 에이전트 만들기

#### 1단계: 컬렉션 및 문서 준비

1. **지식 관리** 메뉴로 이동
2. **문서 업로드**:
   - `+문서생성` 버튼 클릭  
   2.1 **컬렉션 생성**
     - 컬렉션 선택창 옆 돋보기 버튼 클릭
     - `+새 컬렉션` 버튼 클릭
     - 이름: `insurance_terms`
     - 설명: `보험 약관 문서`
     - `생성` 버튼 클릭
   
   ![컬렉션 생성 가이드](./assets/create_collection.gif)
   
   - 컬렉션: `insurance_terms` 선택
   - 문서명 입력
   - 청킹 방법: **Paragraph** (약관 문서는 구조화되어 있으므로)
   - 파일: 보험 약관 PDF 파일 업로드
   - `생성` 버튼 클릭
3. 업로드 완료 후 인덱싱 진행, 문서 목록에서 상태가 "인덱싱됨"인지 확인

#### 2단계: 그래프 설계

1. **그래프 에디터** 메뉴로 이동
2. **노드 추가**:
   - **InputNode**: 
     - ID: `input`
     - `output`: `user_input`
   - **RetrievalNode**:
     - ID: `retrieval`
     - `collection_name`: `insurance_terms`
     - `top_k`: 3
     - `inputs`
       - `query`: `input.user_input`
     - `output`: `context`
   - **PromptNode**:
     - ID: `prompt`
     - `system_prompt`: "당신은 보험 약관 전문가입니다. 제공된 컨텍스트를 바탕으로 정확하게 답변하세요."
     - `user_prompt`: "질문: {question}\n\n컨텍스트:\n{context}\n\n답변:"
     - `inputs`
       - `question`: `input.user_input`
       - `context`: `retrieval.context`
     - `output_key`: `answer`
   - **OutputNode**:
     - ID: `output`
     - `wrap_template`: "AI 답변 : {answer}"
     - `inputs`
       - `answer`: `prompt.answer`
     - `output`: `agent_output`

3. **엣지 연결**:
   - `input` → `retrieval`
   - `retrieval` → `prompt`
   - `prompt` → `output`

4. **그래프 저장**:
   - 이름: `보험 약관 Q&A`
   - 설명: `보험 약관 문서 기반 질의응답 에이전트`
   - 버전: 1

#### 3단계: 테스트

1. 우측 챗 패널에 질문 입력
   ```
   해지 환급금에 대해 알려줘
   ```
2. "전송" 버튼 클릭
3. **결과 확인**:
   - **최종 결과**: agent_output을 markdown 형태로 파싱한 결과 출력
   - **노드별입출력** 탭: 각 노드의 실행 결과 확인
     - `retrieval`: 검색된 3개의 청크 내용
     - `prompt`: LLM이 생성한 답변
   - **그래프 히스토리** 탭: 그래프 실행 히스토리
   - **그래프 스테이트** 탭: 그래프의 최종 상태 dict

#### 4단계: Agent 관리에서 재사용

1. **Agent 관리** 메뉴로 이동
2. "보험 약관 Q&A" 그래프 Row 확인
3. 필요 시 더블클릭 또는 우측 편집 버튼을 통해 그래프 에디터로 진입해 편집하여 프롬프트 개선 또는 노드 추가

---

## 📚 문서

### 아키텍처
- [시스템 아키텍처](./docs/architecture.md)

### 기능별 가이드
- [그래프 에디터](./docs/features/graph-editor.md)
- [지식 관리 (RAG)](./docs/features/knowledge-management.md)

### 배포
- [Minikube 로컬 배포](./docs/deployment/minikube.md)

### 개발자 문서
- [Backend 개발 가이드](./backend/README.md)
- [Frontend 개발 가이드](./frontend/README.md)

### 문제 해결
- [트러블슈팅 가이드](./docs/troubleshooting.md)

---

## 🛣️ 로드맵

자세한 로드맵은 [여기](./docs/roadmap.md)에서 확인하세요.

### v1.1 (다음 릴리스)
- [ ] Reranker 지원 (Cohere, Cross-Encoder)
- [ ] HyDE, Query Expansion

### v1.2
- [ ] Web Search Node, Tool Node, MCP Node
- [ ] 실시간 스트리밍, Undo/Redo
- [ ] 그래프 템플릿 마켓플레이스

### v2.0
- [ ] 사용자 인증 및 권한 관리
- [ ] 멀티 에이전트 협업
- [ ] 성능 모니터링 대시보드
- [ ] 커스텀 노드 플러그인 시스템

---

## 🔧 문제 해결

일반적인 문제와 해결 방법:

### Ingress 접속 불가
```bash
cd k8s
./minikube.sh status
./minikube.sh tunnel
```

### Pod가 ImagePullBackOff
```bash
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest
kubectl rollout restart deployment/ai-agent-backend-deployment
```

### Backend API 호출 실패 (CORS)
`backend/app/main.py`의 `allow_origins`에 Frontend URL 추가 후 재배포

> 📚 **전체 가이드**: [트러블슈팅 문서](./docs/troubleshooting.md)

---

## 📄 라이선스

이 프로젝트는 내부용으로 사용됩니다. 별도의 오픈소스 라이선스는 적용되지 않습니다.

## 💬 문의

- GitHub Issues에 등록

---

**Happy Coding! 🎉**
