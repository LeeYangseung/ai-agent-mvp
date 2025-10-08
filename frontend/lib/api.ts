import axios from "axios";

const API_BASE = "http://0.0.0.0:8000/v1"; // FastAPI 백엔드 주소

export async function runGraph(graph: any) {
  const res = await axios.post(`${API_BASE}/graph/run-graph`, graph);
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

