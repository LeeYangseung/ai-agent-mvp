# Backend - AI Agent MVP

FastAPI 기반의 AI Agent MVP 백엔드 서비스입니다. LangGraph를 활용한 그래프 실행 엔진과 RAG(Retrieval-Augmented Generation) 기능을 제공합니다.

## 📖 목차

- [프로젝트 구조](#-프로젝트-구조)
- [API 명세](#-api-명세)
- [그래프 실행 엔진](#-그래프-실행-엔진)
- [노드 구현 가이드](#-노드-구현-가이드)
- [개발 환경 설정](#-개발-환경-설정)
- [데이터베이스 마이그레이션](#-데이터베이스-마이그레이션)

---

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── api/                    # API 엔드포인트
│   │   └── v1/
│   │       ├── graph/          # 그래프 관련 API
│   │       │   ├── graph.py        # 그래프 CRUD + 실행
│   │       │   ├── node.py         # 노드 CRUD
│   │       │   ├── edge.py         # 엣지 CRUD
│   │       │   └── graph_history.py # 실행 이력
│   │       └── rag/            # RAG 관련 API
│   │           ├── collection.py   # 컬렉션 CRUD
│   │           ├── document.py     # 문서 업로드/관리
│   │           └── chunk.py        # 청크 조회
│   │
│   ├── core/                   # 핵심 기능
│   │   ├── config.py           # 환경 설정 (Pydantic Settings)
│   │   ├── db.py               # 데이터베이스 연결 (SQLAlchemy)
│   │   ├── deps.py             # 의존성 주입 (DB, LLM)
│   │   ├── exception.py        # 커스텀 예외 정의
│   │   ├── exception_handler.py # 전역 예외 핸들러
│   │   ├── graph_runner.py     # LangGraph 실행 엔진
│   │   └── logging.py          # 로깅 설정
│   │
│   ├── database/               # 데이터베이스 레이어
│   │   ├── models/             # SQLAlchemy ORM 모델
│   │   │   ├── base.py             # 공통 Base 클래스
│   │   │   ├── graph/              # 그래프 관련 모델
│   │   │   │   ├── graph.py
│   │   │   │   ├── node.py
│   │   │   │   ├── edge.py
│   │   │   │   └── graph_history.py
│   │   │   └── rag/                # RAG 관련 모델
│   │   │       ├── collection.py
│   │   │       ├── document.py
│   │   │       └── chunk.py
│   │   └── crud/               # CRUD 연산 (Create, Read, Update, Delete)
│   │       ├── graph/
│   │       └── rag/
│   │
│   ├── schemas/                # Pydantic 스키마 (요청/응답 검증)
│   │   ├── base.py             # 공통 스키마 (ResponseModel 등)
│   │   ├── enums.py            # Enum 정의 (NodeType, DocumentStatus 등)
│   │   ├── pagination.py       # 페이지네이션 스키마
│   │   ├── graph/
│   │   └── rag/
│   │
│   ├── services/               # 비즈니스 로직
│   │   ├── graph/              # 그래프 관련 서비스
│   │   │   ├── graph.py            # 그래프 생성/조회/수정/삭제
│   │   │   ├── node.py             # 노드 관리
│   │   │   ├── edge.py             # 엣지 관리
│   │   │   └── graph_history.py    # 실행 이력 저장
│   │   └── rag/                # RAG 관련 서비스
│   │       ├── collection.py       # 컬렉션 관리
│   │       ├── document.py         # 문서 업로드/청킹/임베딩
│   │       └── chunk.py            # 청크 조회
│   │
│   ├── nodes/                  # 노드 구현체
│   │   ├── base.py             # BaseNode 추상 클래스
│   │   ├── input_node.py       # 입력 노드
│   │   ├── prompt_node.py      # LLM 호출 노드
│   │   ├── retrieval_node.py   # 벡터 검색 노드
│   │   ├── condition_node.py   # 조건 분기 노드
│   │   ├── merge_node.py       # 상태 병합 노드
│   │   └── output_node.py      # 출력 노드
│   │
│   ├── utils/                  # 유틸리티 함수
│   │   ├── chunking.py         # 청킹 전략 구현
│   │   ├── vector_store.py     # ChromaDB 래퍼
│   │   └── common.py           # 공통 유틸리티
│   │
│   ├── data/                   # 데이터 저장소 (로컬 파일)
│   │   ├── doc/                # 업로드된 문서 원본
│   │   └── index/              # ChromaDB 벡터 인덱스
│   │
│   └── main.py                 # FastAPI 앱 엔트리포인트
│
├── alembic/                    # DB 마이그레이션
│   ├── versions/               # 마이그레이션 파일
│   └── env.py                  # Alembic 설정
│
├── conf/
│   └── gunicorn_conf.py        # Gunicorn 설정
│
├── pyproject.toml              # 프로젝트 메타데이터 및 의존성
├── uv.lock                     # 의존성 잠금 파일
├── alembic.ini                 # Alembic 설정 파일
├── run.sh                      # 로컬 실행 스크립트
└── Dockerfile                  # 컨테이너 이미지 빌드
```

### 디렉토리별 역할

| 디렉토리 | 역할 |
|---------|------|
| `api/` | HTTP 요청 처리, 요청/응답 검증, 라우팅 |
| `core/` | 애플리케이션 핵심 기능 (설정, DB, 예외, 그래프 실행) |
| `database/` | 데이터 영속성 레이어 (ORM 모델, CRUD) |
| `schemas/` | 데이터 검증 및 직렬화 (Pydantic) |
| `services/` | 비즈니스 로직 (API와 DB 사이의 중간 계층) |
| `nodes/` | LangGraph 노드 구현체 |
| `utils/` | 재사용 가능한 유틸리티 함수 |

---

## 📡 API 명세

### 베이스 URL

- 로컬 개발: `http://localhost:8000/api/v1`
- Kubernetes: `http://aiagent.local/api/v1`
- API 문서(Swagger): `/docs`
- API 문서(ReDoc): `/redoc`

### 공통 응답 형식

모든 API는 다음과 같은 형식으로 응답합니다:

```json
{
  "status": 200,
  "message": "성공 메시지",
  "data": { /* 응답 데이터 */ },
  "pagination": { /* 페이지네이션 정보 (목록 조회 시) */ }
}
```

### 에러 응답 형식

```json
{
  "status": 400,
  "message": "에러 메시지",
  "data": { /* 추가 에러 정보 */ }
}
```

---

### 1. 그래프 API

#### 1.1 그래프 실행

**POST** `/graphs/run-graph`

요청 그래프를 실행하고 결과를 반환합니다.

**Request Body:**
```json
{
  "nodes": [
    {
      "id": "input",
      "type": "InputNode",
      "params": {
        "input_key": "question"
      }
    },
    {
      "id": "prompt",
      "type": "PromptNode",
      "params": {
        "system_prompt": "당신은 도움이 되는 AI 비서입니다.",
        "user_prompt": "{question}",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "output_key": "answer"
      }
    },
    {
      "id": "output",
      "type": "OutputNode",
      "params": {
        "output_key": "answer"
      }
    }
  ],
  "edges": [
    {"source": "input", "target": "prompt"},
    {"source": "prompt", "target": "output"}
  ],
  "input": {
    "question": "안녕하세요. 오늘 날씨가 어떤가요?"
  }
}
```

**Response:**
```json
{
  "results": {
    "nodes": [
      {
        "node_id": "input",
        "type": "InputNode",
        "input": {"question": "안녕하세요. 오늘 날씨가 어떤가요?"},
        "output": {"question": "안녕하세요. 오늘 날씨가 어떤가요?"},
        "execution_time": 0.001
      },
      {
        "node_id": "prompt",
        "type": "PromptNode",
        "input": {"question": "안녕하세요. 오늘 날씨가 어떤가요?"},
        "output": {"answer": "죄송하지만 저는 실시간 날씨 정보에 접근할 수 없습니다..."},
        "execution_time": 1.234
      },
      {
        "node_id": "output",
        "type": "OutputNode",
        "input": {"answer": "죄송하지만..."},
        "output": "죄송하지만 저는 실시간 날씨 정보에 접근할 수 없습니다...",
        "execution_time": 0.001
      }
    ],
    "execution_order": ["input", "prompt", "output"],
    "total_time": 1.236
  },
  "final_state": {
    "question": "안녕하세요. 오늘 날씨가 어떤가요?",
    "answer": "죄송하지만 저는 실시간 날씨 정보에 접근할 수 없습니다..."
  }
}
```

#### 1.2 그래프 목록 조회

**GET** `/graphs`

저장된 그래프 목록을 조회합니다.

**Query Parameters:**
- `page` (int, default=0): 페이지 번호
- `size` (int, default=10): 페이지 크기
- `name` (str, optional): 그래프 이름 검색
- `description` (str, optional): 그래프 설명 검색
- `version` (int, optional): 버전 필터
- `sort` (str, default="created_at:desc"): 정렬 조건 (예: `name:asc,created_at:desc`)

**Response:**
```json
{
  "status": 200,
  "message": "그래프 목록 조회에 성공했습니다.",
  "pagination": {
    "page": 0,
    "size": 10,
    "total": 25,
    "total_pages": 3
  },
  "data": [
    {
      "id": "uuid-1234",
      "name": "회사 정책 Q&A",
      "description": "회사 정책 문서 기반 질의응답",
      "version": 2,
      "created_by": "admin",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_by": "admin",
      "updated_at": "2026-01-05T00:00:00Z"
    }
  ]
}
```

#### 1.3 그래프 상세 조회

**GET** `/graphs/{graph_id}`

특정 그래프의 상세 정보를 조회합니다 (노드 및 엣지 포함).

**Response:**
```json
{
  "status": 200,
  "message": "그래프 조회에 성공했습니다.",
  "data": {
    "id": "uuid-1234",
    "name": "회사 정책 Q&A",
    "description": "회사 정책 문서 기반 질의응답",
    "version": 2,
    "nodes": [
      {
        "id": "uuid-node-1",
        "node_id": "input",
        "type": "InputNode",
        "params": {"input_key": "question"},
        "order": 1
      },
      {
        "id": "uuid-node-2",
        "node_id": "retrieval",
        "type": "RetrievalNode",
        "params": {
          "collection_name": "company_policies",
          "query_key": "question",
          "top_k": 3
        },
        "order": 2
      }
    ],
    "edges": [
      {
        "id": "uuid-edge-1",
        "source": "input",
        "target": "retrieval"
      }
    ],
    "created_by": "admin",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_by": "admin",
    "updated_at": "2026-01-05T00:00:00Z"
  }
}
```

#### 1.4 그래프 생성

**POST** `/graphs`

새 그래프를 생성합니다 (노드 및 엣지 동시 생성 가능).

**Request Body:**
```json
{
  "name": "새 그래프",
  "description": "설명",
  "version": 1,
  "created_by": "admin",
  "updated_by": "admin",
  "nodes": [
    {
      "node_id": "input",
      "type": "InputNode",
      "params": {"input_key": "question"},
      "order": 1
    }
  ],
  "edges": [
    {
      "source": "input",
      "target": "output"
    }
  ]
}
```

**Response:**
```json
{
  "status": 201,
  "message": "그래프 생성에 성공했습니다.",
  "data": {
    "id": "uuid-new",
    "name": "새 그래프",
    "version": 1
  }
}
```

#### 1.5 그래프 수정

**PUT** `/graphs/{graph_id}`

기존 그래프를 수정합니다. 노드 및 엣지도 함께 갱신할 수 있습니다.

**Request Body:**
```json
{
  "name": "수정된 그래프 이름",
  "description": "수정된 설명",
  "updated_by": "admin",
  "nodes": [ /* 전체 노드 목록 */ ],
  "edges": [ /* 전체 엣지 목록 */ ]
}
```

**Response:**
```json
{
  "status": 200,
  "message": "그래프 수정에 성공했습니다.",
  "data": {
    "id": "uuid-1234",
    "version": 3
  }
}
```

#### 1.6 그래프 삭제

**DELETE** `/graphs/{graph_id}`

그래프 및 관련된 모든 노드와 엣지를 삭제합니다.

**Request Body:**
```json
{
  "updated_by": "admin"
}
```

**Response:**
```json
{
  "status": 200,
  "message": "그래프 삭제에 성공했습니다."
}
```

---

### 2. 노드 API

#### 2.1 노드 목록 조회

**GET** `/nodes`

**Query Parameters:**
- `page`, `size`: 페이지네이션
- `node_uuid` (UUID): 노드 UUID 필터
- `graph_id` (UUID): 그래프 ID 필터
- `node_id` (str): 노드 ID 검색 (예: "input", "retrieval")
- `type` (str): 노드 타입 필터 (예: "InputNode")
- `order` (int): 실행 순서 필터

#### 2.2 노드 상세 조회

**GET** `/nodes/{node_uuid}`

#### 2.3 노드 생성

**POST** `/nodes`

#### 2.4 노드 수정

**PUT** `/nodes/{node_uuid}`

#### 2.5 노드 삭제

**DELETE** `/nodes/{node_uuid}`

---

### 3. 엣지 API

#### 3.1 엣지 목록 조회

**GET** `/edges`

**Query Parameters:**
- `edge_id`, `graph_id`, `source`, `target`

#### 3.2 엣지 상세 조회

**GET** `/edges/{edge_id}`

#### 3.3 엣지 생성

**POST** `/edges`

#### 3.4 엣지 수정

**PUT** `/edges/{edge_id}`

#### 3.5 엣지 삭제

**DELETE** `/edges/{edge_id}`

---

### 4. 컬렉션 API

#### 4.1 컬렉션 목록 조회

**GET** `/collections`

**Query Parameters:**
- `page`, `size`: 페이지네이션
- `collection_id` (UUID): 컬렉션 ID 필터
- `collection_name` (str): 컬렉션 이름 검색
- `sort` (str): 정렬 조건

**Response:**
```json
{
  "status": 200,
  "message": "컬렉션 목록 조회에 성공했습니다.",
  "data": [
    {
      "id": "uuid-coll-1",
      "name": "company_policies",
      "description": "회사 정책 문서",
      "document_count": 15,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

#### 4.2 컬렉션 상세 조회

**GET** `/collections/{collection_id}`

#### 4.3 컬렉션 생성

**POST** `/collections`

**Request Body:**
```json
{
  "name": "new_collection",
  "description": "설명",
  "created_by": "admin",
  "updated_by": "admin"
}
```

#### 4.4 컬렉션 수정

**PUT** `/collections/{collection_id}`

#### 4.5 컬렉션 삭제

**DELETE** `/collections/{collection_id}`

**주의**: 컬렉션에 문서가 있으면 삭제가 거부됩니다.

---

### 5. 문서 API

#### 5.1 문서 목록 조회

**GET** `/documents`

**Query Parameters:**
- `page`, `size`: 페이지네이션
- `document_id` (UUID): 문서 ID 필터
- `collection_id` (UUID): 컬렉션 ID 필터
- `collection_name` (str): 컬렉션 이름 검색
- `chunk_id` (UUID): 청크 ID 필터
- `document_name` (str): 문서 이름 검색
- `chunk_content` (str): 청크 내용 검색
- `path` (str): 문서 경로 필터
- `status` (enum): 문서 상태 필터 (`pending`, `processing`, `completed`, `failed`)
- `sort` (str): 정렬 조건

#### 5.2 문서 상세 조회

**GET** `/documents/{document_id}`

문서 정보와 모든 청크를 반환합니다.

**Response:**
```json
{
  "status": 200,
  "message": "문서 조회에 성공했습니다.",
  "data": {
    "id": "uuid-doc-1",
    "name": "policy_2026.pdf",
    "path": "/app/data/doc/policy_2026.pdf",
    "status": "completed",
    "method": "paragraph",
    "collection": {
      "id": "uuid-coll-1",
      "name": "company_policies"
    },
    "chunks": [
      {
        "id": "uuid-chunk-1",
        "chunk_index": 0,
        "content": "제1조 목적...",
        "created_at": "2026-01-01T00:00:00Z"
      },
      {
        "id": "uuid-chunk-2",
        "chunk_index": 1,
        "content": "제2조 적용 범위...",
        "created_at": "2026-01-01T00:00:00Z"
      }
    ],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  }
}
```

#### 5.3 문서 업로드

**POST** `/documents`

**Content-Type**: `multipart/form-data`

**Form Fields:**
- `file` (File, 필수): 업로드할 파일 (PDF, TXT)
- `collection_id` (UUID, 필수): 컬렉션 ID
- `method` (enum, 필수): 청킹 방법 (`length`, `semantic`, `hybrid`, `paragraph`)
- `chunk_size` (int, optional): 청킹 사이즈 (기본값: 500, method=length/hybrid 시 사용)
- `overlap_size` (int, optional): 오버랩 사이즈 (기본값: 100)
- `breakpoint_threshold_type` (enum, optional): 임계값 유형 (method=semantic/hybrid 시 사용)
  - `percentile` (기본값)
  - `standard_deviation`
  - `interquartile`
- `created_by` (str, 필수): 작성자
- `updated_by` (str, 필수): 수정자

**Response:**
```json
{
  "status": 201,
  "message": "문서 생성에 성공했습니다.",
  "data": {
    "id": "uuid-new-doc",
    "name": "uploaded_file.pdf",
    "status": "completed",
    "chunk_count": 25
  }
}
```

**프로세스:**
1. 파일 수신 및 로컬 저장 (`app/data/doc/`)
2. 텍스트 추출 (PDF → PyPDF)
3. 선택된 방법으로 청킹
4. OpenAI `text-embedding-3-small`로 임베딩 생성
5. PostgreSQL에 문서/청크 메타데이터 저장
6. ChromaDB에 벡터 + 텍스트 저장

#### 5.4 문서 수정

**PUT** `/documents/{document_id}`

문서 메타데이터만 수정 가능 (파일 자체는 재업로드 필요).

#### 5.5 문서 삭제

**DELETE** `/documents/{document_id}`

PostgreSQL 및 ChromaDB에서 문서와 모든 청크를 삭제합니다.

**Request Body:**
```json
{
  "updated_by": "admin"
}
```

---

### 6. 청크 API

#### 6.1 청크 목록 조회

**GET** `/chunks`

**Query Parameters:**
- `chunk_id`, `document_id`, `chunk_index`, `content`

#### 6.2 청크 상세 조회

**GET** `/chunks/{chunk_id}`

---

### 7. 그래프 히스토리 API

#### 7.1 실행 이력 목록 조회

**GET** `/graph-histories`

**Query Parameters:**
- `graph_history_id`, `graph_id`, `status`

그래프 실행 이력을 조회합니다 (향후 구현 예정).

---

## 🚀 그래프 실행 엔진

### 개요

`app/core/graph_runner.py`에 구현된 그래프 실행 엔진은 LangGraph를 기반으로 노드와 엣지로 구성된 워크플로우를 실행합니다.

### 실행 프로세스

```
1. 그래프 정의 수신 (nodes, edges, input)
       ↓
2. 노드 검증 및 인스턴스화
   - 각 노드의 타입에 따라 app/nodes/의 클래스를 동적으로 로드
   - 노드 파라미터 검증
       ↓
3. StateGraph 빌드
   - LangGraph의 StateGraph 객체 생성
   - 각 노드를 StateGraph에 추가
   - 엣지를 연결하여 실행 경로 정의
       ↓
4. Runnable 컴파일
   - StateGraph.compile()로 실행 가능한 객체 생성
       ↓
5. 초기 상태 설정
   - input 파라미터를 state 딕셔너리로 변환
       ↓
6. 그래프 실행
   - runnable.invoke(state)로 실행
   - 각 노드가 순차적/병렬로 실행되며 state 업데이트
       ↓
7. 결과 수집
   - 각 노드의 입출력 및 실행 시간 기록
   - 최종 state 반환
       ↓
8. 구조화된 결과 반환
   - node_results: 노드별 실행 결과
   - final_state: 최종 상태
   - execution_order: 실행 순서
```

### 주요 함수

#### `run_graph(graph_def: dict, llm) -> dict`

**Parameters:**
- `graph_def`: 그래프 정의 (nodes, edges, input)
- `llm`: OpenAI LLM 인스턴스

**Returns:**
```python
{
    "structured_results": {
        "nodes": [
            {
                "node_id": "input",
                "type": "InputNode",
                "input": {...},
                "output": {...},
                "execution_time": 0.001
            },
            ...
        ],
        "execution_order": ["input", "retrieval", "prompt", "output"],
        "total_time": 2.345
    },
    "final_state": {
        "question": "...",
        "context": "...",
        "answer": "..."
    }
}
```

### State 관리

LangGraph의 상태(State)는 전체 그래프 실행 과정에서 공유되는 딕셔너리입니다:

- **초기화**: InputNode가 input 값을 state에 추가
- **누적**: 각 노드가 state를 읽고 새로운 키-값을 추가
- **전달**: 엣지를 따라 다음 노드로 전달
- **최종**: OutputNode에서 최종 결과 추출

**예시:**
```python
# 초기 state (InputNode 실행 후)
{
    "question": "회사 정책은?"
}

# RetrievalNode 실행 후
{
    "question": "회사 정책은?",
    "context": "제1조 목적...\n제2조 적용 범위..."
}

# PromptNode 실행 후
{
    "question": "회사 정책은?",
    "context": "제1조 목적...",
    "answer": "회사 정책에 따르면..."
}

# OutputNode 실행 후 (최종 state)
{
    "question": "회사 정책은?",
    "context": "제1조 목적...",
    "answer": "회사 정책에 따르면...",
    "output": "회사 정책에 따르면..."
}
```

---

## 🧩 노드 구현 가이드

### BaseNode 구조

모든 노드는 `app/nodes/base.py`의 `BaseNode` 추상 클래스를 상속합니다.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseNode(ABC):
    def __init__(self, node_id: str, params: Dict[str, Any] = None, llm=None):
        self.node_id = node_id
        self.params = params or {}
        self.llm = llm
    
    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        노드의 핵심 로직을 구현합니다.
        
        Args:
            state: 현재 그래프 상태 딕셔너리
        
        Returns:
            업데이트된 state 딕셔너리
        """
        pass
```

### 기존 노드 설명

#### 1. InputNode

**역할**: 워크플로우 시작점, 초기 입력값을 state에 설정

**파라미터:**
- `input_key` (str, default="input"): 입력값이 저장될 state 키

**구현 위치**: `app/nodes/input_node.py`

**실행 예시:**
```python
# params = {"input_key": "question"}
# input = {"question": "안녕하세요"}
# 실행 후 state = {"question": "안녕하세요"}
```

#### 2. PromptNode

**역할**: LLM 호출 및 응답 생성

**파라미터:**
- `system_prompt` (str): 시스템 프롬프트 (템플릿 지원)
- `user_prompt` (str): 사용자 프롬프트 (템플릿 지원)
- `model` (str, default="gpt-4o-mini"): 사용할 LLM 모델
- `temperature` (float, default=0.7): 생성 다양성
- `output_key` (str, default="output"): 응답이 저장될 state 키

**템플릿 변수**: `{variable_name}` 형식으로 state 값 참조

**구현 위치**: `app/nodes/prompt_node.py`

**실행 예시:**
```python
# state = {"question": "파이썬이란?", "context": "파이썬은 프로그래밍 언어입니다."}
# params = {
#     "system_prompt": "당신은 전문가입니다.",
#     "user_prompt": "질문: {question}\n컨텍스트: {context}",
#     "model": "gpt-4o-mini",
#     "temperature": 0.3,
#     "output_key": "answer"
# }
# 실행 후 state["answer"] = "파이썬은 고수준 프로그래밍 언어로..."
```

#### 3. RetrievalNode

**역할**: ChromaDB 벡터 검색

**파라미터:**
- `collection_name` (str, 필수): 검색할 컬렉션 이름
- `query_key` (str, default="input"): 검색 질의가 있는 state 키
- `output_key` (str, default="context"): 검색 결과가 저장될 state 키
- `top_k` (int, default=5): 반환할 최대 문서 개수

**구현 위치**: `app/nodes/retrieval_node.py`

**실행 예시:**
```python
# state = {"question": "연차 휴가는?"}
# params = {
#     "collection_name": "company_policies",
#     "query_key": "question",
#     "output_key": "context",
#     "top_k": 3
# }
# 실행 후 state["context"] = "제10조 연차 휴가...\n제11조..."
```

#### 4. ConditionNode

**역할**: 조건에 따라 다음 실행 경로 결정

**파라미터:**
- `condition_type` (enum): 조건 유형
  - `equals`: 값이 같은지
  - `contains`: 문자열 포함 여부
  - `greater_than`: 숫자 크기 비교 (>)
  - `less_than`: 숫자 크기 비교 (<)
  - `exists`: 키 존재 여부
- `check_key` (str): 검사할 state 키
- `condition_value` (Any): 비교 기준값
- `true_next` (str): 조건 참일 때 다음 노드 ID
- `false_next` (str): 조건 거짓일 때 다음 노드 ID

**구현 위치**: `app/nodes/condition_node.py`

**실행 예시:**
```python
# state = {"score": 85}
# params = {
#     "condition_type": "greater_than",
#     "check_key": "score",
#     "condition_value": 80,
#     "true_next": "high_score_handler",
#     "false_next": "low_score_handler"
# }
# 실행 후 다음 노드는 "high_score_handler"
```

#### 5. MergeNode

**역할**: 여러 병렬 경로의 state를 하나로 병합

**파라미터:**
- `merge_strategy` (enum, default="merge"): 병합 전략
  - `merge`: 딕셔너리 병합 (중복 키는 나중 값으로 덮어씀)
  - `replace`: 첫 번째 state만 사용
  - `append`: 리스트 값을 이어붙임
- `merge_keys` (list, optional): 병합할 키 목록 (지정하지 않으면 모든 키)

**구현 위치**: `app/nodes/merge_node.py`

#### 6. OutputNode

**역할**: 최종 결과 포맷팅 및 워크플로우 종료

**파라미터:**
- `output_key` (str, default="output"): 최종 출력으로 사용할 state 키
- `format` (enum, default="text"): 출력 포맷
  - `text`: 텍스트 그대로
  - `json`: JSON 직렬화
  - `markdown`: Markdown 포맷

**구현 위치**: `app/nodes/output_node.py`

**실행 예시:**
```python
# state = {"answer": "결과 텍스트"}
# params = {"output_key": "answer", "format": "text"}
# 실행 후 state["output"] = "결과 텍스트"
```

### 새 노드 추가하기

새로운 노드를 추가하려면:

1. **노드 클래스 작성** (`app/nodes/my_custom_node.py`):

```python
from app.nodes.base import BaseNode
from typing import Dict, Any

class MyCustomNode(BaseNode):
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # 파라미터 읽기
        input_key = self.params.get("input_key", "input")
        output_key = self.params.get("output_key", "output")
        
        # 입력값 가져오기
        input_value = state.get(input_key)
        
        # 커스텀 로직 수행
        result = self.process(input_value)
        
        # state 업데이트
        state[output_key] = result
        return state
    
    def process(self, input_value: Any) -> Any:
        # 실제 처리 로직
        return f"Processed: {input_value}"
```

2. **Graph Runner에 등록** (`app/core/graph_runner.py`):

```python
from app.nodes.my_custom_node import MyCustomNode

NODE_CLASSES = {
    "InputNode": InputNode,
    "PromptNode": PromptNode,
    "RetrievalNode": RetrievalNode,
    "ConditionNode": ConditionNode,
    "MergeNode": MergeNode,
    "OutputNode": OutputNode,
    "MyCustomNode": MyCustomNode,  # 추가
}
```

3. **Frontend에 노드 타입 추가** (프론트엔드 README 참고)

---

## 💻 개발 환경 설정

### 사전 요구사항

- Python 3.11+
- PostgreSQL 14+
- `uv` (Python 패키지 관리자, 권장) 또는 `pip`

### 1. 의존성 설치

```bash
cd backend

# uv 사용 (권장)
uv sync --frozen

# 또는 pip 사용
pip install -e .
```

### 2. 환경 변수 설정

`.env` 파일 생성 또는 환경 변수 export:

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/ai_agent_db"
export OPENAI_SECRET_KEY="sk-your-openai-api-key"
export VECTOR_STORE_DATA_DIR="app/data"
export LOG_LEVEL="info"
export LOG_FILE_PATH="logs/app/app.log"
export ROOT_PATH=""
export OPENAPI_URL="/openapi.json"
export DOCS_URL="/docs"
export REDOC_URL="/redoc"
```

### 3. PostgreSQL 실행

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

### 4. 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
alembic upgrade head
```

### 5. 서버 실행

```bash
# 개발 서버 (uvicorn)
./run.sh

# 또는 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 `http://localhost:8000`에서 실행됩니다.

### 6. API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🗄️ 데이터베이스 마이그레이션

이 프로젝트는 Alembic을 사용하여 데이터베이스 스키마 변경을 관리합니다.

### 현재 마이그레이션

```
alembic/versions/
├── 9ae2062eaac7_create_graph_tables.py          # 그래프/노드/엣지 테이블
├── b0f91ee7f793_add_rag_models_document_and_chunk.py  # 문서/청크 테이블
├── c1d2e3f4a5b6_add_collection_table_and_document_fk.py  # 컬렉션 테이블
├── 683bc4c24582_add_chunking_methods_and_breakpoint_.py  # 청킹 메서드 필드
└── ba89c70aa082_alter_table.py                 # 기타 변경
```

### 마이그레이션 명령어

```bash
# 최신 마이그레이션 적용
alembic upgrade head

# 특정 버전으로 업그레이드
alembic upgrade <revision>

# 이전 버전으로 다운그레이드
alembic downgrade -1

# 마이그레이션 이력 확인
alembic history

# 현재 버전 확인
alembic current

# 새 마이그레이션 생성 (모델 변경 후)
alembic revision --autogenerate -m "변경 내용 설명"
```

### 새 마이그레이션 작성 예시

1. **ORM 모델 수정** (`app/database/models/`)

```python
# app/database/models/graph/graph.py
class Graph(Base):
    __tablename__ = "graphs"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    # 새 필드 추가
    tags = Column(JSON, default=list)
```

2. **마이그레이션 생성**

```bash
alembic revision --autogenerate -m "add tags field to graphs"
```

3. **마이그레이션 파일 확인** (`alembic/versions/xxx_add_tags_field_to_graphs.py`)

4. **마이그레이션 적용**

```bash
alembic upgrade head
```

---

## 🧪 테스트

> **참고**: 현재 테스트 코드가 포함되어 있지 않습니다. 향후 추가 예정입니다.

테스트 추가 시 권장 구조:

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures
│   ├── test_api/            # API 엔드포인트 테스트
│   ├── test_services/       # 서비스 레이어 테스트
│   ├── test_nodes/          # 노드 실행 테스트
│   └── test_utils/          # 유틸리티 함수 테스트
```

---

## 📦 의존성 관리

### 주요 의존성

| 패키지 | 버전 | 용도 |
|-------|------|------|
| `fastapi` | 0.115.6 | 웹 프레임워크 |
| `uvicorn` | latest | ASGI 서버 |
| `gunicorn` | 22.0.0 | 프로덕션 서버 |
| `sqlalchemy` | 2.0.31 | ORM |
| `asyncpg` | 0.30.0 | PostgreSQL 비동기 드라이버 |
| `alembic` | 1.13.2 | 데이터베이스 마이그레이션 |
| `pydantic` | 2.11.9 | 데이터 검증 |
| `openai` | 1.109.1 | OpenAI API 클라이언트 |
| `langchain` | 0.3+ | LLM 추상화 |
| `langgraph` | 1.0.5+ | 그래프 기반 워크플로우 |
| `chromadb` | 1.1.0 | 벡터 데이터베이스 |
| `pypdf` | 6.1.1 | PDF 파싱 |

### 의존성 추가

```bash
# pyproject.toml에 추가
[project]
dependencies = [
    "new-package>=1.0.0",
]

# uv로 설치
uv sync
```

---

## 🐛 디버깅

### 로그 확인

```bash
# 로컬 개발
tail -f logs/app/app.log

# Kubernetes
kubectl logs -f deployment/ai-agent-backend-deployment
```

### 로그 레벨 변경

```bash
export LOG_LEVEL="debug"  # error, warning, info, debug
```

### 일반적인 문제

#### 1. OpenAI API 키 오류

**증상**: `AuthenticationError: Invalid API key`

**해결**:
```bash
export OPENAI_SECRET_KEY="sk-your-valid-key"
```

#### 2. ChromaDB 권한 오류

**증상**: `PermissionError: [Errno 13] Permission denied`

**해결**:
```bash
chmod -R 777 app/data/index/
```

#### 3. DB 연결 실패

**증상**: `sqlalchemy.exc.OperationalError: could not connect to server`

**해결**:
```bash
# PostgreSQL이 실행 중인지 확인
docker ps | grep postgres

# DATABASE_URL 확인
echo $DATABASE_URL
```

---

## 🚀 프로덕션 배포

### Docker 이미지 빌드

```bash
cd docker
./docker_build.sh --backend-only
```

### Kubernetes 배포

자세한 내용은 [프로젝트 루트 README](../README.md)의 "배포" 섹션을 참고하세요.

---

## 📚 추가 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 문서](https://docs.sqlalchemy.org/)
- [LangChain 문서](https://python.langchain.com/)
- [LangGraph 튜토리얼](https://langchain-ai.github.io/langgraph/tutorials/)
- [ChromaDB 문서](https://docs.trychroma.com/)

---

**Happy Coding! 🎉**

