"use client"

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Save, X, Upload } from "lucide-react";
import { getDocumentDetail, updateDocument, createDocument, DocumentDetail, Chunk } from "@/lib/api";
import { useToast } from "../hooks/use-toast";

interface DocumentDetailPageProps {
  documentId: string;
  onBack: (shouldRefresh?: boolean) => void;
  isCreateMode?: boolean;
}

export function DocumentDetailPage({ documentId, onBack, isCreateMode = false }: DocumentDetailPageProps) {
  const { toast } = useToast();
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [editedName, setEditedName] = useState("");
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  
  // 생성 모드용 상태
  const [chunkSize, setChunkSize] = useState("");
  const [overlapSize, setOverlapSize] = useState("");
  const [method, setMethod] = useState("overlap");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 문서 상세 정보 조회
  const fetchDocumentDetail = async () => {
    setLoading(true);
    try {
      const response = await getDocumentDetail(documentId);
      console.log('문서 상세 응답:', response);
      
      const documentData = response.data?.document || response.data || response;
      console.log('문서 데이터:', documentData);
      setDocument(documentData);
      setEditedName(documentData.name || "");
      setHasChanges(false);
    } catch (error) {
      console.error('문서 상세 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 문서명 변경 감지
  const handleNameChange = (value: string) => {
    setEditedName(value);
    setHasChanges(value !== document?.name);
  };

  // 유효성 검사
  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!editedName.trim()) {
      newErrors.name = "문서명을 입력해주세요";
    }
    if (!chunkSize.trim()) {
      newErrors.chunkSize = "청킹 사이즈를 입력해주세요";
    }
    if (!overlapSize.trim()) {
      newErrors.overlapSize = "오버랩 사이즈를 입력해주세요";
    }
    if (!uploadedFile) {
      newErrors.file = "파일을 업로드해주세요";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 문서 수정
  const handleSave = async () => {
    if (isCreateMode) {
      if (!validateForm()) return;
      
      setSaving(true);
      try {
        const formData = new FormData();
        formData.append('name', editedName);
        formData.append('chunk_size', chunkSize);
        formData.append('overlap_size', overlapSize);
        formData.append('method', method);
        formData.append('file', uploadedFile!);
        formData.append('created_by', 'admin');
        
        const response = await createDocument(formData);
        
        // 백엔드 메시지를 토스트로 표시
        toast({
          title: "문서 생성 성공",
          description: response.message || "문서가 정상적으로 생성되었습니다.",
        });
        
        // 목록 리프레시와 함께 목록으로 돌아가기
        onBack(true);
      } catch (error: any) {
        console.error('문서 생성 실패:', error);
        toast({
          title: "오류",
          description: error.response?.data?.message || "문서 생성에 실패했습니다.",
          variant: "destructive",
        });
      } finally {
        setSaving(false);
      }
    } else {
      if (!document || !hasChanges) return;
      
      setSaving(true);
      try {
        const response = await updateDocument(documentId, { 
          name: editedName,
          updated_by: "admin"
        });
        
        // 백엔드 메시지를 토스트로 표시
        toast({
          title: "문서 수정 성공",
          description: response.message || "문서가 정상적으로 수정되었습니다.",
        });
        
        setDocument({ ...document, name: editedName });
        setHasChanges(false);
      } catch (error: any) {
        console.error('문서 수정 실패:', error);
        toast({
          title: "오류",
          description: error.response?.data?.message || "문서 수정에 실패했습니다.",
          variant: "destructive",
        });
      } finally {
        setSaving(false);
      }
    }
  };

  useEffect(() => {
    if (!isCreateMode && documentId !== 'create') {
      fetchDocumentDetail();
    }
  }, [documentId, isCreateMode]);

  // 브라우저 뒤로가기 처리
  useEffect(() => {
    const handlePopState = () => {
      onBack();
    };

    window.addEventListener('popstate', handlePopState);
    
    // 현재 페이지를 히스토리에 추가
    window.history.pushState({ documentId }, '', window.location.href);

    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [onBack]);

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">로딩 중...</div>
        </div>
      </div>
    );
  }

  if (!isCreateMode && !document) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">문서를 찾을 수 없습니다.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">
          {isCreateMode ? '문서 생성' : '문서 상세'}
        </h1>
        <Button variant="outline" onClick={() => onBack()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          뒤로가기
        </Button>
      </div>

      <div className="space-y-6">
        {/* 문서 정보 */}
        <Card>
          <CardHeader>
            <CardTitle>문서 정보</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 문서명 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                문서명
              </label>
              <div className="relative">
                <Input
                  value={editedName}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="문서명을 입력하세요"
                  className={`pr-16 ${errors.name ? 'border-red-500' : ''}`}
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-gray-500">
                  {editedName.length}/1000
                </div>
              </div>
              {errors.name && (
                <p className="text-red-500 text-sm mt-1">{errors.name}</p>
              )}
            </div>

            {/* 청킹 사이즈 */}
            {isCreateMode && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  청킹 사이즈
                </label>
                <Input
                  value={chunkSize}
                  onChange={(e) => setChunkSize(e.target.value)}
                  placeholder="청킹 사이즈를 입력하세요"
                  className={errors.chunkSize ? 'border-red-500' : ''}
                  type="number"
                />
                {errors.chunkSize && (
                  <p className="text-red-500 text-sm mt-1">{errors.chunkSize}</p>
                )}
              </div>
            )}

            {/* 오버랩 사이즈 */}
            {isCreateMode && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  오버랩 사이즈
                </label>
                <Input
                  value={overlapSize}
                  onChange={(e) => setOverlapSize(e.target.value)}
                  placeholder="오버랩 사이즈를 입력하세요"
                  className={errors.overlapSize ? 'border-red-500' : ''}
                  type="number"
                />
                {errors.overlapSize && (
                  <p className="text-red-500 text-sm mt-1">{errors.overlapSize}</p>
                )}
              </div>
            )}

            {/* 청킹 방법 */}
            {isCreateMode && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  청킹 방법
                </label>
                <Select value={method} onValueChange={setMethod}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="overlap">overlap</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* 상태 */}
            {!isCreateMode && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  상태
                </label>
                <Badge 
                  variant={
                    document?.status === 'indexed' ? 'default' : 
                    document?.status === 'pending' ? 'secondary' : 
                    'destructive'
                  }
                  className={
                    document?.status === 'indexed' ? 'bg-green-100 text-green-800' : 
                    document?.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                    'bg-red-100 text-red-800'
                  }
                >
                  {document?.status === 'pending' ? '대기중' : 
                   document?.status === 'indexed' ? '인덱싱됨' : 
                   document?.status === 'deleted' ? '삭제됨' : document?.status}
                </Badge>
              </div>
            )}

            {/* 경로 */}
            {!isCreateMode && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  경로
                </label>
                <div className="text-gray-900 text-sm break-all">{document?.path || '-'}</div>
              </div>
            )}

            {/* 청킹 설정 */}
            {!isCreateMode && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    청킹 사이즈
                  </label>
                  <div className="text-gray-900">{document?.chunk_size || '-'}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    오버랩 사이즈
                  </label>
                  <div className="text-gray-900">{document?.overlap_size || '-'}</div>
                </div>
              </div>
            )}

            {/* 청킹 방법 */}
            {!isCreateMode && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  청킹 방법
                </label>
                <div className="text-gray-900">{document?.method || '-'}</div>
              </div>
            )}

            {/* 생성일/수정일 */}
            {!isCreateMode && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    생성일
                  </label>
                  <div className="text-gray-900 text-sm">
                    {document?.created_at ? new Date(document.created_at).toLocaleString('ko-KR') : '-'}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    수정일
                  </label>
                  <div className="text-gray-900 text-sm">
                    {document?.updated_at ? new Date(document.updated_at).toLocaleString('ko-KR') : '-'}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 파일 업로드 또는 청크 목록 */}
        {isCreateMode ? (
          <Card>
            <CardHeader>
              <CardTitle>파일 업로드</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    파일 선택
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="file"
                      accept=".pdf,.txt"
                      onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                      className="hidden"
                      id="file-upload"
                    />
                    <label
                      htmlFor="file-upload"
                      className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50"
                    >
                      <Upload className="h-4 w-4" />
                      파일 선택
                    </label>
                    {uploadedFile && (
                      <span className="text-sm text-gray-600">
                        {uploadedFile.name}
                      </span>
                    )}
                  </div>
                  {errors.file && (
                    <p className="text-red-500 text-sm mt-1">{errors.file}</p>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  지원 형식: PDF, TXT
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>청크 목록 ({document?.chunks?.length || 0}개)</CardTitle>
            </CardHeader>
            <CardContent>
              {document?.chunks && document.chunks.length > 0 ? (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {document.chunks.map((chunk: Chunk, index: number) => (
                    <div key={chunk.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">
                          청크 #{chunk.chunk_index + 1}
                        </span>
                        <span className="text-xs text-gray-500">
                          {chunk.created_at ? new Date(chunk.created_at).toLocaleString('ko-KR') : ''}
                        </span>
                      </div>
                      <div className="text-sm text-gray-900 whitespace-pre-wrap">
                        {chunk.content}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  청크가 없습니다.
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* 저장 버튼 */}
      <div className="flex justify-end mt-6">
        <Button 
          onClick={handleSave}
          disabled={
            isCreateMode 
              ? saving || editedName.length > 1000
              : !hasChanges || saving || editedName.length > 1000
          }
          className="min-w-[120px]"
        >
          <Save className="h-4 w-4 mr-2" />
          {saving ? '저장 중...' : isCreateMode ? '생성' : '저장'}
        </Button>
      </div>
    </div>
  );
}
