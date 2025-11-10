## AI Agent MVP

AI 에이전트(그래프 기반)와 RAG 문서 관리를 제공하는 풀스택 MVP입니다. FastAPI 백엔드, Next.js 프론트엔드, PostgreSQL, Chroma(Vector Store), Kubernetes 배포 구성을 포함합니다.

### 주요 기능
- 그래프 실행: 노드/엣지로 구성된 그래프 실행 및 단계별 결과 확인
- RAG 문서 관리: 컬렉션 기반 문서 업로드/청크/색인 및 상세 조회
- 컬렉션 관리: 문서를 논리적으로 그룹화하여 검색 범위 격리 및 관리
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
  - 컬렉션 관리: 컬렉션 생성/수정/삭제, 컬렉션별 문서 그룹화
  - 문서 업로드(멀티파트): 컬렉션 선택 후 문서 업로드, 목록/필터/페이징
  - 청킹 방법 선택: Length(길이 기반), Semantic(의미 기반), Hybrid(하이브리드), Paragraph(문단 기반)
  - 청크 상세: `chunk_index`, `content`, 생성/수정 시간 확인
  - 벡터 검색: 컬렉션별 독립적인 검색 범위 제공

#### 청킹 방법 사용 가이드
문서 생성 시 문서 특성에 맞는 청킹 방법을 선택할 수 있습니다:

1. **Length (길이 기반)** - 기본 권장
   - 고정된 문자 수로 문서를 분할
   - **사용 시점**: 짧은 일반 텍스트, 빠른 처리가 필요한 경우
   - **설정값**: 청킹 사이즈(기본 500), 오버랩 사이즈(기본 100)
   - **예시**: 뉴스 기사, 블로그 포스트, 짧은 보고서

2. **Semantic (의미 기반)**
   - 임베딩을 사용하여 의미적 유사도 기반으로 분할
   - **사용 시점**: 주제별 분리가 중요한 문서, 대화 데이터
   - **설정값**: 임계값 유형(Percentile/Standard Deviation/Interquartile)
   - **예시**: 인터뷰 기록, 대화 로그, 리포트
   - **주의**: 임베딩 API 호출로 인해 처리 시간이 길어질 수 있음

3. **Hybrid (하이브리드)**
   - 길이 기반 분할 후 의미 기반으로 재분할
   - **사용 시점**: 긴 문서를 의미 있는 단위로 분할하면서 크기도 제어
   - **설정값**: 청킹 사이즈(기본 1000), 오버랩 사이즈(기본 100), 임계값 유형
   - **예시**: 긴 연구 논문, 기술 문서, 상세 보고서

4. **Paragraph (문단 기반)**
   - Markdown/HTML 구조 또는 문단 구분자를 기준으로 분할
   - **사용 시점**: 구조화된 문서, 헤더가 있는 문서
   - **설정값**: 없음 (자동 감지)
   - **예시**: 위키 문서, 기술 매뉴얼, 정책 문서, Markdown 파일

**임계값 유형 설명** (Semantic/Hybrid 사용 시):
- **Percentile (백분위수)**: 의미 차이의 상위 95%를 기준으로 분할 - 균형잡힌 청크 생성 (기본 권장)
- **Standard Deviation (표준편차)**: 평균에서 3 표준편차 이상 벗어난 지점에서 분할 - 명확한 주제 전환 감지
- **Interquartile (사분위수)**: 사분위수 범위를 기준으로 분할 - 이상치에 강건하며 안정적인 청크 생성

#### 노드의 역할과 I/O
- 입력 노드(Input): 사용자 질문, 시스템 설정 등 초기 컨텍스트 생성 (output: 초기 state)
- 프롬프트 노드(Prompt): 템플릿 기반 메시지 생성 및 LLM 호출 (input: state, output: 답변/중간 결과)
- 리트리벌 노드(Retrieval): 지정된 컬렉션의 벡터 스토어에서 관련 컨텍스트 검색 (input: 질의 + 컬렉션명, output: 컨텍스트 목록)
- 조건 노드(Condition): 분기/루프 등 조건 처리 (input: state, output: 분기된 흐름)
- 출력 노드(Output): 최종 응답/요약/구조화 결과 반환 (input: 최종 state)

입·출력은 그래프 상태(State)에 합류하며, 노드 간 연결(엣지)로 데이터가 전달됩니다.

#### To Do: 예정 기능
- 노드 추가: Merge Node, Web Search Node, Tool Node, MCP Node 등
- 지식관리 강화: Reranker, HyDE, Query Expansion 등

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
- 컬렉션 관리
  - `GET /api/v1/collections` — 목록(필터: 이름, 페이징)
  - `GET /api/v1/collections/{id}` — 상세(문서 개수 포함)
  - `POST /api/v1/collections` — 생성
  - `PUT /api/v1/collections/{id}` — 수정
  - `DELETE /api/v1/collections/{id}` — 삭제 (문서가 없을 때만 가능)
- 문서 관리
  - `GET /api/v1/documents` — 목록(필터: 컬렉션ID/이름/상태/페이지 등)
  - `GET /api/v1/documents/{id}` — 상세(청크 포함)
  - `POST /api/v1/documents` — 생성(멀티파트, collection_id + 청킹 방법 선택)
  - `PUT /api/v1/documents/{id}` — 수정
  - `DELETE /api/v1/documents/{id}` — 삭제 (벡터 스토어에서도 삭제)

#### 청킹 방법 (Chunking Methods)

문서 업로드 시 다양한 청킹 전략을 선택할 수 있으며, 각 방법은 문서 특성에 따라 최적화되어 있습니다.

**1. Length-based Chunking (길이 기반)**
- **알고리즘**: `RecursiveCharacterTextSplitter` 사용
- **동작 방식**: 지정된 문자 수로 문서를 균등하게 분할하며, 구분자 우선순위(`\n\n` → `\n` → ` ` → `""`)에 따라 자연스러운 경계에서 분할 시도
- **파라미터**:
  - `chunk_size`: 각 청크의 최대 문자 수 (기본값: 500)
  - `overlap_size`: 청크 간 중복 문자 수 (기본값: 100) - 문맥 연속성 유지
- **장점**: 빠른 처리 속도, 예측 가능한 청크 크기, API 호출 비용 없음
- **단점**: 문맥을 고려하지 않아 문장/단락 중간에서 분할될 수 있음
- **추천 사용 사례**: 일반 텍스트, 뉴스 기사, 블로그 포스트, 빠른 프로토타이핑

**2. Semantic Chunking (의미 기반)**
- **알고리즘**: `SemanticChunker` + OpenAI Embeddings 사용
- **동작 방식**: 
  1. 문장 단위로 임베딩 생성
  2. 인접 문장 간 의미적 유사도(코사인 거리) 계산
  3. 임계값을 초과하는 지점(의미가 크게 변하는 지점)에서 분할
- **파라미터**:
  - `breakpoint_threshold_type`: 분할 임계값 결정 방식
    - `percentile`: 거리 분포의 95 백분위수 사용 (기본 권장)
    - `standard_deviation`: 평균 + 3×표준편차 사용
    - `interquartile`: IQR(Inter-Quartile Range) 기반 이상치 제거
- **장점**: 의미적으로 응집력 있는 청크 생성, 주제별 자연스러운 분리
- **단점**: 임베딩 API 호출로 인한 비용 및 시간 증가, 청크 크기 불균등
- **추천 사용 사례**: 인터뷰/대화 기록, 주제가 자주 바뀌는 문서, 리포트

**3. Hybrid Chunking (하이브리드)**
- **알고리즘**: Length + Semantic 2단계 처리
- **동작 방식**:
  1. 1단계: `RecursiveCharacterTextSplitter`로 큰 청크 생성 (기본 1000자)
  2. 2단계: 각 청크를 `SemanticChunker`로 의미 기반 재분할
- **파라미터**:
  - `chunk_size`: 1단계 분할 크기 (기본값: 1000)
  - `overlap_size`: 1단계 오버랩 크기 (기본값: 100)
  - `breakpoint_threshold_type`: 2단계 의미 분할 임계값
- **장점**: 청크 크기 제어 + 의미적 응집성 확보, 긴 문서 처리 효율적
- **단점**: 가장 긴 처리 시간, API 비용 증가
- **추천 사용 사례**: 긴 연구 논문, 기술 문서, 복잡한 보고서

**4. Paragraph Chunking (문단 기반)**
- **알고리즘**: 문서 구조 기반 파서 사용
- **동작 방식**:
  - Markdown: `MarkdownHeaderTextSplitter`로 헤더(`#`, `##`, `###`) 기준 분할
  - HTML: `HTMLHeaderTextSplitter`로 태그(`<h1>`, `<h2>`, `<h3>`) 기준 분할
  - 일반 텍스트: 문단 구분자(`\n\n`) 기준 분할
- **파라미터**: 없음 (문서 구조 자동 감지)
- **장점**: 문서의 원래 구조 보존, 빠른 처리, 추가 API 비용 없음
- **단점**: 구조화되지 않은 문서에는 비효율적, 청크 크기 불균등
- **추천 사용 사례**: 위키 문서, 기술 매뉴얼, Markdown/HTML 파일, 정책 문서

**청킹 방법 선택 가이드**:
```
문서 특성            → 권장 방법
─────────────────────────────────────
짧은 일반 텍스트      → Length
긴 문서 (빠른 처리)   → Length (큰 chunk_size)
의미 단위 분리 필요   → Semantic
긴 문서 (의미 보존)   → Hybrid
구조화된 문서         → Paragraph
대화/인터뷰          → Semantic
기술 문서/매뉴얼      → Paragraph 또는 Hybrid
```

**임베딩 모델**: 모든 청킹 후 `text-embedding-3-small` (OpenAI) 사용하여 벡터화

#### 그래프 구조 개념
- 노드(Node): 입력/프롬프트/리트리벌/조건/출력 등 처리 단위를 정의
  - RetrievalNode: `params.collection` 파라미터로 검색할 컬렉션 지정 가능
- 엣지(Edge): 노드 간 데이터 플로우(방향성) 정의
- 그래프 히스토리(Graph History): 실행 시점/입출력/결과를 기록하여 추적/디버깅에 활용

#### 컬렉션 기능
- **컬렉션이란?**: 문서를 논리적으로 그룹화하는 단위로, ChromaDB의 Collection 개념 활용
- **사용 사례**:
  - 프로젝트별 문서 분리 (project_a, project_b)
  - 문서 타입별 분리 (contracts, manuals, reports)
  - 사용자별 문서 격리 (user_123, user_456)
- **검색 격리**: RetrievalNode에서 특정 컬렉션만 검색하여 검색 범위 제한
- **주의사항**:
  - 문서 생성 시 collection_id 필수
  - 컬렉션 삭제 시 내부 문서가 있으면 삭제 불가
  - 문서 삭제 시 벡터 스토어에서도 자동 삭제

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
```bash
cd docker
./docker_build.sh

# 개별 빌드도 가능
./docker_build.sh --backend-only
./docker_build.sh --frontend-only
```

#### Kubernetes 배포

##### 사전 요구사항
- Kubernetes 클러스터 (minikube, kind, EKS, GKE, AKS 등)
- `kubectl` CLI 도구 설치 및 클러스터 연결
- Docker 이미지 빌드 완료

##### 로컬 개발 환경 (Minikube - 선택사항)

Minikube는 로컬에서 Kubernetes를 실행하기 위한 도구입니다. 로컬 개발/테스트 환경에서 사용하며, 프로덕션 환경에서는 관리형 Kubernetes 서비스(EKS, GKE, AKS 등)를 사용하세요.

```bash
cd k8s

# Minikube 시작 (자동으로 Ingress addon 활성화 및 Tunnel 실행)
./minikube.sh start

# 상태 확인
./minikube.sh status

# 중지 (데이터 보존)
./minikube.sh stop

# 완전 삭제 (데이터 삭제)
./minikube.sh stop --delete
```

**Minikube 데이터 영속성:**
- ✅ `minikube stop` → `minikube start`: 데이터 보존
- ✅ Pod 재시작, Deployment 재배포: 데이터 보존
- ❌ `minikube delete`: 모든 데이터 삭제

##### 애플리케이션 배포

```bash
cd k8s

# 1. Secret 설정 (최초 1회)
# secret.example.yaml을 참고하여 secret.yaml 생성
vim secret.yaml

# 2. 전체 배포
./deploy.sh                   # ConfigMap/Secret/DB/BE/FE/Ingress 전체 배포

# 3. 상태 확인
./deploy.sh --status          # 배포 상태 확인
kubectl get pods              # Pod 상태 확인
kubectl get pvc               # 스토리지 확인

# 개별 배포 옵션
./deploy.sh --backend-only    # 백엔드만
./deploy.sh --frontend-only   # 프론트엔드만
./deploy.sh --config-only     # ConfigMap/Secret만

# 네임스페이스 지정
./deploy.sh -n production     # 프로덕션 네임스페이스
./deploy.sh -n development    # 개발 네임스페이스

# 삭제
./deploy.sh --delete          # 모든 리소스 삭제
```

##### 접속 방법

**1) Ingress 사용 (권장 - Minikube 환경)**

Minikube Tunnel이 실행되면 Ingress를 통해 접속할 수 있습니다:

```bash
# 1. /etc/hosts 파일 설정 (최초 1회)
sudo sh -c 'echo "127.0.0.1 aiagent.local" >> /etc/hosts'

# 2. Ingress 확인
kubectl get ingress

# 예시 출력:
# NAME              CLASS   HOSTS           ADDRESS     PORTS   AGE
# aiagent-ingress   nginx   aiagent.local   127.0.0.1   80      5m

# 3. 브라우저에서 접속
# Frontend: http://aiagent.local/
# Backend API: http://aiagent.local/api/
# API Docs: http://aiagent.local/api/docs
```

**참고:** 
- Ingress에 `host: aiagent.local`이 설정되어 있어 해당 도메인으로만 접속 가능합니다
- `localhost`로 접속하려면 `ingress.yaml`의 `host` 부분을 제거하세요

**Tunnel 확인 및 시작:**
```bash
# Tunnel 상태 확인
cd k8s
./minikube.sh status

# Tunnel 시작 (필요시)
./minikube.sh tunnel
```

**2) Port Forwarding (개별 Service 테스트)**

Tunnel 없이 개별 Service를 테스트할 때:

```bash
# Backend API
kubectl port-forward svc/ai-agent-backend-service 8000:8000

# Frontend
kubectl port-forward svc/ai-agent-frontend-service 3000:3000

# PostgreSQL
kubectl port-forward svc/postgres-service 5432:5432

# 접속: http://localhost:8000, http://localhost:3000
```

**3) 프로덕션 환경**

관리형 Kubernetes(EKS, GKE, AKS)에서는 LoadBalancer IP 또는 도메인으로 직접 접근:

```bash
# LoadBalancer External IP 확인
kubectl get services
kubectl get ingress
```

##### 이미지 업데이트

```bash
# 1. 이미지 재빌드
cd docker
./docker_build.sh

# 2. Minikube에 이미지 로드 (Minikube 사용 시)
cd ../k8s
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest

# 3. Deployment 재시작
kubectl rollout restart deployment/ai-agent-backend-deployment
kubectl rollout restart deployment/ai-agent-frontend-deployment
```

##### 프로덕션 환경 배포

프로덕션 환경에서는 다음 사항을 추가로 고려하세요:

- **관리형 Kubernetes**: AWS EKS, GCP GKE, Azure AKS 등 사용
- **스토리지**: 클라우드 기반 Persistent Volume (EBS, Persistent Disk 등)
- **Secret 관리**: AWS Secrets Manager, HashiCorp Vault 등 사용
- **모니터링**: Prometheus, Grafana 등 연동
- **로깅**: ELK Stack, Loki 등 중앙 집중식 로그 수집
- **백업**: 데이터베이스 스냅샷 정책 수립
- **보안**: NetworkPolicy, Pod Security Policy 적용
- **스케일링**: Horizontal Pod Autoscaler (HPA) 설정

자세한 내용은 `k8s/README.md`를 참고하세요.

---

### 문제 해결(트러블슈팅)
- 404/경로 이슈: 프록시/Ingress 뒤에서는 `ROOT_PATH=/api`에 맞춰 최종 경로가 `/api/v1`가 되도록 구성
- CORS 오류: 백엔드 `allow_origins`에 실제 프론트 호스트 추가
- 벡터 인덱스 권한: `VECTOR_STORE_DATA_DIR` 쓰기 가능 경로 확인
- DB 접속 실패: `DATABASE_URL` 호스트/포트/크리덴셜/Service 이름 확인

### 라이선스/문의
- 라이선스: 별도 파일이 없으면 내부용으로 사용
- 문의: 저장소 이슈 또는 팀 담당자에게 연락


