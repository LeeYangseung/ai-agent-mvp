# 시스템 아키텍처

## 전체 구조도

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Graph Editor │  │ Agent Mgmt   │  │ Knowledge (RAG)      │   │
│  │ (React Flow) │  │ (List/Search)│  │ (Collection/Doc)     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Layer (v1)                        │  │
│  │  /graphs  /documents  /collections  /chunks              │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                            │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │              Service Layer                               │  │
│  │  - Graph Service      - Document Service                 │  │
│  │  - Node Service       - Collection Service               │  │
│  │  - Edge Service       - Chunk Service                    │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                            │
│  ┌────────────────▼─────────────────┐  ┌───────────────────┐   │
│  │       Graph Runner               │  │  Chunking Utils   │   │
│  │   (LangGraph Executor)           │  │  - Length         │   │
│  │                                  │  │  - Semantic       │   │
│  │  ┌────────────────────────────┐  │  │  - Hybrid         │   │
│  │  │  Node Implementations      │  │  │  - Paragraph      │   │
│  │  │  - InputNode               │  │  └───────────────────┘   │
│  │  │  - PromptNode              │  │                          │
│  │  │  - RetrievalNode           │  │  ┌───────────────────┐   │
│  │  │  - ConditionNode           │  │  │  Vector Store     │   │
│  │  │  - MergeNode               │  │  │   Utils (Chroma)  │   │
│  │  │  - OutputNode              │  │  └───────────────────┘   │
│  │  └────────────────────────────┘  │                          │
│  └──────────────────────────────────┘                          │
└───────────────────┬──────────────────────┬─────────────────────┘
                    │                      │
        ┌───────────▼────────┐  ┌──────────▼──────────┐
        │   PostgreSQL       │  │   ChromaDB          │
        │   (Metadata)       │  │   (Vector Store)    │
        │                    │  │                     │
        │  - Graphs          │  │  - Embeddings       │
        │  - Nodes           │  │  - Collections      │
        │  - Edges           │  │  - Vector Index     │
        │  - Documents       │  │                     │
        │  - Chunks          │  │                     │
        │  - Collections     │  │                     │
        │  - Graph History   │  │                     │
        └────────────────────┘  └─────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              Infrastructure (Kubernetes)                        │
│  - Deployments: Backend, Frontend, PostgreSQL                   │
│  - Services: ClusterIP, LoadBalancer                            │
│  - Ingress: Nginx Ingress Controller                            │
│  - ConfigMaps: Environment Variables                            │
│  - Secrets: Sensitive Data (DB Credentials, API Keys)           │
│  - Persistent Volumes: DB & Vector Store Data Persistence       │
└─────────────────────────────────────────────────────────────────┘
```

## 컴포넌트 역할

| 컴포넌트 | 역할 | 주요 기술 |
|---------|------|----------|
| **Frontend** | 사용자 인터페이스 제공, 그래프 시각화 | Next.js 15, React 19, React Flow, TailwindCSS |
| **Backend** | 비즈니스 로직, API 제공, 그래프 실행 | FastAPI, LangChain, LangGraph, SQLAlchemy |
| **PostgreSQL** | 메타데이터 영속화 (그래프, 문서, 사용자 등) | PostgreSQL 14+ |
| **ChromaDB** | 벡터 임베딩 저장 및 유사도 검색 | Chroma 1.1.0 |
| **Kubernetes** | 컨테이너 오케스트레이션, 배포, 스케일링 | K8s, Nginx Ingress |

---

## 데이터 흐름

### 1. 그래프 실행 흐름

```
[사용자] → [그래프 에디터]
              ↓
    그래프 정의 생성 (nodes, edges)
              ↓
    POST /api/v1/graphs/run-graph
              ↓
    [Backend Graph Runner]
              ↓
    ┌─────────────────────┐
    │ 1. 그래프 검증       │
    │ 2. 실행 가능 그래프  │
    │    (Runnable) 빌드  │
    │ 3. 상태 초기화       │
    └──────────┬──────────┘
               ↓
    ┌──────────────────────────────────┐
    │   노드별 순차/병렬 실행           │
    │   ┌─────────────────────────┐   │
    │   │ InputNode               │   │
    │   │  → state 초기화         │   │
    │   └────────┬────────────────┘   │
    │            ↓                     │
    │   ┌─────────────────────────┐   │
    │   │ RetrievalNode           │   │
    │   │  → 벡터 검색 (Chroma)   │   │
    │   │  → 컨텍스트 추가        │   │
    │   └────────┬────────────────┘   │
    │            ↓                     │
    │   ┌─────────────────────────┐   │
    │   │ PromptNode              │   │
    │   │  → LLM 호출 (OpenAI)    │   │
    │   │  → 응답 생성            │   │
    │   └────────┬────────────────┘   │
    │            ↓                     │
    │   ┌─────────────────────────┐   │
    │   │ ConditionNode           │   │
    │   │  → 조건 평가            │   │
    │   │  → 다음 경로 결정       │   │
    │   └────────┬────────────────┘   │
    │            ↓                     │
    │   ┌─────────────────────────┐   │
    │   │ OutputNode              │   │
    │   │  → 최종 결과 포맷팅     │   │
    │   └─────────────────────────┘   │
    └──────────────┬───────────────────┘
                   ↓
    ┌──────────────────────────────┐
    │ 실행 결과 반환               │
    │ - final_state (전체 상태)   │
    │ - node_results (노드별 결과)│
    │ - execution_history         │
    └──────────┬───────────────────┘
               ↓
    [Frontend] 결과 시각화
               ↓
    [사용자] 결과 확인
```

### 2. 지식 관리(RAG) 흐름

```
[사용자] → [지식 관리 UI]
              ↓
    1. 컬렉션 생성
       POST /api/v1/collections
              ↓
       [PostgreSQL] 컬렉션 메타데이터 저장
       [ChromaDB] 컬렉션 생성
              ↓
    2. 문서 업로드
       POST /api/v1/documents (multipart/form-data)
              ↓
       [Backend Document Service]
              ↓
       ┌───────────────────────────────┐
       │ 파일 수신 및 텍스트 추출       │
       │  - PDF → PyPDF                │
       │  - TXT → 직접 읽기            │
       └────────┬──────────────────────┘
                ↓
       ┌───────────────────────────────┐
       │ 청킹 전략 선택 및 실행         │
       │  - Length: 고정 길이 분할     │
       │  - Semantic: 의미 기반 분할   │
       │  - Hybrid: 길이+의미 혼합     │
       │  - Paragraph: 문단 기반       │
       └────────┬──────────────────────┘
                ↓
       ┌───────────────────────────────┐
       │ 임베딩 생성                   │
       │  OpenAI text-embedding-3-small│
       └────────┬──────────────────────┘
                ↓
       ┌───────────────────────────────┐
       │ 저장                          │
       │  [PostgreSQL] 문서/청크 메타  │
       │  [ChromaDB] 벡터 + 텍스트     │
       └───────────────────────────────┘
              ↓
    3. 검색 (RetrievalNode 실행 시)
       query = "사용자 질문"
              ↓
       [Vector Store Utils]
              ↓
       query_embedding = embed(query)
              ↓
       [ChromaDB] 유사도 검색
              ↓
       상위 K개 청크 반환
              ↓
       [PromptNode] 컨텍스트로 활용
              ↓
       [LLM] 답변 생성
```

### 3. Agent 관리 흐름

```
[사용자] → [Agent 관리 UI]
              ↓
    1. 그래프 저장
       POST /api/v1/graphs
       {
         name, description, version,
         nodes: [...],
         edges: [...]
       }
              ↓
       [Backend Graph Service]
              ↓
       [PostgreSQL] 트랜잭션
       - graphs 테이블에 그래프 메타 저장
       - nodes 테이블에 각 노드 저장
       - edges 테이블에 각 엣지 저장
              ↓
    2. 그래프 조회/검색
       GET /api/v1/graphs?name=xxx&sort=updated_at:desc
              ↓
       [PostgreSQL] 필터링 + 정렬 + 페이징
              ↓
       [Frontend] 목록 표시
              ↓
    3. 그래프 불러오기
       GET /api/v1/graphs/{id}
              ↓
       [Backend] 그래프 + 노드 + 엣지 조회
              ↓
       [Frontend] 그래프 에디터에 렌더링
              ↓
    4. 그래프 수정
       PUT /api/v1/graphs/{id}
              ↓
       [Backend] 기존 노드/엣지 삭제 후 재생성
              ↓
       [PostgreSQL] 업데이트
```

---

## 기술 스택 상세

### Frontend
- **Framework**: Next.js 15 (App Router)
- **UI Library**: React 19
- **그래프 시각화**: React Flow
- **스타일링**: TailwindCSS
- **UI 컴포넌트**: Radix UI, shadcn/ui
- **상태 관리**: React useState/useEffect
- **HTTP 클라이언트**: Axios

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0 (비동기)
- **마이그레이션**: Alembic
- **데이터 검증**: Pydantic v2
- **LLM 프레임워크**: LangChain, LangGraph
- **LLM Provider**: OpenAI (gpt-4o, gpt-4o-mini)
- **임베딩**: OpenAI text-embedding-3-small
- **서버**: Uvicorn (개발), Gunicorn (프로덕션)

### Database
- **관계형 DB**: PostgreSQL 14+
- **벡터 DB**: ChromaDB 1.1.0
- **연결**: asyncpg (비동기 PostgreSQL 드라이버)

### Infrastructure
- **컨테이너화**: Docker
- **오케스트레이션**: Kubernetes
- **Ingress**: Nginx Ingress Controller
- **로컬 개발**: Minikube

---

## 보안 고려사항

### 현재 구현
- ✅ CORS 설정 (Backend)
- ✅ Secret 관리 (Kubernetes Secrets)
- ✅ 환경 변수 분리 (ConfigMap)
- ✅ API 키 보호 (env 변수)

### 향후 개선 필요
- ⚠️ 사용자 인증 (JWT, OAuth2)
- ⚠️ API Rate Limiting
- ⚠️ 입력 검증 강화
- ⚠️ SQL Injection 방지 (ORM 사용으로 기본 보호)
- ⚠️ XSS 방지 (React 기본 보호)

---

## 성능 최적화

### 현재 최적화
- ✅ 비동기 DB 쿼리 (asyncpg)
- ✅ 연결 풀링 (SQLAlchemy)
- ✅ 벡터 인덱스 (ChromaDB HNSW)
- ✅ Next.js 정적 최적화

### 향후 개선
- ⚠️ Redis 캐싱 (그래프 조회, API 응답)
- ⚠️ CDN 활용 (정적 파일)
- ⚠️ 데이터베이스 인덱스 최적화
- ⚠️ 로드 밸런싱 (HPA)

---

## 모니터링 및 로깅

### 현재
- ✅ 애플리케이션 로그 (파일 기반)
- ✅ Request ID 추적
- ✅ 실행 시간 로깅

### 프로덕션 권장
- Prometheus + Grafana (메트릭)
- ELK Stack 또는 Loki (중앙 집중식 로깅)
- Sentry (에러 트래킹)
- Jaeger (분산 추적)

---

[← 메인 README로 돌아가기](../README.md)

