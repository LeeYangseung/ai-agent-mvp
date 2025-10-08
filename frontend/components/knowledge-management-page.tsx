"use client"

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ChevronUp, ChevronDown, Search, RotateCcw, Trash2, Plus } from "lucide-react";
import { getDocuments, Document, DocumentFilters, deleteDocument, createDocument } from "@/lib/api";
import { DocumentDetailPage } from "./document-detail-page";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";

type SortField = 'document_name' | 'chunk_size' | 'overlap_size' | 'method' | 'status';
type SortDirection = 'asc' | 'desc';

// 백엔드 필드명 매핑 (필요시 수정)
const FIELD_MAPPING: Record<SortField, string> = {
  document_name: 'name',
  chunk_size: 'chunk_size', 
  overlap_size: 'overlap_size',
  method: 'method',
  status: 'status'
};

export function KnowledgeManagementPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<DocumentFilters>({
    page: 1,
    limit: 10
  });
  const [sortField, setSortField] = useState<SortField>('document_name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [isCreateMode, setIsCreateMode] = useState(false);

  // 정렬 처리
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // 정렬 아이콘 렌더링
  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />;
  };

  // 문서 목록 조회
  const fetchDocuments = async () => {
    setLoading(true);
    try {
      // 백엔드에서 기대하는 형식: sort=컬럼명:방향
      const backendField = FIELD_MAPPING[sortField];
      const sortParam = `${backendField}:${sortDirection}`;
      console.log('정렬 파라미터:', sortParam);
      
      // 백엔드는 0부터 시작하는 페이지네이션 사용
      const backendPage = currentPage - 1;
      console.log('프론트엔드 페이지:', currentPage, '백엔드 페이지:', backendPage);
      
      const response = await getDocuments({
        ...filters,
        sort: sortParam,
        page: backendPage,
        limit: 10
      });
      
      console.log('API 응답 전체:', response);
      console.log('응답 데이터:', response.data?.documents);
      console.log('응답 총 개수:', response.pagination?.total_count);
      
      setDocuments(response.data?.documents || []);
      setTotalCount(response.pagination?.total_count || 0);
    } catch (error) {
      console.error('문서 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 검색/필터링
  const handleSearch = () => {
    setCurrentPage(1);
    fetchDocuments();
  };

  // 필터 초기화
  const handleReset = () => {
    setFilters({
      page: 1,
      limit: 10
    });
    setCurrentPage(1);
    setSortField('document_name');
    setSortDirection('asc');
  };

  // 페이지 변경
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // 페이지네이션 계산
  const totalPages = Math.ceil(totalCount / 10);
  const startItem = (currentPage - 1) * 10 + 1;
  const endItem = Math.min(currentPage * 10, totalCount);

  useEffect(() => {
    fetchDocuments();
  }, [currentPage, sortField, sortDirection]);

  // 디버깅용 로그
  useEffect(() => {
    console.log('documents 상태 변경:', { length: documents.length, documents });
  }, [documents]);

  // 상세 페이지로 이동
  const handleDocumentClick = (documentId: string) => {
    setSelectedDocumentId(documentId);
  };

  // 목록으로 돌아가기
  const handleBackToList = (shouldRefresh?: boolean) => {
    setSelectedDocumentId(null);
    setIsCreateMode(false);
    
    // 목록 리프레시가 필요한 경우
    if (shouldRefresh) {
      fetchDocuments();
    }
  };

  // 문서 생성 모드로 이동
  const handleCreateDocument = () => {
    setIsCreateMode(true);
    setSelectedDocumentId('create');
  };

  // 문서 삭제
  const handleDeleteDocument = async (documentId: string) => {
    try {
      await deleteDocument(documentId);
      // 삭제 후 목록 새로고침
      fetchDocuments();
    } catch (error) {
      console.error('문서 삭제 실패:', error);
    }
  };

  // 상세 페이지가 선택된 경우 상세 페이지 렌더링
  if (selectedDocumentId) {
    return (
      <DocumentDetailPage 
        documentId={selectedDocumentId} 
        onBack={handleBackToList}
        isCreateMode={isCreateMode}
      />
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">지식 관리</h1>
        <p className="text-gray-600">문서의 청킹 및 관리 작업을 수행합니다.</p>
      </div>

      {/* 검색 및 필터링 섹션 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">문서 ID</label>
            <Input
              placeholder="문서 ID 입력"
              value={filters.document_id || ''}
              onChange={(e) => setFilters({ ...filters, document_id: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">청킹 ID</label>
            <Input
              placeholder="청킹 ID 입력"
              value={filters.chunk_id || ''}
              onChange={(e) => setFilters({ ...filters, chunk_id: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">문서명</label>
            <Input
              placeholder="문서명 입력"
              value={filters.document_name || ''}
              onChange={(e) => setFilters({ ...filters, document_name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">청킹 내용</label>
            <Input
              placeholder="청킹 내용 입력"
              value={filters.chunk_content || ''}
              onChange={(e) => setFilters({ ...filters, chunk_content: e.target.value })}
            />
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">경로</label>
            <Input
              placeholder="경로 입력"
              value={filters.path || ''}
              onChange={(e) => setFilters({ ...filters, path: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">상태</label>
            <Select
              value={filters.status || undefined}
              onValueChange={(value) => setFilters({ ...filters, status: value === 'all' ? undefined : value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="전체" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">전체</SelectItem>
                <SelectItem value="pending">대기중</SelectItem>
                <SelectItem value="indexed">인덱싱됨</SelectItem>
                <SelectItem value="deleted">삭제됨</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="h-4 w-4 mr-2" />
            초기화
          </Button>
          <Button onClick={handleSearch}>
            <Search className="h-4 w-4 mr-2" />
            조회
          </Button>
        </div>
      </div>

      {/* 문서 생성 버튼 */}
      <div className="flex justify-end mb-4">
        <Button onClick={handleCreateDocument} variant="default">
          <Plus className="h-4 w-4 mr-2" />
          문서 생성
        </Button>
      </div>

      {/* 문서 목록 테이블 */}
      <div className="bg-white rounded-lg shadow">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('document_name')}
                >
                  <div className="flex items-center gap-2">
                    문서명
                    {renderSortIcon('document_name')}
                  </div>
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('chunk_size')}
                >
                  <div className="flex items-center gap-2">
                    청킹 사이즈
                    {renderSortIcon('chunk_size')}
                  </div>
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('overlap_size')}
                >
                  <div className="flex items-center gap-2">
                    오버랩 사이즈
                    {renderSortIcon('overlap_size')}
                  </div>
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('method')}
                >
                  <div className="flex items-center gap-2">
                    청킹 방법
                    {renderSortIcon('method')}
                  </div>
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center gap-2">
                    상태
                    {renderSortIcon('status')}
                  </div>
                </TableHead>
                <TableHead className="w-20">작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    로딩 중...
                  </TableCell>
                </TableRow>
              ) : documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    조회된 문서가 없습니다.
                  </TableCell>
                </TableRow>
              ) : (
                documents.map((doc) => (
                  <TableRow 
                    key={doc.id}
                    className="cursor-pointer hover:bg-gray-50"
                    onDoubleClick={() => handleDocumentClick(doc.id)}
                  >
                    <TableCell className="font-medium">{doc.name}</TableCell>
                    <TableCell>{doc.chunk_size || '-'}</TableCell>
                    <TableCell>{doc.overlap_size || '-'}</TableCell>
                    <TableCell>{doc.method || '-'}</TableCell>
                    <TableCell>
                      <Badge 
                        variant={
                          doc.status === 'indexed' ? 'default' : 
                          doc.status === 'pending' ? 'secondary' : 
                          'destructive'
                        }
                        className={
                          doc.status === 'indexed' ? 'bg-green-100 text-green-800' : 
                          doc.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-red-100 text-red-800'
                        }
                      >
                        {doc.status === 'pending' ? '대기중' : 
                         doc.status === 'indexed' ? '인덱싱됨' : 
                         doc.status === 'deleted' ? '삭제됨' : doc.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            className="text-red-600 hover:text-red-800 hover:bg-red-50"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>문서 삭제</AlertDialogTitle>
                            <AlertDialogDescription>
                              정말로 이 문서를 삭제하시겠습니까?<br />
                              <strong>"{doc.name}"</strong><br />
                              이 작업은 되돌릴 수 없습니다.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>취소</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteDocument(doc.id)}
                              className="bg-red-600 hover:bg-red-700"
                            >
                              삭제
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* 페이지네이션 */}
        <div className="flex items-center justify-between px-6 py-4 border-t">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(1)}
              disabled={currentPage === 1}
            >
              &lt;&lt;
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              &lt;
            </Button>
            
            {/* 페이지 번호들 */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
              if (pageNum > totalPages) return null;
              
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === currentPage ? "default" : "outline"}
                  size="sm"
                  onClick={() => handlePageChange(pageNum)}
                  className={pageNum === currentPage ? "bg-blue-600 text-white" : ""}
                >
                  {pageNum}
                </Button>
              );
            })}
            
            {totalPages > 5 && (
              <>
                <span className="px-2">...</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(totalPages)}
                >
                  {totalPages}
                </Button>
              </>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              &gt;
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(totalPages)}
              disabled={currentPage === totalPages}
            >
              &gt;&gt;
            </Button>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">페이지당</span>
              <Select
                value="10"
                onValueChange={(value) => {
                  setFilters({ ...filters, limit: parseInt(value) });
                  setCurrentPage(1);
                }}
              >
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="text-sm text-gray-600">
              {totalCount}개 중 {startItem}-{endItem} 항목 (페이지 {currentPage}/{totalPages})
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
