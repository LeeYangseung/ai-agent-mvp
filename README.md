# AI Agent MVP

> LangGraph 기반의 유연하고 확장 가능한 AI 에이전트 플랫폼

## 📖 목차

- [프로젝트 소개](#-프로젝트-소개)
- [시스템 아키텍처](#-시스템-아키텍처)
- [주요 기능](#-주요-기능)
- [빠른 시작](#-빠른-시작)
- [사용 가이드](#-사용-가이드)
- [개발자 문서](#-개발자-문서)

---

## 🎯 프로젝트 소개

AI Agent MVP는 **LangGraph**를 기반으로 구축된 그래프 기반 AI 에이전트 플랫폼입니다. 복잡한 AI 워크플로우를 시각적으로 설계하고 실행할 수 있으며, RAG(Retrieval-Augmented Generation) 기반의 지식 관리 시스템을 통합하여 문서 기반 질의응답을 지원합니다.

### 💡 LangGraph 철학

이 프로젝트는 LangGraph의 핵심 철학을 따릅니다:

- **그래프 기반 워크플로우**: AI 에이전트의 로직을 노드(Node)와 엣지(Edge)로 구성된 방향성 그래프로 표현합니다.
- **상태 관리(State Management)**: 각 노드는 공유 상태(State)를 읽고 수정하며, 이를 통해 컨텍스트가 전체 워크플로우에 걸쳐 유지됩니다.
- **유연한 제어 흐름**: 조건 분기, 루프, 병렬 처리 등 복잡한 제어 흐름을 그래프 구조로 자연스럽게 표현할 수 있습니다.
- **모듈화와 재사용성**: 각 노드는 독립적인 기능 단위로 설계되어, 다양한 그래프에서 재사용할 수 있습니다.
- **추적 가능성(Traceability)**: 모든 실행 과정과 상태 변화를 기록하여 디버깅과 분석이 용이합니다.

### 🎨 설계 원칙

1. **시각적 직관성**: 드래그 앤 드롭 방식의 그래프 에디터로 누구나 쉽게 AI 워크플로우를 설계할 수 있습니다.
2. **확장 가능성**: 새로운 노드 타입을 추가하여 기능을 확장할 수 있는 플러그인 아키텍처를 지향합니다.
3. **엔터프라이즈 레디**: 컬렉션 기반 문서 격리, 버전 관리, 감사 추적(Audit Trail) 등 프로덕션 환경에 필요한 기능을 제공합니다.

---

## 🏗️ 시스템 아키텍처

### 전체 구조도

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
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Layer (v1)                        │   │
│  │  /graphs  /documents  /collections  /chunks              │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                             │
│  ┌────────────────▼─────────────────────────────────────────┐   │
│  │              Service Layer                               │   │
│  │  - Graph Service      - Document Service                 │   │
│  │  - Node Service       - Collection Service               │   │
│  │  - Edge Service       - Chunk Service                    │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                             │
│  ┌────────────────▼─────────────────┐  ┌───────────────────┐    │
│  │       Graph Runner               │  │  Chunking Utils   │    │
│  │   (LangGraph Executor)           │  │  - Length         │    │
│  │                                  │  │  - Semantic       │    │
│  │  ┌────────────────────────────┐  │  │  - Hybrid         │    │
│  │  │  Node Implementations      │  │  │  - Paragraph      │    │
│  │  │  - InputNode               │  │  └───────────────────┘    │
│  │  │  - PromptNode              │  │                           │
│  │  │  - RetrievalNode           │  │  ┌───────────────────┐    │
│  │  │  - ConditionNode           │  │  │  Vector Store     │    │
│  │  │  - MergeNode               │  │  │   Utils (Chroma)  │    │
│  │  │  - OutputNode              │  │  └───────────────────┘    │
│  │  └────────────────────────────┘  │                           │
│  └──────────────────────────────────┘                           │
└───────────────────┬──────────────────────┬──────────────────────┘
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

### 데이터 흐름

#### 1️⃣ 그래프 실행 흐름

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
    │ 1. 그래프 검증         │
    │ 2. 실행 가능 그래프     │
    │    (Runnable) 빌드   │
    │ 3. 상태 초기화         │
    └──────────┬──────────┘
               ↓
    ┌──────────────────────────────────┐
    │   노드별 순차/병렬 실행               │
    │   ┌─────────────────────────┐    │
    │   │ InputNode               │    │
    │   │  → state 초기화           │    │
    │   └────────┬────────────────┘    │
    │            ↓                     │
    │   ┌─────────────────────────┐    │
    │   │ RetrievalNode           │    │
    │   │  → 벡터 검색 (Chroma)     │    │
    │   │  → 컨텍스트 추가           │    │
    │   └────────┬────────────────┘    │
    │            ↓                     │
    │   ┌─────────────────────────┐    │
    │   │ PromptNode              │    │
    │   │  → LLM 호출 (OpenAI)     │    │
    │   │  → 응답 생성              │    │
    │   └────────┬────────────────┘    │
    │            ↓                     │
    │   ┌─────────────────────────┐    │
    │   │ ConditionNode           │    │
    │   │  → 조건 평가              │    │
    │   │  → 다음 경로 결정          │    │
    │   └────────┬────────────────┘    │
    │            ↓                     │
    │   ┌─────────────────────────┐    │
    │   │ OutputNode              │    │
    │   │  → 최종 결과 포맷팅         │    │
    │   └─────────────────────────┘    │
    └──────────────┬───────────────────┘
                   ↓
    ┌──────────────────────────────┐
    │ 실행 결과 반환                  │
    │ - final_state (전체 상태)      │
    │ - node_results (노드별 결과)    │
    │ - execution_history          │
    └──────────┬───────────────────┘
               ↓
    [Frontend] 결과 시각화
               ↓
    [사용자] 결과 확인
```

#### 2️⃣ 지식 관리(RAG) 흐름

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
       │ 파일 수신 및 텍스트 추출            │
       │  - PDF → PyPDF                │
       │  - TXT → 직접 읽기              │
       └────────┬──────────────────────┘
                ↓
       ┌───────────────────────────────┐
       │ 청킹 전략 선택 및 실행             │
       │  - Length: 고정 길이 분할        │
       │  - Semantic: 의미 기반 분할      │
       │  - Hybrid: 길이+의미 혼합        │
       │  - Paragraph: 문단 기반         │
       └────────┬──────────────────────┘
                ↓
       ┌───────────────────────────────┐
       │ 임베딩 생성                      │
       │  OpenAI text-embedding-3-small│
       └────────┬──────────────────────┘
                ↓
       ┌───────────────────────────────┐
       │ 저장                           │
       │  [PostgreSQL] 문서/청크 메타     │
       │  [ChromaDB] 벡터 + 텍스트        │
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

#### 3️⃣ Agent 관리 흐름

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

### 컴포넌트 역할

| 컴포넌트 | 역할 | 주요 기술 |
|--------|-----|---------|
| **Frontend** | 사용자 인터페이스 제공, 그래프 시각화 | Next.js 15, React 19, React Flow, TailwindCSS |
| **Backend** | 비즈니스 로직, API 제공, 그래프 실행 | FastAPI, LangChain, LangGraph, SQLAlchemy |
| **PostgreSQL** | 메타데이터 영속화 (그래프, 문서, 사용자 등) | PostgreSQL 14+ |
| **ChromaDB** | 벡터 임베딩 저장 및 유사도 검색 | Chroma 1.1.0 |
| **Kubernetes** | 컨테이너 오케스트레이션, 배포, 스케일링 | K8s, Nginx Ingress |

---

## ✨ 주요 기능

### 1. 그래프 에디터

드래그 앤 드롭 방식으로 AI 워크플로우를 시각적으로 설계할 수 있는 에디터입니다.

#### 지원 노드 타입

| 노드 타입 | 설명 | 입력 | 출력 |
|---------|-----|-----|-----|
| **InputNode** | 워크플로우 시작점, 초기 상태 설정 | 사용자 입력 (질문, 파라미터) | 초기화된 state |
| **PromptNode** | LLM 호출, 템플릿 기반 프롬프트 생성 | state (컨텍스트) | LLM 응답 추가된 state |
| **RetrievalNode** | 벡터 검색, 관련 문서 조회 | query, collection_name | 검색된 컨텍스트 추가된 state |
| **ConditionNode** | 조건 분기, 동적 경로 결정 | state | 다음 노드 ID (분기 경로) |
| **MergeNode** | 여러 경로 합류, 상태 병합 | 여러 state | 병합된 state |
| **OutputNode** | 워크플로우 종료점, 최종 결과 포맷팅 | state | 최종 응답 |

#### 노드 설정 상세

##### InputNode
- **역할**: 사용자의 질문이나 초기 파라미터를 받아 그래프 실행의 시작점 역할
- **설정 항목**:
  - `output`: input node의 출력이 저장될 state 키 (user_input으로 고정)

##### PromptNode
- **역할**: 템플릿 기반으로 프롬프트를 생성하고 LLM을 호출하여 응답 생성
- **설정 항목**:
  - `system_prompt`: 시스템 메시지 템플릿
  - `user_prompt`: 사용자 메시지 템플릿
  - `assistant_prompt`: 어시스턴트 메시지 템플릿(선택사항)
  - `inputs`: 노드 내에서 사용될 variables(고정값 또는 타 노드의 output 참조 가능)
  - `output`: 응답이 저장될 state 키

##### RetrievalNode
- **역할**: 지정된 컬렉션에서 벡터 유사도 검색을 수행하여 관련 문서 조회
- **설정 항목**:
  - `collection`: 검색할 컬렉션 이름 (필수)
  - `top_k`: 반환할 최대 문서 개수 (기본값: 4)
  - `inputs`: 노드 내에서 사용될 variables(고정값 또는 타 노드의 output 참조 가능, query는 필수)
  - `output`: 검색 결과가 저장될 state 키 (기본값: "context")
  

##### ConditionNode
- **역할**: state 값을 평가하여 다음 실행 경로를 결정 (if-else, 루프 구현 가능)
- **설정 항목**:
  - `evaluation_mode`: 분기 유형
    - `First Match`: 조건을 만족하는 첫 분기만 실행
    - `All Matches`: 조건을 만족하는 모든 분기를 병렬 실행(Fan-out)
  - `inputs`: 노드 내에서 사용될 variables(고정값 또는 타 노드의 output 참조 가능)
  - `conditions`: inputs에서 받은 값에 대해 특정 값과 비교해 True이면 match, 모든 값이 false이면 else 분기 실행
    - `operator`: 연산자
    - `target`: match시 분기할 타겟 노드
    - `value`: 비교할 값
    - `variable`: input으로 받은 variables 중 비교할 variable

##### MergeNode
- **역할**: 여러 병렬 실행 경로의 결과를 하나로 합침
- **설정 항목**:
  - `merge_strategy`: 병합 전략 (concat, list, dict)
  - `inputs`: 병합할 state 키 목록
  - `output`: 병합 결과가 저장될 state 키

##### OutputNode
- **역할**: 최종 결과를 포맷팅하고 워크플로우 종료
- **설정 항목**:
  - `inputs`: 노드 내에서 사용될 variables(고정값 또는 타 노드의 output 참조 가능)
  - `output`: 응답이 저장될 state 키(agent_output 고정)

#### 사용 방법

1. **노드 추가**: 좌측 노드 팔레트에서 노드를 드래그하여 캔버스에 배치
2. **노드 설정**: 노드를 클릭하여 우측 속성 패널에서 설정 편집
3. **엣지 연결**: 노드의 출력 핸들을 다음 노드의 입력 핸들로 드래그하여 연결
4. **그래프 저장**: 상단 "저장" 버튼으로 그래프를 데이터베이스에 저장
5. **실행 및 결과 확인**: 
   - 우측 Chat 패널에서 입력값을 넣고 "전송" 클릭
   - 그래프의 최종 출력 확인
   - 출력 하단 '노드별 입출력' 패널 확장해 노드별 수행 상태, 입력, 출력 확인
   - 출력 하단 '그래프 히스토리' 패널 확장해 그래프 수행 히스토리 확인
   - 출력 하단 '그래프 스테이트' 패널 확장해 그래프 State dict 확인

### 2. Agent 관리

저장된 그래프(Agent)를 관리하는 화면입니다.

#### 기능

- **목록 조회**: 모든 그래프를 카드 형태로 표시
- **검색**: 이름, 설명으로 그래프 검색
- **필터링**: 버전 필터
- **정렬**: 생성일, 수정일, 이름순 정렬
- **상세 보기**: 그래프 메타데이터 확인/수정
- **편집**: 그래프 에디터로 불러와 수정
- **삭제**: 그래프 및 관련 노드/엣지 삭제

### 3. 지식 관리 (RAG)

문서를 업로드하고 벡터 검색을 통해 AI가 답변할 수 있는 지식 베이스를 구축합니다.

#### 3.1 컬렉션 관리

컬렉션은 문서를 논리적으로 그룹화하여 검색 범위를 격리하는 단위입니다.

**사용 예시:**
- 프로젝트별 분리: `project_alpha`, `project_beta`
- 문서 타입별 분리: `contracts`, `manuals`, `policies`
- 사용자별 격리: `user_123`, `team_sales`

**기능:**
- 컬렉션 생성/수정/삭제
- 컬렉션별 문서 개수 확인
- 컬렉션 검색 및 정렬

**주의사항:**
- 문서가 포함된 컬렉션은 삭제 불가 (먼저 문서 삭제 필요)
- RetrievalNode에서 `collection_name` 파라미터로 검색 범위 지정

#### 3.2 문서 관리

**지원 파일 형식:**
- PDF (`.pdf`)
- 텍스트 (`.txt`, `.md`)

**문서 업로드 프로세스:**

1. **파일 선택 및 컬렉션 지정**
   - 멀티파일 업로드 지원
   - 업로드 시 컬렉션 필수 선택

2. **청킹 방법 선택**

   문서의 특성에 맞는 청킹 전략을 선택하세요:

   ##### Length (길이 기반) - 기본 권장
   
   - **동작 방식**: 고정된 문자 수로 문서를 균등 분할
   - **사용 시점**: 
     - 짧은 일반 텍스트 (뉴스, 블로그)
     - 빠른 처리가 필요한 경우
     - 문맥보다 속도가 중요한 경우
   - **설정값**:
     - `청킹 사이즈`: 각 청크의 최대 문자 수 (기본 500, 권장 300-1000)
     - `오버랩 사이즈`: 청크 간 중복 문자 수 (기본 100, 청킹 사이즈의 10-20% 권장)
   - **장점**: 빠른 처리, 예측 가능한 크기, API 비용 없음
   - **단점**: 문장/단락 중간에서 분할될 수 있음

   ##### Semantic (의미 기반)
   
   - **동작 방식**: 문장 단위로 임베딩을 생성하고 의미적 유사도가 크게 변하는 지점에서 분할
   - **사용 시점**:
     - 주제별 분리가 중요한 문서 (인터뷰, 대화 로그)
     - 자연스러운 주제 전환 지점에서 분할하고 싶을 때
     - 청크 크기보다 의미적 응집성이 중요한 경우
   - **설정값**:
     - `임계값 유형`: 분할 지점 결정 방식
       - **Percentile (백분위수)**: 거리 분포의 95%를 기준으로 분할 - 균형잡힌 청크 (기본 권장)
       - **Standard Deviation (표준편차)**: 평균 + 3σ 기준 - 명확한 주제 전환만 감지
       - **Interquartile (사분위수)**: IQR 기반 - 이상치에 강건, 안정적
   - **장점**: 의미적으로 응집력 있는 청크, 자연스러운 주제 단위
   - **단점**: 임베딩 API 비용, 처리 시간 증가, 청크 크기 불균등
   - **주의**: 긴 문서는 처리 시간이 매우 길어질 수 있음

   ##### Hybrid (하이브리드)
   
   - **동작 방식**: 
     1. 1단계: Length 방식으로 큰 청크 생성
     2. 2단계: 각 청크를 Semantic 방식으로 재분할
   - **사용 시점**:
     - 긴 문서를 의미 있는 단위로 분할하되 크기도 제어하고 싶을 때
     - 연구 논문, 기술 문서, 상세 보고서
   - **설정값**:
     - `청킹 사이즈`: 1단계 분할 크기 (기본 1000)
     - `오버랩 사이즈`: 1단계 오버랩 크기 (기본 100)
     - `임계값 유형`: 2단계 의미 분할 기준 (Semantic과 동일)
   - **장점**: 청크 크기 제어 + 의미적 응집성 확보
   - **단점**: 가장 긴 처리 시간, 높은 API 비용
   - **추천**: 긴 문서 (5000자 이상) 처리 시

   ##### Paragraph (문단 기반)
   
   - **동작 방식**: 문서 구조(헤더, 문단 구분자)를 기준으로 분할
     - Markdown: `#`, `##`, `###` 헤더 기준
     - HTML: `<h1>`, `<h2>`, `<h3>` 태그 기준
     - 일반 텍스트: `\n\n` (빈 줄) 기준
   - **사용 시점**:
     - 구조화된 문서 (위키, 매뉴얼, 정책 문서)
     - Markdown 또는 HTML 파일
     - 원래 문서 구조를 보존하고 싶을 때
   - **설정값**: 없음 (자동 감지)
   - **장점**: 원래 문서 구조 보존, 빠른 처리, API 비용 없음
   - **단점**: 구조화되지 않은 문서는 비효율적, 청크 크기 불균등
   - **추천**: 기술 문서, 정책 문서, Markdown 파일

   **청킹 방법 선택 가이드:**

   | 문서 특성 | 권장 방법 | 예시 |
   |---------|---------|------|
   | 짧은 일반 텍스트 (< 5000자) | Length | 뉴스 기사, 블로그 포스트 |
   | 긴 일반 텍스트 (> 5000자) | Hybrid | 연구 논문, 보고서 |
   | 주제 전환이 많은 문서 | Semantic | 인터뷰, 대화 로그 |
   | 구조화된 문서 | Paragraph | 위키, 매뉴얼, Markdown |
   | 빠른 프로토타입 | Length | 모든 문서 |

3. **임베딩 생성 및 저장**
   - OpenAI `text-embedding-3-small` 모델 사용
   - PostgreSQL: 문서 메타데이터 및 청크 텍스트 저장
   - ChromaDB: 벡터 임베딩 저장

4. **문서 조회**
   - 목록: 필터링 (컬렉션, 상태, 이름), 정렬, 페이징
   - 상세: 문서 정보 + 모든 청크 내역 확인
     - 청크별 인덱스 번호
     - 청크 내용
     - 생성/수정 시간

5. **문서 삭제**
   - PostgreSQL 및 ChromaDB에서 동시 삭제
   - 연관된 모든 청크도 삭제

#### 3.3 벡터 검색 동작 방식

RetrievalNode 실행 시:

1. 사용자 질의 → 임베딩 변환
2. ChromaDB에서 지정된 컬렉션 내 유사도 검색 (코사인 유사도)
3. 상위 K개 청크 반환
4. 청크 내용을 PromptNode의 컨텍스트로 전달
5. LLM이 컨텍스트 기반 답변 생성

---

## 🚀 빠른 시작

### 사전 요구사항

| 항목 | 버전 | 용도 |
|-----|------|------|
| Docker | 20.10+ | 컨테이너 빌드 |
| Minikube | 1.25+ | 로컬 Kubernetes 클러스터 (개발용) |
| kubectl | 1.25+ | Kubernetes 클러스터 관리 |
| OpenAI API Key | - | LLM 및 임베딩 API |

### 옵션 1: Minikube로 로컬 실행 (권장)

로컬 환경에서 전체 스택을 Kubernetes에 배포하여 테스트할 수 있습니다.

#### 1단계: Minikube 시작

```bash
cd k8s
./minikube.sh start
```

이 명령은 다음을 자동으로 수행합니다:
- Minikube 클러스터 시작
- Ingress addon 활성화
- Minikube Tunnel 실행 (백그라운드)

#### 2단계: Docker 이미지 빌드

```bash
cd ../docker
./docker_build.sh
```

이 스크립트는 Backend와 Frontend 이미지를 모두 빌드합니다.

#### 3단계: Minikube에 이미지 로드

```bash
cd ../k8s
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest
```

#### 4단계: Secret 설정

```bash
# secret.example.yaml을 참고하여 secret.yaml 생성
cp secret.example.yaml secret.yaml
vim secret.yaml  # OpenAI API 키 및 DB 크레덴셜 입력
```

`secret.yaml` 예시:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-agent-secret
type: Opaque
stringData:
  OPENAI_SECRET_KEY: "sk-your-openai-api-key-here"
  DB_USER: "postgres"
  DB_PASSWORD: "your-secure-password"
  DB_DATABASE: "ai_agent_db"
```

#### 5단계: 애플리케이션 배포

```bash
./deploy.sh
```

이 스크립트는 다음을 순차적으로 배포합니다:
- ConfigMap (환경 변수)
- Secret (민감 정보)
- PostgreSQL (Persistent Volume 포함)
- Backend (FastAPI)
- Frontend (Next.js)
- Ingress (Nginx)

#### 6단계: 접속 설정

```bash
# /etc/hosts 파일에 도메인 추가 (최초 1회만)
sudo sh -c 'echo "127.0.0.1 aiagent.local" >> /etc/hosts'
```

#### 7단계: 브라우저에서 접속

- **Frontend**: http://aiagent.local/
- **Backend API Docs**: http://aiagent.local/api/docs

#### 배포 상태 확인

```bash
./deploy.sh --status

# 또는 kubectl 직접 사용
kubectl get pods
kubectl get svc
kubectl get ingress
```

#### 로그 확인

```bash
# Backend 로그
kubectl logs -f deployment/ai-agent-backend-deployment

# Frontend 로그
kubectl logs -f deployment/ai-agent-frontend-deployment

# PostgreSQL 로그
kubectl logs -f deployment/postgres-deployment
```

#### Minikube 중지

```bash
# 데이터 보존하고 중지
./minikube.sh stop

# 완전 삭제 (모든 데이터 삭제)
./minikube.sh stop --delete
```

### 옵션 2: Docker Compose로 빠른 실행

> **참고**: 추후 제공 예정입니다.

### 옵션 3: 로컬 개발 환경 (Backend + Frontend 개별 실행)

개발 중 빠른 피드백을 위해 Backend와 Frontend를 각각 로컬에서 실행할 수 있습니다.

#### Backend 실행

```bash
cd backend

# Python 3.11+ 가상환경 (uv 사용 권장)
uv sync --frozen

# 환경 변수 설정
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/ai_agent_db" # 로컬에 별도 postgres 설치 필요
export OPENAI_SECRET_KEY="your-openai-api-key"
export VECTOR_STORE_DATA_DIR="app/data" # 또는 벡터db data가 저장될 경로
export LOG_LEVEL="info"

# 서버 실행
./run.sh
```

Backend는 `http://localhost:8000`에서 실행됩니다.

#### Frontend 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

Frontend는 `http://localhost:3000`에서 실행됩니다.

#### PostgreSQL 실행 (로컬)

```bash
# Docker로 PostgreSQL 실행
docker run -d \
  --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=ai_agent_db \
  -p 5432:5432 \
  postgres:14
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

## 👩‍💻 개발자 문서

프로젝트 구조 및 개발 관련 상세 문서는 각 디렉토리의 README를 참고하세요:

- **[Backend README](./backend/README.md)**: Backend 소스코드 구조, API 명세, 노드 구현 가이드
- **[Frontend README](./frontend/README.md)**: Frontend 소스코드 구조, 컴포넌트 설명, 개발 가이드
- **[Kubernetes README](./k8s/README.md)**: Kubernetes 배포 상세 가이드, 프로덕션 환경 설정

---

## 🔧 문제 해결

### 일반적인 문제

#### 1. Ingress 접속 불가

**증상**: `aiagent.local`로 접속되지 않음

**해결 방법**:
```bash
# Minikube Tunnel이 실행 중인지 확인
cd k8s
./minikube.sh status

# Tunnel이 중지되어 있으면 재시작
./minikube.sh tunnel

# /etc/hosts에 도메인이 추가되었는지 확인
cat /etc/hosts | grep aiagent.local
```

#### 2. Pod가 ImagePullBackOff 상태

**증상**: `kubectl get pods`에서 Pod가 `ImagePullBackOff` 상태

**원인**: Minikube가 로컬 이미지를 찾지 못함

**해결 방법**:
```bash
# 이미지를 Minikube에 로드
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest

# Pod 재시작
kubectl rollout restart deployment/ai-agent-backend-deployment
kubectl rollout restart deployment/ai-agent-frontend-deployment
```

#### 3. Backend API 호출 실패 (CORS 에러)

**원인**: Backend의 `allow_origins`에 Frontend URL이 없음

**해결 방법**:

`backend/app/main.py` 수정:
```python
origins = [
    "http://localhost:3000",
    "http://aiagent.local",  # 추가
    # ... 기타 도메인
]
```

#### 4. 벡터 검색이 작동하지 않음

**원인**: ChromaDB 데이터 디렉토리 권한 문제 또는 컬렉션 미생성

**해결 방법**:
```bash
# Backend Pod에 접속
kubectl exec -it deployment/ai-agent-backend-deployment -- /bin/bash

# 데이터 디렉토리 확인
ls -la /app/app/data/index/

# ChromaDB 로그 확인
kubectl logs deployment/ai-agent-backend-deployment | grep -i chroma
```

#### 5. OpenAI API 키 오류

**증상**: PromptNode 또는 Semantic Chunking 실행 시 API 키 에러

**해결 방법**:
```bash
# Secret 확인
kubectl get secret ai-agent-secret -o yaml

# Secret 재생성
vim k8s/secret.yaml  # OPENAI_SECRET_KEY 수정
kubectl apply -f k8s/secret.yaml

# Backend Pod 재시작
kubectl rollout restart deployment/ai-agent-backend-deployment
```

---

## 📚 추가 자료

- **LangChain 공식 문서**: https://docs.langchain.com/
- **LangGraph 공식 문서**: https://langchain-ai.github.io/langgraph/
- **FastAPI 공식 문서**: https://fastapi.tiangolo.com/
- **Next.js 공식 문서**: https://nextjs.org/docs
- **ChromaDB 공식 문서**: https://docs.trychroma.com/

---

## 🛣️ 로드맵

### v1.1 (다음 릴리스)
- [ ] Reranker 지원 (Cohere, Cross-Encoder)
- [ ] HyDE (Hypothetical Document Embeddings)

### v1.2
- [ ] Web Search Node (Google, Bing)
- [ ] Tool Node (함수 호출)
- [ ] MCP (Model Context Protocol) Node
- [ ] 그래프 버전 관리 및 복원
- [ ] 그래프 템플릿 마켓플레이스(스니핏)

### v2.0
- [ ] 멀티 에이전트 협업
- [ ] 실시간 스트리밍 응답
- [ ] 그래프 성능 모니터링 대시보드
- [ ] 커스텀 노드 플러그인 시스템

---

## 📄 라이선스

이 프로젝트는 내부용으로 사용됩니다. 별도의 오픈소스 라이선스는 적용되지 않습니다.

## 💬 문의

문제가 발생하거나 제안 사항이 있으면:
- GitHub Issues에 등록

---

**Happy Coding! 🎉**
