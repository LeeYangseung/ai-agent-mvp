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
  const [method, setMethod] = useState("length");
  const [chunkSize, setChunkSize] = useState("500");
  const [overlapSize, setOverlapSize] = useState("100");
  const [breakpointThresholdType, setBreakpointThresholdType] = useState(""); // length는 사용 안함
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

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

  // 청킹 방법 변경 시 기본값 설정
  const handleMethodChange = (newMethod: string) => {
    setMethod(newMethod);
    
    // 각 방법에 따른 기본값 설정 및 불필요한 값 초기화
    if (newMethod === "length") {
      setChunkSize("500");
      setOverlapSize("100");
      setBreakpointThresholdType(""); // semantic 파라미터 초기화
    } else if (newMethod === "semantic") {
      setChunkSize(""); // length 파라미터 초기화
      setOverlapSize(""); // length 파라미터 초기화
      setBreakpointThresholdType("percentile");
    } else if (newMethod === "hybrid") {
      setChunkSize("1000");
      setOverlapSize("100");
      setBreakpointThresholdType("percentile");
    } else if (newMethod === "paragraph") {
      // paragraph는 추가 설정 불필요 - 모두 초기화
      setChunkSize("");
      setOverlapSize("");
      setBreakpointThresholdType("");
    }
  };

  // 유효성 검사
  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!editedName.trim()) {
      newErrors.name = "문서명을 입력해주세요";
    }
    
    // 청킹 방법에 따른 필수값 검증
    if (method === "length" || method === "hybrid") {
      if (!chunkSize.trim()) {
        newErrors.chunkSize = "청킹 사이즈를 입력해주세요";
      } else if (parseInt(chunkSize) <= 0) {
        newErrors.chunkSize = "청킹 사이즈는 0보다 커야 합니다";
      }
      if (!overlapSize.trim()) {
        newErrors.overlapSize = "오버랩 사이즈를 입력해주세요";
      } else if (parseInt(overlapSize) < 0) {
        newErrors.overlapSize = "오버랩 사이즈는 0 이상이어야 합니다";
      }
      if (parseInt(overlapSize) >= parseInt(chunkSize)) {
        newErrors.overlapSize = "오버랩 사이즈는 청킹 사이즈보다 작아야 합니다";
      }
    }
    
    if (method === "semantic" || method === "hybrid") {
      if (!breakpointThresholdType) {
        newErrors.breakpointThresholdType = "임계값 유형을 선택해주세요";
      }
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
        formData.append('method', method);
        
        // 청킹 방법에 따라 필요한 파라미터만 추가
        if (method === "length") {
          // length: chunk_size, overlap_size만 필요
          if (chunkSize) formData.append('chunk_size', chunkSize);
          if (overlapSize) formData.append('overlap_size', overlapSize);
        } else if (method === "semantic") {
          // semantic: breakpoint_threshold_type만 필요
          if (breakpointThresholdType) {
            formData.append('breakpoint_threshold_type', breakpointThresholdType);
          }
        } else if (method === "hybrid") {
          // hybrid: 모두 필요
          if (chunkSize) formData.append('chunk_size', chunkSize);
          if (overlapSize) formData.append('overlap_size', overlapSize);
          if (breakpointThresholdType) {
            formData.append('breakpoint_threshold_type', breakpointThresholdType);
          }
        }
        // paragraph: 추가 파라미터 불필요
        
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

            {/* 청킹 방법 */}
            {isCreateMode && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  청킹 방법
                </label>
                <Select value={method} onValueChange={handleMethodChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="length">Length (길이 기반)</SelectItem>
                    <SelectItem value="semantic">Semantic (의미 기반)</SelectItem>
                    <SelectItem value="hybrid">Hybrid (하이브리드)</SelectItem>
                    <SelectItem value="paragraph">Paragraph (문단 기반)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">
                  {method === "length" && "고정된 길이로 문서를 분할합니다. \n💡 추천: 짧은 일반 텍스트"}
                  {method === "semantic" && "의미를 기반으로 문서를 분할합니다. (임베딩 사용) \n💡 추천: 리포트, 대화 데이터"}
                  {method === "hybrid" && "길이와 의미를 결합하여 문서를 분할합니다. \n💡 추천: 긴 보고서나 리포트"}
                  {method === "paragraph" && "문단 구조를 기반으로 문서를 분할합니다. \n💡 추천: 위키, 기술문서, 매뉴얼, 정책문서"}
                </p>
              </div>
            )}

            {/* 고급 설정 토글 */}
            {isCreateMode && method !== "paragraph" && (
              <div>
                <button
                  type="button"
                  onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                  className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-800"
                >
                  {showAdvancedSettings ? "▼" : "▶"} 고급 설정
                </button>
              </div>
            )}

            {/* 고급 설정 - Length/Hybrid 방법 */}
            {isCreateMode && showAdvancedSettings && (method === "length" || method === "hybrid") && (
              <>
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
                  <p className="text-xs text-gray-500 mt-1">
                    {method === "length" && "기본값: 500 (각 청크의 최대 문자 수)"}
                    {method === "hybrid" && "기본값: 1000 (각 청크의 최대 문자 수)"}
                  </p>
                </div>

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
                  <p className="text-xs text-gray-500 mt-1">
                    기본값: 100 (청크 간 중복 문자 수)
                  </p>
                </div>
              </>
            )}

            {/* 고급 설정 - Semantic/Hybrid 방법 */}
            {isCreateMode && showAdvancedSettings && (method === "semantic" || method === "hybrid") && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  임계값 유형
                </label>
                <Select 
                  value={breakpointThresholdType} 
                  onValueChange={setBreakpointThresholdType}
                >
                  <SelectTrigger className={errors.breakpointThresholdType ? 'border-red-500' : ''}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="percentile">Percentile (백분위수)</SelectItem>
                    <SelectItem value="standard_deviation">Standard Deviation (표준편차)</SelectItem>
                    <SelectItem value="interquartile">Interquartile (사분위수)</SelectItem>
                  </SelectContent>
                </Select>
                {errors.breakpointThresholdType && (
                  <p className="text-red-500 text-sm mt-1">{errors.breakpointThresholdType}</p>
                )}
                <div className="text-xs text-gray-500 mt-1 space-y-1">
                  {breakpointThresholdType === "percentile" && (
                    <p>✓ Percentile: 의미 차이의 상위 95%를 기준으로 분할. 균형잡힌 청크 생성에 적합 (기본 권장)</p>
                  )}
                  {breakpointThresholdType === "standard_deviation" && (
                    <p>✓ Standard Deviation: 평균에서 3 표준편차 이상 벗어난 지점에서 분할. 명확한 주제 전환 감지에 적합</p>
                  )}
                  {breakpointThresholdType === "interquartile" && (
                    <p>✓ Interquartile: 사분위수 범위를 기준으로 분할. 이상치에 강건하며 안정적인 청크 생성에 적합</p>
                  )}
                </div>
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
                <div className="text-gray-900">
                  {document?.method === 'length' ? 'Length (길이 기반)' :
                   document?.method === 'semantic' ? 'Semantic (의미 기반)' :
                   document?.method === 'hybrid' ? 'Hybrid (하이브리드)' :
                   document?.method === 'paragraph' ? 'Paragraph (문단 기반)' :
                   document?.method || '-'}
                </div>
              </div>
            )}

            {/* 임계값 유형 (Semantic/Hybrid인 경우) */}
            {!isCreateMode && (document?.method === 'semantic' || document?.method === 'hybrid') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  임계값 유형
                </label>
                <div className="text-gray-900">
                  {(document as any)?.breakpoint_threshold_type === 'percentile' ? 'Percentile (백분위수)' :
                   (document as any)?.breakpoint_threshold_type === 'standard_deviation' ? 'Standard Deviation (표준편차)' :
                   (document as any)?.breakpoint_threshold_type === 'interquartile' ? 'Interquartile (사분위수)' :
                   (document as any)?.breakpoint_threshold_type || '-'}
                </div>
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
