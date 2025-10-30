## AI Agent MVP

AI 에이전트(그래프 기반)와 RAG 문서 관리를 제공하는 풀스택 MVP입니다. FastAPI 백엔드, Next.js 프론트엔드, PostgreSQL, Chroma(Vector Store), Kubernetes 배포 구성을 포함합니다.

### 주요 기능
- 그래프 실행: 노드/엣지로 구성된 그래프 실행 및 단계별 결과 확인
- RAG 문서 관리: 문서 업로드/청크/색인 및 상세 조회
- 시각화 UI: 그래프 에디터, 그래프 관리, 지식 관리 화면 제공
- 운영 도구: Docker/K8s 매니페스트와 배포 스크립트 제공

### 기술 스택
- Backend: FastAPI, SQLAlchemy, Alembic, LangChain, LangGraph, ChromaDB, OpenAI SDK
- Frontend: Next.js 15, React 19, TailwindCSS, Radix UI, React Flow
- DB/스토리지: PostgreSQL, Chroma (로컬 경로 기반)
- DevOps: Docker, Kubernetes(Deployment/Service/Ingress), `k8s/deploy.sh`

### 디렉토리 구조(요약)
```
backend/           # FastAPI 서비스
frontend/          # Next.js 앱
k8s/               # Kubernetes 매니페스트 및 배포 스크립트
docker/            # Backend, Frontend container 빌드 스크립트
```

---

### 1) 프론트엔드 매뉴얼

#### 화면 구성과 사용법
- 그래프 에디터
  - 노드 추가/편집: 캔버스에서 노드 추가, 속성 편집, 엣지 연결
  - 스니핏/채팅: 채팅으로 질문 시 각 노드 실행 결과를 단계별로 확인
  - State 확인: 실행 중간/최종 `Graph State` 및 `노드 별 실행 결과`를 패널에서 확인
- 그래프 관리
  - 그래프 목록/검색/정렬, 단건 상세/수정/삭제
  - 버전 및 메타 정보 확인(작성자/수정자/시간)
- 지식 관리
  - 문서 업로드(멀티파트), 목록/필터/페이징
  - 청크 상세: `chunk_index`, `content`, 생성/수정 시간 확인

#### 노드의 역할과 I/O
- 입력 노드(Input): 사용자 질문, 시스템 설정 등 초기 컨텍스트 생성 (output: 초기 state)
- 프롬프트 노드(Prompt): 템플릿 기반 메시지 생성 및 LLM 호출 (input: state, output: 답변/중간 결과)
- 리트리벌 노드(Retrieval): 벡터 스토어에서 관련 컨텍스트 검색 (input: 질의, output: 컨텍스트 목록)
- 조건 노드(Condition): 분기/루프 등 조건 처리 (input: state, output: 분기된 흐름)
- 출력 노드(Output): 최종 응답/요약/구조화 결과 반환 (input: 최종 state)

입·출력은 그래프 상태(State)에 합류하며, 노드 간 연결(엣지)로 데이터가 전달됩니다.

#### To Do: 예정 기능
- 노드 추가: Merge Node, Web Search Node, Tool Node, MCP Node 등
- 지식관리 강화: Chunking 방법 추가(semantic, hybrid), Reranker, HyDE 등

---

### 2) 백엔드 사용 매뉴얼(개발자용)

#### 개요
- 앱 엔트리: `backend/app/main.py`
- API 베이스: `/api/v1`
- 공통: CORS 허용, 요청 로깅/Request-ID, 전역 예외 처리, 시작 시 테이블 생성

#### 엔드포인트(요약)
- 그래프 실행
  - `POST /api/v1/graphs/run-graph` — 요청 그래프(nodes/edges) 실행
- 그래프 관리
  - `GET /api/v1/graphs` — 목록/검색/정렬/페이징
  - `GET /api/v1/graphs/{id}` — 단건 조회
  - `POST /api/v1/graphs` — 생성 (옵션: `nodes`, `edges` 포함 가능)
  - `PUT /api/v1/graphs/{id}` — 수정 (그래프/노드/엣지 동시 갱신 가능)
  - `DELETE /api/v1/graphs/{id}` — 삭제
- 문서 관리
  - `GET /api/v1/documents` — 목록(필터: 이름/상태/페이지 등)
  - `GET /api/v1/documents/{id}` — 상세(청크 포함)
  - `POST /api/v1/documents` — 생성(멀티파트 또는 JSON)
  - `PUT /api/v1/documents/{id}` — 수정
  - `DELETE /api/v1/documents/{id}` — 삭제

#### 그래프 구조 개념
- 노드(Node): 입력/프롬프트/리트리벌/조건/출력 등 처리 단위를 정의
- 엣지(Edge): 노드 간 데이터 플로우(방향성) 정의
- 그래프 히스토리(Graph History): 실행 시점/입출력/결과를 기록하여 추적/디버깅에 활용

---

### 3) 개발

#### 사전 준비
- Node.js 20+ / npm 또는 pnpm
- Python 3.11+
- PostgreSQL (로컬 또는 컨테이너)

#### 환경 변수(요약)
- Frontend(`k8s/configmap.yaml` 참고)
  - `NEXT_PUBLIC_API_BASE_URL`(선택): 비우면 `window.location.origin + /api/v1`
  - `NODE_ENV`: production 권장
- Backend
  - `LOG_LEVEL`: error/warning/info/debug
  - `LOG_FILE_PATH`: "logs/app/app.log"
  - `DATABASE_URL`: "postgresql+asyncpg://DB_UESER:DB_PASSWORD@DB_IP:DB_PORT/DB_DATABASE"
  - `OPENAI_SECRET_KEY`: "YOUR_OPENAI_SECRET_KEY"
  - `VECTOR_STORE_DATA_DIR`: "app/data"
  - `ROOT_PATH`: ""
  - `OPENAPI_URL`:  "/openapi.json"
  - `DOCS_URL`:  "/docs"
  - `REDOC_URL`:  "/redoc"

#### 로컬 실행
- 백엔드
  ```
  cd backend
  uv sync -- frozen
  ./run.sh
  ```
  - 기본 포트: `8000` / Swagger 문서: `http://localhost:8000/docs`

- 프론트엔드
  ```
  cd frontend
  npm install
  npm run dev
  ```
  - 기본 포트: `3000`

---

### 4) 배포

#### Docker Build
  ```
  cd docker
  ./docker_build.sh
  ```

#### Kubernetes Deploy
- 요구사항: `kubernetes` 설치, `kubectl` 연결, Ingress 컨트롤러(NGINX 등)
- 배포 스크립트 사용
  ```
  cd k8s
  ./deploy.sh                   # ConfigMap/Secret/DB/BE/FE/Ingress 전체 배포
  ./deploy.sh --status          # 상태 확인
  ./deploy.sh --delete          # 삭제
  ./deploy.sh --backend-only    # 백엔드만
  ./deploy.sh --frontend-only   # 프론트엔드만
  ./deploy.sh -n production     # 네임스페이스 지정
  ```
- 포트포워딩 예시
  ```
  kubectl port-forward svc/ai-agent-backend-service 8000:8000 -n <NS>
  kubectl port-forward svc/ai-agent-frontend-service 3000:3000 -n <NS>
  kubectl port-forward svc/postgres-service 5432:5432 -n <NS>
  ```

---

### 문제 해결(트러블슈팅)
- 404/경로 이슈: 프록시/Ingress 뒤에서는 `ROOT_PATH=/api`에 맞춰 최종 경로가 `/api/v1`가 되도록 구성
- CORS 오류: 백엔드 `allow_origins`에 실제 프론트 호스트 추가
- 벡터 인덱스 권한: `VECTOR_STORE_DATA_DIR` 쓰기 가능 경로 확인
- DB 접속 실패: `DATABASE_URL` 호스트/포트/크리덴셜/Service 이름 확인

### 라이선스/문의
- 라이선스: 별도 파일이 없으면 내부용으로 사용
- 문의: 저장소 이슈 또는 팀 담당자에게 연락


