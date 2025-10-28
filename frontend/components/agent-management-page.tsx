"use client"

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ChevronUp, ChevronDown, Search, RotateCcw, Trash2, Plus, Edit } from "lucide-react";
import { getGraphs, Graph, GraphFilters, deleteGraph } from "@/lib/api";
import { GraphEditor } from "./graph-editor";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

type SortField = 'name' | 'version' | 'created_at' | 'updated_at';
type SortDirection = 'asc' | 'desc';

// 백엔드 필드명 매핑
const FIELD_MAPPING: Record<SortField, string> = {
  name: 'name',
  version: 'version', 
  created_at: 'created_at',
  updated_at: 'updated_at'
};

export function AgentManagementPage() {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<GraphFilters>({
    page: 0,
    size: 10
  });
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedGraphId, setSelectedGraphId] = useState<string | null>(null);
  const [isCreateMode, setIsCreateMode] = useState(false);
  const [isNewGraphDialogOpen, setIsNewGraphDialogOpen] = useState(false);
  const [newGraphData, setNewGraphData] = useState({
    name: '',
    description: '',
    version: 1
  });

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

  // 그래프 목록 조회
  const fetchGraphs = async () => {
    setLoading(true);
    try {
      const backendField = FIELD_MAPPING[sortField];
      const sortParam = `${backendField}:${sortDirection}`;
      
      const backendPage = currentPage - 1;
      
      const response = await getGraphs({
        ...filters,
        sort: sortParam,
        page: backendPage,
        size: 10
      });
      
      console.log('그래프 API 응답:', response);
      
      setGraphs(response.data?.graphs || []);
      setTotalCount(response.pagination?.total_count || 0);
    } catch (error) {
      console.error('그래프 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 검색/필터링
  const handleSearch = () => {
    setCurrentPage(1);
    fetchGraphs();
  };

  // 필터 초기화
  const handleReset = () => {
    setFilters({
      page: 0,
      size: 10
    });
    setCurrentPage(1);
    setSortField('name');
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
    fetchGraphs();
  }, [currentPage, sortField, sortDirection]);

  // 상세 페이지로 이동
  const handleGraphClick = (graphId: string) => {
    setSelectedGraphId(graphId);
  };

  // 목록으로 돌아가기
  const handleBackToList = (shouldRefresh?: boolean) => {
    setSelectedGraphId(null);
    setIsCreateMode(false);
    
    if (shouldRefresh) {
      fetchGraphs();
    }
  };

  // 새 그래프 생성 모드로 이동
  const handleCreateGraph = () => {
    setIsCreateMode(true);
    setSelectedGraphId('create');
  };

  // 그래프 삭제
  const handleDeleteGraph = async (graphId: string) => {
    try {
      await deleteGraph(graphId);
      fetchGraphs();
    } catch (error) {
      console.error('그래프 삭제 실패:', error);
    }
  };

  // 새 그래프 생성 다이얼로그 처리
  const handleCreateNewGraph = () => {
    setIsNewGraphDialogOpen(true);
  };

  const handleConfirmCreateGraph = () => {
    setIsNewGraphDialogOpen(false);
    setIsCreateMode(true);
    setSelectedGraphId('create');
  };

  // 상세 페이지가 선택된 경우 그래프 에디터 렌더링
  if (selectedGraphId) {
    return (
      <GraphEditor 
        graphId={selectedGraphId} 
        onBack={handleBackToList}
        isCreateMode={isCreateMode}
        initialGraphData={isCreateMode ? newGraphData : undefined}
      />
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        {/* <h1 className="text-2xl font-bold text-gray-800 mb-2">AI Agent 관리</h1> */}
        <p className="text-gray-600">AI Agent 그래프의 생성 및 관리 작업을 수행합니다.</p>
      </div>

      {/* 검색 및 필터링 섹션 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">그래프 이름</label>
            <Input
              placeholder="그래프 이름 입력"
              value={filters.name || ''}
              onChange={(e) => setFilters({ ...filters, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">설명</label>
            <Input
              placeholder="설명 입력"
              value={filters.description || ''}
              onChange={(e) => setFilters({ ...filters, description: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">버전</label>
            <Input
              placeholder="버전 입력"
              type="number"
              value={filters.version || ''}
              onChange={(e) => setFilters({ ...filters, version: e.target.value ? parseInt(e.target.value) : undefined })}
            />
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

      {/* 그래프 생성 버튼 */}
      <div className="flex justify-end mb-4">
        <Button onClick={handleCreateNewGraph} variant="default">
          <Plus className="h-4 w-4 mr-2" />
          Agent 생성
        </Button>
      </div>

      {/* 그래프 목록 테이블 */}
      <div className="bg-white rounded-lg shadow">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('name')}
                >
                  <div className="flex items-center gap-2">
                    그래프 이름
                    {renderSortIcon('name')}
                  </div>
                </TableHead>
                <TableHead>설명</TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('version')}
                >
                  <div className="flex items-center gap-2">
                    버전
                    {renderSortIcon('version')}
                  </div>
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('created_at')}
                >
                  <div className="flex items-center gap-2">
                    생성일
                    {renderSortIcon('created_at')}
                  </div>
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('updated_at')}
                >
                  <div className="flex items-center gap-2">
                    수정일
                    {renderSortIcon('updated_at')}
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
              ) : graphs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    조회된 그래프가 없습니다.
                  </TableCell>
                </TableRow>
              ) : (
                graphs.map((graph) => (
                  <TableRow 
                    key={graph.id}
                    className="cursor-pointer hover:bg-gray-50"
                    onDoubleClick={() => handleGraphClick(graph.id)}
                  >
                    <TableCell className="font-medium">{graph.name}</TableCell>
                    <TableCell>{graph.description || '-'}</TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        v{graph.version || 1}
                      </Badge>
                    </TableCell>
                    <TableCell>{graph.created_at ? new Date(graph.created_at).toLocaleDateString() : '-'}</TableCell>
                    <TableCell>{graph.updated_at ? new Date(graph.updated_at).toLocaleDateString() : '-'}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleGraphClick(graph.id);
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
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
                              <AlertDialogTitle>그래프 삭제</AlertDialogTitle>
                              <AlertDialogDescription>
                                정말로 이 그래프를 삭제하시겠습니까?<br />
                                <strong>"{graph.name}"</strong><br />
                                이 작업은 되돌릴 수 없습니다.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>취소</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDeleteGraph(graph.id)}
                                className="bg-red-600 hover:bg-red-700"
                              >
                                삭제
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
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
                  setFilters({ ...filters, size: parseInt(value) });
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

      {/* 새 그래프 생성 다이얼로그 */}
      <Dialog open={isNewGraphDialogOpen} onOpenChange={setIsNewGraphDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>AI Agent 생성</DialogTitle>
            <DialogDescription>
              새로운 AI Agent 그래프를 생성하기 위한 기본 정보를 입력해주세요.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">
                이름
              </Label>
              <Input
                id="name"
                value={newGraphData.name}
                onChange={(e) => setNewGraphData({ ...newGraphData, name: e.target.value })}
                placeholder="그래프 이름을 입력하세요"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description">
                설명
              </Label>
              <Textarea
                id="description"
                value={newGraphData.description}
                onChange={(e) => setNewGraphData({ ...newGraphData, description: e.target.value })}
                placeholder="그래프 설명을 입력하세요"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="version">
                버전
              </Label>
              <Input
                id="version"
                type="number"
                value={newGraphData.version}
                onChange={(e) => setNewGraphData({ ...newGraphData, version: parseInt(e.target.value) || 1 })}
                placeholder="1"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsNewGraphDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleConfirmCreateGraph} disabled={!newGraphData.name.trim()}>
              생성
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
