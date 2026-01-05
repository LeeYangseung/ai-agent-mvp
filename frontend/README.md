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
│   ├── graph-snippet.tsx       # 그래프 실행 스니핏 (입력/실행/결과)
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

**주요 기능:**
1. **노드 팔레트**: 좌측에 드래그 가능한 노드 목록
2. **캔버스**: 노드를 배치하고 엣지로 연결
3. **속성 패널**: 선택된 노드의 설정 편집
4. **그래프 저장/불러오기**: DB에 그래프 저장 및 조회
5. **스니핏 패널**: 하단에 그래프 실행 UI

**상태 관리:**
- `nodes`: React Flow 노드 배열
- `edges`: React Flow 엣지 배열
- `selectedNode`: 현재 선택된 노드
- `graphInfo`: 그래프 메타데이터 (이름, 설명, 버전)

**핵심 이벤트 핸들러:**

##### 노드 추가
```tsx
const onDrop = (event: DragEvent) => {
  // 드래그된 노드 타입 가져오기
  const nodeType = event.dataTransfer.getData("application/reactflow")
  
  // 캔버스 좌표로 변환
  const position = screenToFlowPosition({
    x: event.clientX,
    y: event.clientY,
  })
  
  // 새 노드 생성
  const newNode = {
    id: `${nodeType}_${Date.now()}`,
    type: "custom",
    position,
    data: {
      label: nodeType,
      type: nodeType,
      params: getDefaultParams(nodeType),
    },
  }
  
  setNodes((nds) => nds.concat(newNode))
}
```

##### 노드 연결
```tsx
const onConnect = (connection: Connection) => {
  setEdges((eds) => addEdge(connection, eds))
}
```

##### 노드 선택
```tsx
const onNodeClick = (event: React.MouseEvent, node: Node) => {
  setSelectedNode(node)
  // 우측 속성 패널에 노드 정보 표시
}
```

##### 그래프 저장
```tsx
const handleSaveGraph = async () => {
  const graphData = {
    name: graphInfo.name,
    description: graphInfo.description,
    version: graphInfo.version || 1,
    nodes: nodes.map((node) => ({
      node_id: node.id,
      type: node.data.type,
      params: node.data.params,
      order: node.position.y, // Y 좌표를 실행 순서로 사용
    })),
    edges: edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
    })),
    created_by: "admin",
    updated_by: "admin",
  }
  
  if (graphInfo.id) {
    // 기존 그래프 수정
    await updateGraph(graphInfo.id, graphData)
  } else {
    // 새 그래프 생성
    await createGraph(graphData)
  }
}
```

#### `components/node.tsx`

React Flow 커스텀 노드 컴포넌트입니다.

**노드 타입별 스타일:**
- **InputNode**: 초록색 배경
- **PromptNode**: 파란색 배경
- **RetrievalNode**: 보라색 배경
- **ConditionNode**: 노란색 배경
- **MergeNode**: 주황색 배경
- **OutputNode**: 빨간색 배경

**구조:**
```tsx
<div className="node-wrapper">
  <Handle type="target" position={Position.Top} />
  
  <div className="node-header">
    <NodeIcon />
    <span>{nodeType}</span>
  </div>
  
  <div className="node-body">
    {/* 노드 타입별 파라미터 표시 */}
  </div>
  
  <Handle type="source" position={Position.Bottom} />
</div>
```

**Handle (연결 포인트):**
- `target`: 노드 상단, 들어오는 엣지 연결
- `source`: 노드 하단, 나가는 엣지 연결

#### `components/graph-snippet.tsx`

그래프 실행 및 결과 확인 패널입니다.

**주요 기능:**
1. **입력 탭**: 그래프에 전달할 입력값 입력 (JSON 형태)
2. **실행 버튼**: 현재 그래프를 Backend에 전송하여 실행
3. **결과 탭**: 
   - **Node Results**: 각 노드의 입출력 및 실행 시간
   - **Final State**: 최종 상태 딕셔너리
   - **Execution History**: 실행 순서 및 타임라인

**실행 프로세스:**
```tsx
const handleRunGraph = async () => {
  // 입력값 파싱
  const inputData = JSON.parse(inputValue)
  
  // 그래프 데이터 구성
  const graphData = {
    nodes: nodes.map((node) => ({
      id: node.id,
      type: node.data.type,
      params: node.data.params,
    })),
    edges: edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
    })),
    input: inputData,
  }
  
  // Backend API 호출
  const result = await runGraph(graphData)
  
  // 결과 표시
  setResults(result)
}
```

**결과 표시 예시:**
```tsx
<Tabs>
  <TabsList>
    <TabsTrigger value="node_results">Node Results</TabsTrigger>
    <TabsTrigger value="final_state">Final State</TabsTrigger>
    <TabsTrigger value="history">Execution History</TabsTrigger>
  </TabsList>
  
  <TabsContent value="node_results">
    {results.nodes.map((nodeResult) => (
      <Card>
        <h3>{nodeResult.node_id}</h3>
        <p>실행 시간: {nodeResult.execution_time}s</p>
        <pre>{JSON.stringify(nodeResult.output, null, 2)}</pre>
      </Card>
    ))}
  </TabsContent>
  
  <TabsContent value="final_state">
    <pre>{JSON.stringify(results.final_state, null, 2)}</pre>
  </TabsContent>
</Tabs>
```

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

문서 및 컬렉션을 관리하는 페이지입니다.

**주요 기능:**
1. **탭 구조**:
   - **문서 탭**: 문서 목록/업로드/상세/삭제
   - **컬렉션 탭**: 컬렉션 목록/생성/수정/삭제

2. **문서 목록**:
   - 테이블 형태로 문서 표시 (이름, 컬렉션, 상태, 생성일)
   - 필터: 컬렉션별, 상태별
   - 정렬: 이름/생성일/수정일
   - 페이지네이션

3. **문서 업로드**:
   - 파일 선택 (PDF, TXT)
   - 컬렉션 선택 (드롭다운)
   - 청킹 방법 선택:
     - **Length**: 청킹 사이즈, 오버랩 사이즈 입력
     - **Semantic**: 임계값 유형 선택
     - **Hybrid**: 청킹 사이즈 + 임계값 유형
     - **Paragraph**: 추가 설정 없음
   - "업로드" 버튼

4. **문서 상세**:
   - 문서 메타데이터 표시
   - 모든 청크 목록 표시 (인덱스, 내용)

5. **컬렉션 관리**:
   - 컬렉션 생성 다이얼로그
   - 컬렉션 수정 다이얼로그
   - 컬렉션 삭제 (문서가 없을 때만 가능)

**문서 업로드 폼:**
```tsx
<Dialog>
  <DialogTrigger asChild>
    <Button>문서 업로드</Button>
  </DialogTrigger>
  
  <DialogContent>
    <DialogHeader>
      <DialogTitle>문서 업로드</DialogTitle>
    </DialogHeader>
    
    <form onSubmit={handleUpload}>
      {/* 파일 선택 */}
      <Input type="file" accept=".pdf,.txt" onChange={handleFileChange} />
      
      {/* 컬렉션 선택 */}
      <Select value={collectionId} onValueChange={setCollectionId}>
        {collections.map((col) => (
          <SelectItem key={col.id} value={col.id}>
            {col.name}
          </SelectItem>
        ))}
      </Select>
      
      {/* 청킹 방법 선택 */}
      <Select value={chunkingMethod} onValueChange={setChunkingMethod}>
        <SelectItem value="length">Length (길이 기반)</SelectItem>
        <SelectItem value="semantic">Semantic (의미 기반)</SelectItem>
        <SelectItem value="hybrid">Hybrid (하이브리드)</SelectItem>
        <SelectItem value="paragraph">Paragraph (문단 기반)</SelectItem>
      </Select>
      
      {/* 청킹 방법별 설정 */}
      {chunkingMethod === "length" && (
        <>
          <Input 
            type="number" 
            placeholder="청킹 사이즈" 
            value={chunkSize} 
            onChange={(e) => setChunkSize(e.target.value)} 
          />
          <Input 
            type="number" 
            placeholder="오버랩 사이즈" 
            value={overlapSize} 
            onChange={(e) => setOverlapSize(e.target.value)} 
          />
        </>
      )}
      
      {(chunkingMethod === "semantic" || chunkingMethod === "hybrid") && (
        <Select value={thresholdType} onValueChange={setThresholdType}>
          <SelectItem value="percentile">Percentile (백분위수)</SelectItem>
          <SelectItem value="standard_deviation">Standard Deviation (표준편차)</SelectItem>
          <SelectItem value="interquartile">Interquartile (사분위수)</SelectItem>
        </Select>
      )}
      
      <Button type="submit">업로드</Button>
    </form>
  </DialogContent>
</Dialog>
```

**문서 업로드 처리:**
```tsx
const handleUpload = async (e: React.FormEvent) => {
  e.preventDefault()
  
  // FormData 생성
  const formData = new FormData()
  formData.append("file", selectedFile)
  formData.append("collection_id", collectionId)
  formData.append("method", chunkingMethod)
  formData.append("created_by", "admin")
  formData.append("updated_by", "admin")
  
  // 청킹 방법별 파라미터 추가
  if (chunkingMethod === "length" || chunkingMethod === "hybrid") {
    formData.append("chunk_size", chunkSize)
    formData.append("overlap_size", overlapSize)
  }
  
  if (chunkingMethod === "semantic" || chunkingMethod === "hybrid") {
    formData.append("breakpoint_threshold_type", thresholdType)
  }
  
  // Backend API 호출
  await createDocument(formData)
  
  // 문서 목록 새로고침
  fetchDocuments()
}
```

#### `components/document-detail-page.tsx`

문서 상세 정보와 청크 목록을 표시하는 페이지입니다.

**표시 정보:**
- 문서 이름, 경로, 상태
- 컬렉션 정보
- 청킹 방법 및 설정값
- 생성/수정 시간
- 청크 목록 (테이블 형태)
  - 청크 인덱스
  - 청크 내용 (접기/펼치기 가능)
  - 생성 시간

#### `components/collection-manager-dialog.tsx`

컬렉션 생성/수정 다이얼로그입니다.

**폼 필드:**
- 컬렉션 이름 (필수)
- 설명 (선택)

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
- [ ] 그래프 에디터 실행 취소/다시 실행 (Undo/Redo)
- [ ] 노드 그룹화 기능
- [ ] 그래프 확대/축소/중앙 정렬 툴바
- [ ] 그래프 미니맵

### v1.2
- [ ] 다크모드 개선
- [ ] 모바일 반응형 최적화
- [ ] 그래프 실행 실시간 스트리밍
- [ ] 문서 업로드 진행 상태 표시
- [ ] 드래그 앤 드롭 파일 업로드

### v2.0
- [ ] 사용자 인증 및 권한 관리 UI
- [ ] 그래프 템플릿 마켓플레이스
- [ ] 노드 실행 결과 시각화 (차트, 그래프)
- [ ] 실시간 협업 기능 (WebSocket)

---

**Happy Coding! 🎉**
