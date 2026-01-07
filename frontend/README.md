# Frontend - AI Agent MVP

Next.js 15 기반의 AI Agent MVP 프론트엔드 애플리케이션입니다. React Flow를 활용한 그래프 에디터와 문서 관리 UI를 제공합니다.

## 📖 목차

- [프로젝트 구조](#-프로젝트-구조)
- [주요 컴포넌트](#-주요-컴포넌트)
- [상태 관리](#-상태-관리)
- [API 통신](#-api-통신)
- [개발 환경 설정](#-개발-환경-설정)
- [빌드 및 배포](#-빌드-및-배포)
- [스타일링](#-스타일링)

---

## 📁 프로젝트 구조

```
frontend/
├── app/                        # Next.js 15 App Router
│   ├── layout.tsx              # 루트 레이아웃 (ThemeProvider, 폰트)
│   ├── page.tsx                # 메인 페이지 (Sidebar + Header + MainContent)
│   ├── loading.tsx             # 로딩 상태
│   ├── globals.css             # 전역 스타일
│   └── runtime-config/         # 런타임 환경 변수 API
│       └── route.ts
│
├── components/                 # React 컴포넌트
│   ├── sidebar.tsx             # 좌측 사이드바 (메뉴 네비게이션)
│   ├── header.tsx              # 상단 헤더 (페이지 제목, 사용자 정보)
│   ├── main-content.tsx        # 메인 콘텐츠 라우터
│   │
│   ├── graph-editor.tsx        # 그래프 에디터 (React Flow 기반)
│   ├── graph-snippet.tsx       # 미리 정의된 그래프 템플릿 데이터
│   ├── node.tsx                # 커스텀 노드 컴포넌트
│   │
│   ├── agent-management-page.tsx  # Agent 관리 페이지
│   ├── knowledge-management-page.tsx  # 지식 관리 페이지
│   ├── document-detail-page.tsx  # 문서 상세 페이지
│   ├── collection-manager-dialog.tsx  # 컬렉션 관리 다이얼로그
│   │
│   ├── resizer.tsx             # 패널 리사이저
│   ├── theme-provider.tsx      # 다크모드/라이트모드 Provider
│   │
│   └── ui/                     # Radix UI + shadcn/ui 컴포넌트
│       ├── button.tsx
│       ├── dialog.tsx
│       ├── input.tsx
│       ├── select.tsx
│       ├── table.tsx
│       ├── tabs.tsx
│       └── ... (35+ 컴포넌트)
│
├── lib/                        # 유틸리티 라이브러리
│   ├── api.ts                  # Backend API 클라이언트 함수
│   └── utils.ts                # 공통 유틸리티 (cn, 날짜 포맷 등)
│
├── hooks/                      # 커스텀 React Hooks
│   ├── use-mobile.tsx          # 모바일 감지 Hook
│   └── use-toast.ts            # Toast 알림 Hook
│
├── public/                     # 정적 파일
│   ├── logo.png
│   └── ...
│
├── styles/                     # 추가 스타일
│   └── globals.css
│
├── next.config.mjs             # Next.js 설정
├── tailwind.config.ts          # TailwindCSS 설정
├── tsconfig.json               # TypeScript 설정
├── components.json             # shadcn/ui 설정
├── package.json                # 의존성 및 스크립트
└── Dockerfile                  # 컨테이너 이미지 빌드
```

### 디렉토리별 역할

| 디렉토리 | 역할 |
|---------|------|
| `app/` | Next.js 15 App Router (라우팅, 레이아웃, 페이지) |
| `components/` | 재사용 가능한 React 컴포넌트 |
| `components/ui/` | 공통 UI 컴포넌트 (버튼, 입력, 다이얼로그 등) |
| `lib/` | API 클라이언트, 유틸리티 함수 |
| `hooks/` | 커스텀 React Hooks |
| `public/` | 정적 파일 (이미지, 아이콘) |

---

## 🎨 주요 컴포넌트

### 1. 메인 레이아웃 컴포넌트

#### `app/page.tsx`

애플리케이션의 메인 진입점입니다.

**상태 관리:**
- `sidebarOpen`: 사이드바 열림/닫힘 상태
- `currentPage`: 현재 활성화된 페이지 (`graph-editor`, `agent-management`, `knowledge-management`)

**구조:**
```tsx
<Sidebar />           // 좌측 메뉴
<div>
  <Header />          // 상단 헤더
  <MainContent />     // 페이지 콘텐츠
</div>
```

#### `components/sidebar.tsx`

좌측 네비게이션 메뉴입니다.

**메뉴 항목:**
- **그래프 에디터**: 그래프 설계 및 실행
- **Agent 관리**: 저장된 그래프 목록/검색/편집
- **지식 관리**: 컬렉션/문서 관리

**주요 기능:**
- 접기/펼치기 토글
- 활성 메뉴 하이라이트
- 반응형 디자인 (모바일에서는 오버레이)

#### `components/header.tsx`

상단 헤더 바입니다.

**표시 정보:**
- 현재 페이지 제목
- 사용자 정보 (향후 구현 예정)
- 테마 토글 (다크모드/라이트모드)

#### `components/main-content.tsx`

현재 페이지에 따라 적절한 컴포넌트를 렌더링하는 라우터입니다.

```tsx
switch (currentPage) {
  case "agent-management":
    return <AgentManagementPage />
  case "knowledge-management":
    return <KnowledgeManagementPage />
  case "graph-editor":
    return <GraphEditor />
}
```

---

### 2. 그래프 에디터 컴포넌트

#### `components/graph-editor.tsx`

React Flow 기반의 비주얼 그래프 에디터입니다.

**레이아웃 구조:**
```
┌─────────────┬──────────────────────┬─────────────┐
│   Node      │                      │   Chat      │
│  Sidebar    │     Canvas           │   Panel     │
│             │   (ReactFlow)        │             │
│  - Nodes    │                      │  - 메시지     │
│  - Snippets │                      │  - 실행결과    │
└─────────────┴──────────────────────┴─────────────┘
```

**주요 기능:**
1. **노드 사이드바** (좌측): 클릭하여 추가할 수 있는 노드 버튼 및 템플릿 목록
2. **캔버스** (중앙): 추가된 노드를 드래그하여 위치 조정 및 엣지로 연결
3. **노드 설정**: 각 노드 내에서 직접 설정 편집 (프롬프트, 입력, 출력 등)
4. **그래프 저장/불러오기**: DB에 그래프 저장 및 조회
5. **채팅 패널** (우측): 그래프 실행 및 결과 확인 UI

**상태 관리:**
- `nodes`: React Flow 노드 배열
- `edges`: React Flow 엣지 배열
- `messages`: 채팅 메시지 배열 (사용자 입력 및 AI 응답)
- `currentGraphData`: 그래프 메타데이터 (이름, 설명, 버전)
- `isRunning`: 그래프 실행 중 여부
- `isSaving`: 그래프 저장 중 여부

**서브컴포넌트:**

##### 노드 사이드바 (`NodeSidebar`)

그래프 에디터 좌측의 노드 추가 패널입니다.

**Nodes 섹션:**
- 📥 Add Input Node: 사용자 입력 받는 노드
- 💬 Add Prompt Node: LLM 프롬프트 노드
- 🔍 Add Retrieval Node: 벡터 검색 노드
- 🔀 Add Condition Node: 조건 분기 노드
- 🔗 Add Merge Node: 병렬 결과 병합 노드
- 📤 Add Output Node: 최종 출력 포맷팅 노드

**Snippets 섹션:**
- 미리 정의된 그래프 템플릿 버튼 목록
- 클릭 시 현재 그래프를 템플릿으로 교체
- 자동 레이아웃 적용 (BFS 알고리즘)

**핵심 이벤트 핸들러:**

##### 노드 추가
```tsx
const onAddNode = () => {
  // 새 Prompt 노드 생성
  const newNode: Node = {
    id: `node-${nodes.length + 1}`,
    type: "BaseNode",
    position: { x: 100 + nodes.length * 350, y: 200 },
    data: {
      nodeType: "PromptNode",
      system_prompt: "",
      user_prompt: "",
      assistant_prompt: "",
      inputs: {},
      output: "answer",
    },
  }
  setNodes((nds) => [...nds, newNode])
}

// 각 노드 타입별로 별도의 추가 함수 존재
// onAddInputNode, onAddRetrievalNode, onAddOutputNode, 
// onAddConditionNode, onAddMergeNode
```

##### 노드 연결
```tsx
const onConnect = useCallback((params: any) => {
  // 소스 노드와 타겟 노드 정보 가져오기
  const sourceNode = nodes.find(n => n.id === params.source)
  const targetNode = nodes.find(n => n.id === params.target)
  
  // ConditionNode의 경우 특별한 Handle 처리
  if (sourceNode.data.nodeType === "ConditionNode" && params.sourceHandle) {
    // 조건별 타겟 설정
    // ...
  } else {
    // 일반 노드의 output을 타겟 노드의 inputs에 자동 매핑
    // ...
  }
  
  // 엣지 추가 (화살표 마커 포함)
  const newEdge = {
    ...params,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 15,
      height: 15,
      color: '#6b7280',
    },
  }
  setEdges((eds) => addEdge(newEdge, eds))
}, [setEdges, setNodes, nodes])
```

##### 그래프 저장
```tsx
const handleSaveGraph = async () => {
  // 이름이 없으면 입력 팝업 표시
  if (!currentGraphData?.name) {
    setIsGraphInfoDialogOpen(true)
    return
  }
  
  const graphData = {
    name: currentGraphData.name,
    description: currentGraphData.description || '',
    version: currentGraphData.version || 1,
    nodes: nodes.map((n, index) => ({
      node_id: n.id,
      type: n.data.nodeType || "PromptNode",
      output: n.data.output || "output",
      position: n.position ? { x: n.position.x, y: n.position.y } : null, // 위치 저장
      order: index,
      params: {
        // 노드 타입별 파라미터 처리
        ...(n.data.nodeType === "InputNode" ? {} : 
            n.data.nodeType === "OutputNode" ? {
              wrap_template: n.data.wrap_template || "",
              inputs: n.data.inputs || {},
            } : n.data.nodeType === "PromptNode" ? {
              system_prompt: n.data.system_prompt || "",
              user_prompt: n.data.user_prompt || "",
              assistant_prompt: n.data.assistant_prompt || "",
              inputs: n.data.inputs || {},
            } : /* 기타 노드 타입들... */ {})
      }
    })),
    edges: edges.map((e) => ({
      source: e.source,
      target: e.target,
    })),
    created_by: "admin",
    updated_by: "admin",
  }
  
  if (isCreateMode || graphId === 'create') {
    // 새 그래프 생성
    await createGraph(graphData)
  } else if (graphId) {
    // 기존 그래프 수정
    await updateGraph(graphId, graphData)
  }
}
```

#### `components/node.tsx`

React Flow 커스텀 노드 컴포넌트입니다. 각 노드는 자체 편집 기능을 포함합니다.

**노드 타입별 스타일:**
- **InputNode**: 파란색 배경 (blue-50)
- **PromptNode**: 흰색 배경
- **RetrievalNode**: 보라색 배경 (purple-50)
- **ConditionNode**: 노란색 배경 (yellow-50)
- **MergeNode**: 주황색 배경 (orange-50)
- **OutputNode**: 초록색 배경 (green-50)

**주요 기능:**
- **노드 ID 편집**: ID 클릭하여 수정 가능
- **노드 삭제**: 우측 상단 삭제 버튼
- **정보 아이콘**: 노드 타입별 도움말 표시
- **인라인 편집**: 각 노드 내에서 직접 설정 수정
- **자동 입력 추출**: 프롬프트 템플릿에서 `{변수}` 자동 감지

**구조:**
```tsx
<div className={getNodeStyle()}>
  {/* 헤더 */}
  <div className="flex justify-between">
    <span>{nodeType}</span>
    <div>
      <InfoButton /> {/* 정보 아이콘 */}
      <DeleteButton /> {/* 삭제 버튼 */}
    </div>
  </div>
  
  {/* 노드 ID 편집 */}
  <input value={nodeId} onBlur={commitNodeId} />
  
  {/* 노드 타입별 설정 UI */}
  <NodeTypeSpecificUI />
  
  {/* Handle (연결 포인트) */}
  <Handle type="target" position={Position.Left} />
  <Handle type="source" position={Position.Right} />
</div>
```

**Handle (연결 포인트):**
- `target`: 노드 왼쪽, 들어오는 엣지 연결
- `source`: 노드 오른쪽, 나가는 엣지 연결
- **ConditionNode**: 각 조건마다 별도의 source handle 생성

#### `components/graph-snippet.tsx`

미리 정의된 그래프 템플릿(스니펫)을 제공하는 파일입니다.

**제공하는 스니펫:**
1. **기본 검색 그래프**: InputNode → PromptNode → RetrievalNode → PromptNode → OutputNode
2. **병렬 분기 + 병합 테스트**: ConditionNode와 MergeNode를 활용한 병렬 처리 예시
3. **Condition 테스트 (Parallel)**: 조건 기반 병렬 실행 예시
4. **단순 대화형 봇**: 기본 대화 처리 그래프

**사용 방법:**
- 그래프 에디터 좌측 사이드바의 "Snippets" 섹션에서 선택
- 클릭 시 현재 그래프를 템플릿으로 교체
- 자동 레이아웃 적용 (BFS 알고리즘)

#### 채팅 패널 (`ChatPanel` in `graph-editor.tsx`)

우측의 채팅 형식 실행 및 결과 확인 패널입니다.

**주요 기능:**
1. **메시지 입력**: 하단에 사용자 메시지 입력
2. **실행**: 메시지 전송 시 자동으로 그래프 실행
3. **대화 형식 결과**: 
   - 사용자 메시지와 AI 답변을 채팅 형식으로 표시
   - Markdown 렌더링 지원
4. **확장 패널**:
   - **노드별 입출력**: 각 노드의 입력/출력 상세 정보
   - **그래프 히스토리**: 실행 타임라인
   - **그래프 스테이트**: 전체 실행 결과 JSON

**실행 프로세스:**
```tsx
const onSendMessage = async (userInput: string) => {
  // 메시지 추가
  setMessages((msgs) => [...msgs, { 
    role: "user", 
    content: userInput,
    timestamp: new Date()
  }])
  
  setIsRunning(true)
  
  // input_state 구성 (InputNode의 출력 키에 맞춰)
  const inputState = { input: userInput }
  
  // 그래프 데이터 구성
  const graph = {
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.data.nodeType || "PromptNode",
      output: n.data.output || "output",
      params: { /* 노드별 파라미터 */ }
    })),
    edges: edges.map((e) => ({
      source: e.source,
      target: e.target,
    })),
    input_state: inputState,
  }
  
  // Backend API 호출
  const res = await runGraph(graph)
  
  // 결과를 Agent 메시지로 추가
  setMessages((msgs) => [...msgs, { 
    role: "agent", 
    content: JSON.stringify(res.results, null, 2),
    timestamp: new Date()
  }])
  
  setIsRunning(false)
}
```

**결과 표시 예시:**
- **AI 답변**: OutputNode의 agent_output을 Markdown으로 렌더링
- **노드별 입출력**: 각 노드의 status, inputs, outputs, error_message 표시
- **히스토리**: 그래프 실행 시작/완료 타임라인
- **스테이트**: 전체 structured_results와 execution_info를 JSON으로 표시

---

### 3. Agent 관리 컴포넌트

#### `components/agent-management-page.tsx`

저장된 그래프 목록을 관리하는 페이지입니다.

**주요 기능:**
1. **그래프 목록**: 카드 형태로 그래프 표시
2. **검색**: 이름/설명으로 실시간 검색
3. **정렬**: 생성일/수정일/이름순 정렬
4. **필터**: 버전별 필터
5. **액션**:
   - **편집**: 그래프 에디터로 불러오기
   - **삭제**: 그래프 삭제 (확인 다이얼로그)
   - **복제**: 그래프 복사 (향후 구현)

**상태 관리:**
- `graphs`: 그래프 목록
- `searchTerm`: 검색어
- `sortBy`: 정렬 기준
- `currentPage`: 페이지 번호

**그래프 카드 구조:**
```tsx
<Card>
  <CardHeader>
    <h3>{graph.name}</h3>
    <Badge>v{graph.version}</Badge>
  </CardHeader>
  
  <CardContent>
    <p>{graph.description}</p>
    <div className="metadata">
      <span>작성자: {graph.created_by}</span>
      <span>수정일: {formatDate(graph.updated_at)}</span>
    </div>
  </CardContent>
  
  <CardFooter>
    <Button onClick={() => handleEdit(graph.id)}>편집</Button>
    <Button variant="destructive" onClick={() => handleDelete(graph.id)}>
      삭제
    </Button>
  </CardFooter>
</Card>
```

**그래프 불러오기:**
```tsx
const handleEdit = async (graphId: string) => {
  // Backend에서 그래프 조회
  const graph = await getGraph(graphId)
  
  // 그래프 에디터로 페이지 전환
  setCurrentPage("graph-editor")
  
  // 에디터에 그래프 데이터 로드
  loadGraphToEditor(graph)
}
```

---

### 4. 지식 관리 컴포넌트

#### `components/knowledge-management-page.tsx`

문서를 관리하는 메인 페이지입니다.

**주요 기능:**

1. **검색 및 필터링**:
   - 컬렉션별 필터 (드롭다운 선택)
   - 문서명 검색
   - 문서 ID, 청킹 ID, 청킹 내용, 경로 검색
   - 상태별 필터 (pending/indexed/deleted)
   - 초기화 버튼

2. **문서 목록 테이블**:
   - 컬럼: 컬렉션, 문서명, 청킹 사이즈, 오버랩 사이즈, 청킹 방법, 상태, 작업
   - 정렬: 각 컬럼 클릭으로 오름차순/내림차순 정렬
   - 더블클릭: 문서 상세 페이지로 이동
   - 삭제 버튼: 확인 다이얼로그 후 삭제

3. **페이지네이션**:
   - 페이지 번호 선택
   - 이전/다음 페이지 이동
   - 페이지당 항목 수 선택 (10/20/50)
   - 전체 항목 수 및 현재 페이지 정보 표시

4. **문서 생성 버튼**:
   - "문서 생성" 버튼 클릭 시 문서 생성 페이지로 이동

**상태 관리:**
- `documents`: 문서 목록
- `collections`: 컬렉션 목록 (필터용)
- `filters`: 검색/필터 조건
- `sortField`, `sortDirection`: 정렬 기준
- `currentPage`, `totalCount`: 페이지네이션 정보
- `selectedDocumentId`: 선택된 문서 ID (상세 페이지 이동 시)

#### `components/document-detail-page.tsx`

문서 상세/수정 및 문서 생성을 처리하는 페이지입니다.

**두 가지 모드:**

##### 1. 문서 상세/수정 모드
문서 더블클릭 시 진입하며, 다음 정보를 표시합니다:
- 문서명 (편집 가능)
- 컬렉션 정보 (Badge 표시)
- 경로, 상태
- 청킹 방법, 청킹 사이즈, 오버랩 사이즈
- 임계값 유형 (semantic/hybrid인 경우)
- 생성자, 생성일, 수정일
- **청크 목록**: 스크롤 가능한 카드 형태로 각 청크의 인덱스, 내용, 생성일 표시

##### 2. 문서 생성 모드
"문서 생성" 버튼 클릭 시 진입하며, 다음 폼을 제공합니다:

**컬렉션 선택:**
- 읽기 전용 입력 필드
- 돋보기 버튼 (🔍): 클릭 시 `CollectionManagerDialog` 열림
- 이 다이얼로그에서 컬렉션 선택 또는 새로 생성 가능

**문서명:**
- 텍스트 입력 (최대 1000자)
- 실시간 글자 수 표시

**청킹 방법 선택:**
- Length (길이 기반)
- Semantic (의미 기반)
- Hybrid (하이브리드)
- Paragraph (문단 기반)

**청킹 방법별 설정:**
- **Length**: 청킹 사이즈, 오버랩 사이즈 입력
- **Semantic**: 임계값 유형 선택 (percentile/standard_deviation/interquartile)
- **Hybrid**: 청킹 사이즈 + 오버랩 사이즈 + 임계값 유형
- **Paragraph**: 추가 설정 없음

**파일 업로드:**
- 파일 선택 버튼 (PDF, TXT 지원)
- 선택된 파일명 표시

**유효성 검사:**
- 컬렉션, 문서명, 파일 필수
- 청킹 방법별 필수값 검증
- 오버랩 사이즈는 청킹 사이즈보다 작아야 함

**상태 관리:**
- `document`: 문서 상세 데이터
- `collectionId`, `collectionName`: 선택된 컬렉션 정보
- `method`, `chunkSize`, `overlapSize`, `breakpointThresholdType`: 청킹 설정
- `uploadedFile`: 업로드할 파일
- `isCollectionDialogOpen`: 컬렉션 관리 다이얼로그 표시 여부

#### `components/collection-manager-dialog.tsx`

컬렉션을 선택하거나 새로 생성하는 다이얼로그입니다.

**주요 기능:**
- 컬렉션 목록 표시 (테이블 형태)
- 컬렉션 선택 (라디오 버튼)
- 컬렉션 생성: 이름과 설명 입력
- 컬렉션 수정: 기존 컬렉션의 이름과 설명 수정
- 컬렉션 삭제: 문서가 없는 컬렉션만 삭제 가능

**폼 필드:**
- 컬렉션 이름 (필수)
- 설명 (선택)

**사용 위치:**
- 문서 생성 페이지의 컬렉션 선택 돋보기 버튼 클릭 시

---

### 5. 공통 UI 컴포넌트 (`components/ui/`)

Radix UI와 shadcn/ui 기반의 재사용 가능한 UI 컴포넌트입니다.

**주요 컴포넌트:**
- `button.tsx`: 버튼 (variant: default, destructive, outline, ghost, link)
- `dialog.tsx`: 모달 다이얼로그
- `input.tsx`: 텍스트 입력
- `select.tsx`: 드롭다운 선택
- `table.tsx`: 테이블
- `tabs.tsx`: 탭
- `card.tsx`: 카드
- `badge.tsx`: 배지
- `alert.tsx`: 알림
- `toast.tsx`: 토스트 알림
- `scroll-area.tsx`: 스크롤 영역
- `separator.tsx`: 구분선

**사용 예시:**
```tsx
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"

<Dialog>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>제목</DialogTitle>
    </DialogHeader>
    <Input placeholder="입력하세요" />
    <Button>확인</Button>
  </DialogContent>
</Dialog>
```

---

## 🔄 상태 관리

### 로컬 상태 (useState)

대부분의 상태는 React의 `useState`로 관리합니다:

```tsx
const [nodes, setNodes] = useState<Node[]>([])
const [edges, setEdges] = useState<Edge[]>([])
const [selectedNode, setSelectedNode] = useState<Node | null>(null)
```

### 전역 상태

현재 전역 상태 관리 라이브러리(Redux, Zustand 등)를 사용하지 않습니다.

**이유:**
- 애플리케이션 규모가 크지 않음
- 페이지 간 공유해야 할 상태가 많지 않음
- Props drilling 문제가 크지 않음

**향후 고려 사항:**
- 사용자 인증 상태 추가 시 전역 상태 필요
- 그래프 에디터와 Agent 관리 간 데이터 동기화 필요 시 고려

---

## 📡 API 통신

### API 클라이언트 (`lib/api.ts`)

Backend API와 통신하는 함수들을 정의합니다.

**주요 함수:**

#### 그래프 관련
```tsx
// 그래프 실행
await runGraph(graphData: any): Promise<any>

// 그래프 목록 조회
await getGraphs(filters: GraphFilters): Promise<{ data: Graph[], pagination: Pagination }>

// 그래프 상세 조회
await getGraph(graphId: string): Promise<Graph>

// 그래프 생성
await createGraph(graph: Partial<Graph>): Promise<Graph>

// 그래프 수정
await updateGraph(graphId: string, graph: Partial<Graph>): Promise<Graph>

// 그래프 삭제
await deleteGraph(graphId: string): Promise<void>
```

#### 문서 관련
```tsx
// 문서 목록 조회
await getDocuments(filters: DocumentFilters): Promise<{ data: Document[], pagination: Pagination }>

// 문서 상세 조회
await getDocument(documentId: string): Promise<DocumentDetail>

// 문서 업로드
await createDocument(document: FormData): Promise<Document>

// 문서 수정
await updateDocument(documentId: string, document: Partial<Document>): Promise<Document>

// 문서 삭제
await deleteDocument(documentId: string): Promise<void>
```

#### 컬렉션 관련
```tsx
// 컬렉션 목록 조회
await getCollections(filters: CollectionFilters): Promise<{ data: Collection[], pagination: Pagination }>

// 컬렉션 상세 조회
await getCollection(collectionId: string): Promise<Collection>

// 컬렉션 생성
await createCollection(collection: Partial<Collection>): Promise<Collection>

// 컬렉션 수정
await updateCollection(collectionId: string, collection: Partial<Collection>): Promise<Collection>

// 컬렉션 삭제
await deleteCollection(collectionId: string): Promise<void>
```

### 런타임 설정 (`app/runtime-config/route.ts`)

Kubernetes ConfigMap에서 주입된 환경 변수를 프론트엔드에 전달하는 API 엔드포인트입니다.

```tsx
// GET /runtime-config
export async function GET() {
  return NextResponse.json({
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "",
  })
}
```

**동작 방식:**
1. Frontend가 `/runtime-config`를 호출
2. 서버 사이드에서 환경 변수를 읽어 JSON으로 반환
3. `lib/api.ts`의 `getApiBase()` 함수가 이 값을 캐싱
4. 모든 API 호출에서 동적으로 결정된 베이스 URL 사용

**장점:**
- 빌드 시점이 아닌 런타임에 API URL 결정
- 동일한 이미지를 여러 환경(dev, staging, prod)에서 재사용 가능

---

## 💻 개발 환경 설정

### 사전 요구사항

- Node.js 20+
- npm 또는 pnpm

### 1. 의존성 설치

```bash
cd frontend

# npm 사용
npm install

# 또는 pnpm 사용
pnpm install
```

### 2. 환경 변수 설정

`.env.local` 파일 생성 (선택):

```bash
# Backend API URL (빈 값이면 자동으로 window.location.origin + /api/v1 사용)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. 개발 서버 실행

```bash
npm run dev
```

애플리케이션이 `http://localhost:3000`에서 실행됩니다.

### 4. 빌드

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 실행
npm run start
```

---

## 🎨 스타일링

### TailwindCSS

프로젝트는 TailwindCSS를 사용하여 스타일링합니다.

**설정 파일:** `tailwind.config.ts`

**주요 설정:**
- 커스텀 컬러 팔레트 (primary, secondary, accent 등)
- 다크모드 지원 (class 기반)
- 커스텀 애니메이션

**사용 예시:**
```tsx
<div className="flex flex-col gap-4 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md">
  <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
    제목
  </h1>
  <Button className="bg-blue-500 hover:bg-blue-600 text-white">
    클릭
  </Button>
</div>
```

### CSS Modules

필요 시 CSS Modules도 사용 가능합니다.

```tsx
// styles/MyComponent.module.css
.container {
  padding: 1rem;
  background: white;
}

// components/MyComponent.tsx
import styles from "@/styles/MyComponent.module.css"

<div className={styles.container}>...</div>
```

### 전역 스타일

`app/globals.css`에 전역 스타일을 정의합니다.

**주요 내용:**
- Tailwind 기본 레이어 (`@tailwind base, components, utilities`)
- CSS 변수 (컬러, 간격 등)
- 다크모드 변수

---

## 🧩 커스텀 Hooks

### `hooks/use-mobile.tsx`

모바일 디바이스 감지 Hook입니다.

**사용 예시:**
```tsx
import { useMobile } from "@/hooks/use-mobile"

function MyComponent() {
  const isMobile = useMobile()
  
  return (
    <div>
      {isMobile ? <MobileMenu /> : <DesktopMenu />}
    </div>
  )
}
```

### `hooks/use-toast.ts`

토스트 알림을 표시하는 Hook입니다.

**사용 예시:**
```tsx
import { useToast } from "@/hooks/use-toast"

function MyComponent() {
  const { toast } = useToast()
  
  const handleSuccess = () => {
    toast({
      title: "성공",
      description: "작업이 완료되었습니다.",
      variant: "default",
    })
  }
  
  const handleError = () => {
    toast({
      title: "에러",
      description: "작업에 실패했습니다.",
      variant: "destructive",
    })
  }
  
  return (
    <>
      <Button onClick={handleSuccess}>성공 토스트</Button>
      <Button onClick={handleError}>에러 토스트</Button>
    </>
  )
}
```

---

## 🚀 빌드 및 배포

### Docker 이미지 빌드

```bash
cd docker
./docker_build.sh --frontend-only
```

이 스크립트는 `frontend/Dockerfile`을 사용하여 이미지를 빌드합니다.

**Dockerfile 주요 단계:**
1. **Builder Stage**: 의존성 설치 및 빌드
2. **Runner Stage**: 경량 이미지에 빌드 결과만 복사
3. 포트 3000 노출
4. `npm run start`로 Next.js 프로덕션 서버 실행

### Kubernetes 배포

프로젝트 루트의 [README](../README.md)를 참고하세요.

**주요 리소스:**
- **Deployment**: `k8s/frontend.yaml`
- **Service**: ClusterIP 타입, 포트 3000
- **Ingress**: Nginx를 통해 외부 노출
- **ConfigMap**: `NEXT_PUBLIC_API_BASE_URL` 주입

---

## 🧪 테스트

> **참고**: 현재 테스트 코드가 포함되어 있지 않습니다. 향후 추가 예정입니다.

테스트 추가 시 권장 구조:

```
frontend/
├── __tests__/
│   ├── components/
│   │   ├── graph-editor.test.tsx
│   │   ├── agent-management-page.test.tsx
│   │   └── knowledge-management-page.test.tsx
│   ├── lib/
│   │   └── api.test.ts
│   └── hooks/
│       └── use-toast.test.ts
```

**테스트 프레임워크 권장:**
- **Jest**: 단위 테스트
- **React Testing Library**: 컴포넌트 테스트
- **Cypress** 또는 **Playwright**: E2E 테스트

---

## 🐛 디버깅

### React DevTools

브라우저에 React DevTools 확장을 설치하여 컴포넌트 트리 및 상태를 검사할 수 있습니다.

### Next.js DevTools

Next.js 15는 내장 DevTools를 제공합니다.

- 개발 모드에서 `Shift + Ctrl + O` (Windows/Linux) 또는 `Shift + Cmd + O` (Mac)

### 콘솔 로그

API 호출 및 주요 이벤트는 콘솔에 로그를 남깁니다:

```tsx
console.log('API 요청 URL:', url)
console.log('그래프 실행 결과:', result)
```

**프로덕션 빌드 시 로그 제거:**
- Terser 플러그인이 자동으로 `console.log` 제거
- 또는 `NODE_ENV=production`일 때 조건부로 로그 비활성화

---

## 📚 추가 자료

- **Next.js 공식 문서**: https://nextjs.org/docs
- **React 공식 문서**: https://react.dev/
- **TailwindCSS 문서**: https://tailwindcss.com/docs
- **React Flow 문서**: https://reactflow.dev/
- **Radix UI 문서**: https://www.radix-ui.com/
- **shadcn/ui 문서**: https://ui.shadcn.com/

---

## 🛣️ 향후 개선 사항

### v1.1
- [ ] 사이드바에서 캔버스로 드래그 앤 드롭하여 노드 추가 기능
- [ ] 그래프 에디터 실행 취소/다시 실행 (Undo/Redo)
- [ ] 노드 그룹화 기능
- [ ] 그래프 확대/축소/중앙 정렬 툴바

### v1.2
- [ ] 그래프 실행 실시간 스트리밍
- [ ] 문서 업로드 진행 상태 표시
- [ ] 문서 업로드 시 드래그 앤 드롭 지원

### v2.0
- [ ] 사용자 인증 및 권한 관리 UI
- [ ] 그래프 템플릿 마켓플레이스
- [ ] 노드 실행 결과 시각화 (차트, 그래프)\

---

**Happy Coding! 🎉**
