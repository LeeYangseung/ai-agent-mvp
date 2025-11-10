"use client"

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Search, Plus, Edit, Trash2, Check } from "lucide-react";
import { getCollections, createCollection, updateCollection, deleteCollection, Collection } from "@/lib/api";
import { useToast } from "../hooks/use-toast";

interface CollectionManagerDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (collectionId: string, collectionName: string) => void;
}

export function CollectionManagerDialog({ isOpen, onClose, onSelect }: CollectionManagerDialogProps) {
  const { toast } = useToast();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  
  // 생성/수정 모드
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingCollection, setEditingCollection] = useState<Partial<Collection> | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [saving, setSaving] = useState(false);

  // 컬렉션 목록 조회
  const fetchCollections = async () => {
    setLoading(true);
    try {
      const response = await getCollections({ 
        collection_name: searchTerm || undefined,
        sort: "created_at:desc" 
      });
      const collectionData = response.data?.collections || [];
      setCollections(collectionData);
    } catch (error: any) {
      console.error('컬렉션 조회 실패:', error);
      toast({
        title: "오류",
        description: error.response?.data?.message || "컬렉션 목록을 불러오지 못했습니다.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchCollections();
    }
  }, [isOpen, searchTerm]);

  // 새 컬렉션 생성 모드
  const handleCreateNew = () => {
    setIsEditMode(true);
    setEditingCollection(null);
    setEditName("");
    setEditDescription("");
  };

  // 컬렉션 수정 모드
  const handleEdit = (collection: Collection) => {
    setIsEditMode(true);
    setEditingCollection(collection);
    setEditName(collection.name);
    setEditDescription(collection.description || "");
  };

  // 컬렉션 저장 (생성 또는 수정)
  const handleSave = async () => {
    if (!editName.trim()) {
      toast({
        title: "오류",
        description: "컬렉션 이름을 입력해주세요.",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      if (editingCollection?.id) {
        // 수정
        await updateCollection(editingCollection.id, {
          name: editName,
          description: editDescription
        });
        toast({
          title: "수정 완료",
          description: "컬렉션이 성공적으로 수정되었습니다.",
        });
      } else {
        // 생성
        await createCollection({
          name: editName,
          description: editDescription
        });
        toast({
          title: "생성 완료",
          description: "컬렉션이 성공적으로 생성되었습니다.",
        });
      }
      
      setIsEditMode(false);
      setEditingCollection(null);
      fetchCollections();
    } catch (error: any) {
      console.error('컬렉션 저장 실패:', error);
      toast({
        title: "오류",
        description: error.response?.data?.message || "컬렉션 저장에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  // 컬렉션 삭제
  const handleDelete = async (collection: Collection) => {
    if (!window.confirm(`"${collection.name}" 컬렉션을 삭제하시겠습니까?\n\n⚠️ 주의: 이 컬렉션에 문서가 있으면 삭제할 수 없습니다.`)) {
      return;
    }

    try {
      await deleteCollection(collection.id);
      toast({
        title: "삭제 완료",
        description: "컬렉션이 성공적으로 삭제되었습니다.",
      });
      fetchCollections();
      if (selectedCollectionId === collection.id) {
        setSelectedCollectionId(null);
      }
    } catch (error: any) {
      console.error('컬렉션 삭제 실패:', error);
      toast({
        title: "삭제 실패",
        description: error.response?.data?.message || "컬렉션 삭제에 실패했습니다.",
        variant: "destructive",
      });
    }
  };

  // 컬렉션 선택 및 확인
  const handleConfirm = () => {
    const selectedCollection = collections.find(c => c.id === selectedCollectionId);
    if (selectedCollection) {
      onSelect(selectedCollection.id, selectedCollection.name);
      onClose();
    } else {
      toast({
        title: "오류",
        description: "컬렉션을 선택해주세요.",
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>컬렉션 관리</DialogTitle>
          <DialogDescription>
            컬렉션을 생성, 수정, 삭제하거나 선택할 수 있습니다.
          </DialogDescription>
        </DialogHeader>

        {!isEditMode ? (
          // 목록 보기 모드
          <>
            <div className="flex gap-2 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="컬렉션 이름으로 검색..."
                  className="pl-10"
                />
              </div>
              <Button onClick={handleCreateNew}>
                <Plus className="h-4 w-4 mr-2" />
                새 컬렉션
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto border rounded-lg">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-gray-500">로딩 중...</div>
                </div>
              ) : collections.length === 0 ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-gray-500">컬렉션이 없습니다.</div>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">선택</TableHead>
                      <TableHead>이름</TableHead>
                      <TableHead>설명</TableHead>
                      <TableHead className="w-24 text-center">문서 수</TableHead>
                      <TableHead className="w-32 text-center">작업</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {collections.map((collection) => (
                      <TableRow 
                        key={collection.id}
                        className={selectedCollectionId === collection.id ? "bg-blue-50" : ""}
                      >
                        <TableCell>
                          <input
                            type="radio"
                            name="collection"
                            checked={selectedCollectionId === collection.id}
                            onChange={() => setSelectedCollectionId(collection.id)}
                            className="cursor-pointer"
                          />
                        </TableCell>
                        <TableCell className="font-medium">{collection.name}</TableCell>
                        <TableCell className="text-gray-600">
                          {collection.description || "-"}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="secondary">
                            {collection.document_count || 0}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1 justify-center">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(collection)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(collection)}
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={onClose}>
                취소
              </Button>
              <Button onClick={handleConfirm} disabled={!selectedCollectionId}>
                <Check className="h-4 w-4 mr-2" />
                선택
              </Button>
            </DialogFooter>
          </>
        ) : (
          // 생성/수정 모드
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                컬렉션 이름 *
              </label>
              <Input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder="컬렉션 이름을 입력하세요"
                maxLength={255}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                설명
              </label>
              <Textarea
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="컬렉션 설명을 입력하세요 (선택사항)"
                rows={3}
                maxLength={500}
              />
            </div>

            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => {
                  setIsEditMode(false);
                  setEditingCollection(null);
                }}
              >
                취소
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? "저장 중..." : editingCollection ? "수정" : "생성"}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

