import axios from "axios";

const API_BASE = "http://0.0.0.0:8000/v1"; // FastAPI 백엔드 주소

export async function runGraph(graph: any) {
  const res = await axios.post(`${API_BASE}/graphs/run-graph`, graph);
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
  const params = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      params.append(key, value.toString());
    }
  });

  // 디버깅을 위해 URL 출력
  const url = `${API_BASE}/documents?${params.toString()}`;
  console.log('API 요청 URL:', url);

  const res = await axios.get(url);
  return res.data;
}

export async function getDocument(documentId: string) {
  const res = await axios.get(`${API_BASE}/documents/${documentId}`);
  return res.data;
}

export async function createDocument(document: Partial<Document> | FormData) {
  const res = await axios.post(`${API_BASE}/documents`, document, {
    headers: document instanceof FormData ? {
      'Content-Type': 'multipart/form-data',
    } : {
      'Content-Type': 'application/json',
    }
  });
  return res.data;
}

export async function updateDocument(documentId: string, document: Partial<Document>) {
  const res = await axios.put(`${API_BASE}/documents/${documentId}`, document);
  return res.data;
}

export async function deleteDocument(documentId: string) {
  const res = await axios.delete(`${API_BASE}/documents/${documentId}`, {
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
  const res = await axios.get(`${API_BASE}/documents/${documentId}`);
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
  const params = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      params.append(key, value.toString());
    }
  });

  const url = `${API_BASE}/graphs?${params.toString()}`;
  console.log('그래프 API 요청 URL:', url);

  const res = await axios.get(url);
  return res.data;
}

export async function getGraph(graphId: string) {
  const res = await axios.get(`${API_BASE}/graphs/${graphId}`);
  return res.data;
}

export async function createGraph(graph: Partial<Graph> & { nodes?: any[], edges?: any[] }) {
  console.log('createGraph API 호출:', graph);
  try {
    const res = await axios.post(`${API_BASE}/graphs`, graph);
    console.log('createGraph API 응답:', res.data);
    return res.data;
  } catch (error) {
    console.error('createGraph API 에러:', error);
    throw error;
  }
}

export async function updateGraph(graphId: string, graph: Partial<Graph> & { nodes?: any[], edges?: any[] }) {
  const res = await axios.put(`${API_BASE}/graphs/${graphId}`, graph);
  return res.data;
}

export async function deleteGraph(graphId: string) {
  const res = await axios.delete(`${API_BASE}/graphs/${graphId}`, {
    data: {
      updated_by: "admin"
    }
  });
  return res.data;
}

