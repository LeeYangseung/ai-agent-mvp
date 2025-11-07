import axios from "axios";

// 런타임 구성 값을 캐싱하여 최초 1회만 조회
let cachedApiBase: string | null = null;
let loadingPromise: Promise<string> | null = null;

async function getApiBase(): Promise<string> {
  if (cachedApiBase) return cachedApiBase;
  if (loadingPromise) return loadingPromise;

  loadingPromise = (async () => {
    try {
      // 프론트 런타임 설정을 가져옴 (ConfigMap에서 주입된 컨테이너 env를 읽어 전달)
      const res = await fetch("/runtime-config", { cache: "no-store" });
      const data = (await res.json()) as { apiBaseUrl?: string };

      // 1순위: ConfigMap에서 온 값
      if (data?.apiBaseUrl && data.apiBaseUrl.trim().length > 0) {
        cachedApiBase = data.apiBaseUrl;
        return cachedApiBase;
      }

      // 2순위: 브라우저 호스트 기반 자동 구성
      if (typeof window !== "undefined") {
        cachedApiBase = `${window.location.origin}/api/v1`;
        return cachedApiBase;
      }

      // 3순위: 서버 사이드 기본값 (개발용)
      cachedApiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:3000/api/v1";
      return cachedApiBase;
    } finally {
      loadingPromise = null;
    }
  })();

  return loadingPromise;
}

export async function runGraph(graph: any) {
  const base = await getApiBase();
  const res = await axios.post(`${base}/graphs/run-graph`, graph);
  return res.data;
}

// 문서 관리 API 함수들
export interface Document {
  id: string;  // 백엔드에서 id 필드 사용
  chunk_id?: string;
  name: string;  // 백엔드에서 name 필드 사용
  chunk_content?: string;
  path?: string;
  status: string;
  chunk_size?: number;
  overlap_size?: number;
  method?: string;
  breakpoint_threshold_type?: string;  // 시맨틱 청킹 임계값 유형
  updated_by?: string;  // 수정자 필드 추가
}

export interface DocumentFilters {
  document_id?: string;
  chunk_id?: string;
  document_name?: string;
  chunk_content?: string;
  path?: string;
  status?: string;
  sort?: string;
  page?: number;
  limit?: number;
}

export async function getDocuments(filters: DocumentFilters = {}) {
  const base = await getApiBase();
  const params = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      params.append(key, value.toString());
    }
  });

  // 디버깅을 위해 URL 출력
  const url = `${base}/documents?${params.toString()}`;
  console.log('API 요청 URL:', url);

  const res = await axios.get(url);
  return res.data;
}

export async function getDocument(documentId: string) {
  const base = await getApiBase();
  const res = await axios.get(`${base}/documents/${documentId}`);
  return res.data;
}

export async function createDocument(document: Partial<Document> | FormData) {
  const base = await getApiBase();
  const res = await axios.post(`${base}/documents`, document, {
    headers: document instanceof FormData ? {
      'Content-Type': 'multipart/form-data',
    } : {
      'Content-Type': 'application/json',
    }
  });
  return res.data;
}

export async function updateDocument(documentId: string, document: Partial<Document>) {
  const base = await getApiBase();
  const res = await axios.put(`${base}/documents/${documentId}`, document);
  return res.data;
}

export async function deleteDocument(documentId: string) {
  const base = await getApiBase();
  const res = await axios.delete(`${base}/documents/${documentId}`, {
    data: {
      updated_by: "admin"
    }
  });
  return res.data;
}

// 청크 관련 인터페이스
export interface Chunk {
  id: string;
  content: string;
  chunk_index: number;
  created_at: string;
  updated_at: string;
}

// 문서 상세 정보 인터페이스
export interface DocumentDetail extends Document {
  created_at: string;
  updated_at: string;
  chunks: Chunk[];
}

// 문서 상세 조회 (청크 목록 포함)
export async function getDocumentDetail(documentId: string) {
  const base = await getApiBase();
  const res = await axios.get(`${base}/documents/${documentId}`);
  return res.data;
}

// 그래프 관리 API 함수들
export interface Graph {
  id: string;
  name: string;
  description?: string;
  version?: number;
  created_by?: string;
  created_at?: string;
  updated_by?: string;
  updated_at?: string;
}

export interface GraphFilters {
  name?: string;
  description?: string;
  version?: number;
  sort?: string;
  page?: number;
  size?: number;
}

export async function getGraphs(filters: GraphFilters = {}) {
  const base = await getApiBase();
  const params = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      params.append(key, value.toString());
    }
  });

  const url = `${base}/graphs?${params.toString()}`;
  console.log('그래프 API 요청 URL:', url);

  const res = await axios.get(url);
  return res.data;
}

export async function getGraph(graphId: string) {
  const base = await getApiBase();
  const res = await axios.get(`${base}/graphs/${graphId}`);
  return res.data;
}

export async function createGraph(graph: Partial<Graph> & { nodes?: any[], edges?: any[] }) {
  console.log('createGraph API 호출:', graph);
  try {
    const base = await getApiBase();
    const res = await axios.post(`${base}/graphs`, graph);
    console.log('createGraph API 응답:', res.data);
    return res.data;
  } catch (error) {
    console.error('createGraph API 에러:', error);
    throw error;
  }
}

export async function updateGraph(graphId: string, graph: Partial<Graph> & { nodes?: any[], edges?: any[] }) {
  const base = await getApiBase();
  const res = await axios.put(`${base}/graphs/${graphId}`, graph);
  return res.data;
}

export async function deleteGraph(graphId: string) {
  const base = await getApiBase();
  const res = await axios.delete(`${base}/graphs/${graphId}`, {
    data: {
      updated_by: "admin"
    }
  });
  return res.data;
}

