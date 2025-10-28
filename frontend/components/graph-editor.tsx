"use client"

import React, { useCallback, useState, useEffect } from "react";
import ReactFlow, {
  Background,
  Controls,
  addEdge,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import BaseNode from "./node";
import { runGraph, getGraph, createGraph, updateGraph } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { GraphSnippet, graphSnippets } from "./graph-snippet";
import { ArrowLeft, Save } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const nodeTypes = { BaseNode };

// 💬 메시지 타입
type ChatMessage = {
  role: "user" | "agent";
  content: string;
};

// ------------------------------------------------------------
// 그래프 정보 입력 팝업
// ------------------------------------------------------------
function GraphInfoDialog({
  isOpen,
  onClose,
  onConfirm,
  graphData,
  setGraphData,
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  graphData: { name: string; description: string; version: number };
  setGraphData: (data: { name: string; description: string; version: number }) => void;
}) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>그래프 정보 입력</DialogTitle>
          <DialogDescription>
            새 그래프의 이름과 설명을 입력해주세요.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">
              이름
            </Label>
            <Input
              id="name"
              value={graphData.name}
              onChange={(e) => setGraphData({ ...graphData, name: e.target.value })}
              placeholder="그래프 이름을 입력하세요"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="description">
              설명
            </Label>
            <Textarea
              id="description"
              value={graphData.description}
              onChange={(e) => setGraphData({ ...graphData, description: e.target.value })}
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
              value={graphData.version}
              onChange={(e) => setGraphData({ ...graphData, version: parseInt(e.target.value) || 1 })}
              placeholder="1"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            취소
          </Button>
          <Button onClick={onConfirm} disabled={!graphData.name.trim()}>
            확인
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ------------------------------------------------------------
// 채팅 UI
// ------------------------------------------------------------
function ChatPanel({
  messages,
  onSendMessage,
  isRunning,
}: {
  messages: ChatMessage[];
  onSendMessage: (msg: string) => void;
  isRunning: boolean;
}) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    onSendMessage(input);
    setInput("");
  };

  return (
    <div className="flex flex-col border-l bg-white w-80 h-full max-h-screen">
      <div className="flex-1 overflow-y-auto p-4 space-y-2 min-h-0 max-h-full">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`p-2 rounded-lg text-sm max-w-[80%] ${
              m.role === "user"
                ? "bg-blue-100 self-end ml-auto"
                : "bg-gray-100 self-start"
            }`}
          >
            {m.content}
          </div>
        ))}
      </div>

      {/* ✅ form 으로 감싸고 onSubmit에서만 handleSend 실행 */}
      <form
        onSubmit={(e) => {
          e.preventDefault(); // 기본 submit 막기
          handleSend();
        }}
        className="border-t p-2 flex space-x-2 flex-shrink-0 bg-white"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 border rounded px-2 py-1 text-sm"
        />
        <Button type="submit" disabled={isRunning}>
          {isRunning ? "..." : "Send"}
        </Button>
      </form>
    </div>
  );
}


// ------------------------------------------------------------
// 사이드바 컴포넌트
// ------------------------------------------------------------
function NodeSidebar({ 
  onAddNode, 
  onAddRetrievalNode, 
  onAddInputNode,
  onAddOutputNode,
  onAddConditionNode,
  onLoadSnippet 
}: { 
  onAddNode: () => void;
  onAddRetrievalNode: () => void;
  onAddInputNode: () => void;
  onAddOutputNode: () => void;
  onAddConditionNode: () => void;
  onLoadSnippet: (snippet: GraphSnippet) => void;
}) {
  return (
    <div className="p-4 border-r bg-gray-50 w-64">
      <h3 className="font-bold mb-4">Nodes</h3>
      <Button
        className="w-full mb-2"
        onClick={onAddInputNode}
      >
        📥 Add Input Node
      </Button>
      <Button
        className="w-full mb-2"
        onClick={onAddNode}
      >
        💬 Add Prompt Node
      </Button>
      <Button
        className="w-full mb-2"
        onClick={onAddRetrievalNode}
      >
        🔍 Add Retrieval Node
      </Button>
      <Button
        className="w-full mb-2"
        onClick={onAddConditionNode}
      >
        🔀 Add Condition Node
      </Button>
      <Button
        className="w-full mb-2"
        onClick={onAddOutputNode}
      >
        📤 Add Output Node
      </Button>
      
      <div className="mt-6">
        <h3 className="font-bold mb-4">Snippets</h3>
        <div className="space-y-2">
          {graphSnippets.map((snippet, index) => (
            <Button
              key={index}
              variant="outline"
              className="w-full text-left justify-start"
              onClick={() => onLoadSnippet(snippet)}
            >
              {snippet.name}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}

interface GraphEditorProps {
  graphId?: string;
  onBack?: () => void;
  isCreateMode?: boolean;
  initialGraphData?: {
    name: string;
    description: string;
    version: number;
  };
}

export function GraphEditor({ 
  graphId, 
  onBack, 
  isCreateMode = false, 
  initialGraphData 
}: GraphEditorProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [currentGraphData, setCurrentGraphData] = useState(initialGraphData);
  const [isGraphInfoDialogOpen, setIsGraphInfoDialogOpen] = useState(false);
  const [tempGraphData, setTempGraphData] = useState({
    name: '',
    description: '',
    version: 1
  });

  // 그래프 로드
  useEffect(() => {
    if (graphId && graphId !== 'create') {
      loadGraph(graphId);
    }
  }, [graphId]);

  const loadGraph = async (id: string) => {
    try {
      console.log('그래프 로드 시작:', id);
      const response = await getGraph(id);
      console.log('그래프 API 응답 전체:', response);
      
      // 응답 구조 확인: response.data.graph 또는 response.data
      const graph = response.data?.graph || response.data;
      console.log('그래프 데이터:', graph);
      
      if (graph && graph.nodes) {
        console.log('노드 개수:', graph.nodes.length);
        console.log('엣지 개수:', graph.edges?.length || 0);
        
        // 백엔드 노드 데이터를 ReactFlow 노드 형태로 변환
        const reactFlowNodes: Node[] = graph.nodes.map((nodeData: any, index: number) => {
          // 저장된 위치 정보가 있으면 사용, 없으면 기본 위치 사용
          const position = nodeData.position 
            ? { x: nodeData.position.x, y: nodeData.position.y }
            : { x: 100 + index * 300, y: 200 };
          
          console.log(`노드 ${nodeData.node_id} 위치:`, position, '저장된 위치:', nodeData.position);
          
          return {
            id: nodeData.node_id,
            type: "BaseNode",
            position: position,
            data: {
              nodeType: nodeData.type,
              ...nodeData.params,
              output: nodeData.output,
            },
          };
        });

        // 백엔드 엣지 데이터를 ReactFlow 엣지 형태로 변환 (엣지가 있는 경우)
        const reactFlowEdges: Edge[] = graph.edges ? graph.edges.map((edgeData: any, index: number) => ({
          id: `edge-${index}`,
          source: edgeData.source,
          target: edgeData.target,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 15,
            height: 15,
            color: '#6b7280',
          },
          style: {
            strokeWidth: 2,
            stroke: '#6b7280',
          },
        })) : [];

        console.log('변환된 노드:', reactFlowNodes);
        console.log('변환된 엣지:', reactFlowEdges);

        setNodes(reactFlowNodes);
        setEdges(reactFlowEdges);
        setCurrentGraphData({
          name: graph.name,
          description: graph.description || '',
          version: graph.version || 1
        });
      } else {
        console.log('그래프에 노드가 없습니다:', graph);
        // 빈 그래프라도 기본 정보는 설정
        if (graph) {
          setCurrentGraphData({
            name: graph.name || 'Untitled Graph',
            description: graph.description || '',
            version: graph.version || 1
          });
        }
      }
    } catch (error) {
      console.error('그래프 로드 실패:', error);
    }
  };

  // 그래프 저장
  const handleSaveGraph = async () => {
    // 이름이 없는 경우 팝업 표시
    if (!currentGraphData?.name || !currentGraphData.name.trim()) {
      setTempGraphData({
        name: currentGraphData?.name || '',
        description: currentGraphData?.description || '',
        version: currentGraphData?.version || 1
      });
      setIsGraphInfoDialogOpen(true);
      return;
    }

    await performSave();
  };

  // 실제 저장 수행
  const performSave = async (graphInfo?: { name: string; description: string; version: number }) => {
    console.log('performSave 호출됨:', { graphInfo, currentGraphData });
    setIsSaving(true);
    try {
      const dataToUse = graphInfo || currentGraphData;
      const graphData = {
        name: dataToUse?.name || '',
        description: dataToUse?.description || '',
        version: dataToUse?.version || 1,
        nodes: nodes.map((n, index) => ({
          node_id: n.id,
          type: n.data.nodeType || "PromptNode",
          output: n.data.output || "output",
          position: n.position ? { x: n.position.x, y: n.position.y } : null,
          order: index,
          params: {
            ...(n.data.nodeType === "InputNode" ? {} : 
                n.data.nodeType === "OutputNode" ? {
                  wrap_template: n.data.wrap_template || "",
                  inputs: n.data.inputs || {},
                } : n.data.nodeType === "PromptNode" ? {
                  system_prompt: n.data.system_prompt || "",
                  user_prompt: n.data.user_prompt || "",
                  assistant_prompt: n.data.assistant_prompt || "",
                  inputs: n.data.inputs || {},
                } : n.data.nodeType === "RetrievalNode" ? {
                  top_k: n.data.top_k || 4,
                  collection: n.data.collection || "",
                  inputs: n.data.inputs || {},
                } : n.data.nodeType === "ConditionNode" ? {
                  inputs: n.data.inputs || {},
                  conditions: n.data.conditions || [],
                  default_target: n.data.default_target || "",
                } : {})
          }
        })),
        edges: edges.map((e) => ({
          source: e.source,
          target: e.target,
        })),
        created_by: "admin",
        updated_by: "admin",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      console.log('저장할 그래프 데이터:', graphData);
      console.log('노드 개수:', nodes.length);
      console.log('엣지 개수:', edges.length);
      console.log('isCreateMode:', isCreateMode, 'graphId:', graphId);
      
      if (isCreateMode || graphId === 'create' || !graphId) {
        // 새 그래프 생성 (graphId가 없거나 create 모드인 경우)
        console.log('새 그래프 생성 시도...');
        const response = await createGraph(graphData);
        console.log('그래프 생성 성공:', response);
        alert('그래프가 성공적으로 생성되었습니다.');
        if (onBack) {
          onBack(true); // 목록 화면 리프레시를 위해 true 전달
        }
      } else if (graphId) {
        // 기존 그래프 업데이트
        console.log('기존 그래프 업데이트 시도...');
        const response = await updateGraph(graphId, graphData);
        console.log('그래프 업데이트 성공:', response);
        alert('그래프가 성공적으로 저장되었습니다.');
      }
    } catch (error) {
      console.error('그래프 저장 실패:', error);
      console.error('에러 상세:', error.response?.data);
      console.error('에러 상태:', error.response?.status);
      alert(`그래프 저장에 실패했습니다: ${error.response?.data?.message || error.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  // 팝업에서 확인 버튼 클릭 시
  const handleConfirmGraphInfo = () => {
    console.log('팝업에서 확인 버튼 클릭:', tempGraphData);
    setCurrentGraphData(tempGraphData);
    setIsGraphInfoDialogOpen(false);
    performSave(tempGraphData);
  };

  const onConnect = useCallback(
    (params: any) => {
      // 연결된 노드들의 키 매핑 처리
      const sourceNode = nodes.find(n => n.id === params.source);
      const targetNode = nodes.find(n => n.id === params.target);
      
      if (sourceNode && targetNode) {
        // ConditionNode의 특별한 Handle 처리
        if (sourceNode.data.nodeType === "ConditionNode" && params.sourceHandle) {
          const handleId = params.sourceHandle;
          
          if (handleId.startsWith("condition-")) {
            // condition-0, condition-1 등 → 해당 조건의 target 설정
            const conditionIndex = parseInt(handleId.replace("condition-", ""));
            setNodes((nds) =>
              nds.map((n) => {
                if (n.id === params.source) {
                  const newConditions = [...(n.data.conditions || [])];
                  if (newConditions[conditionIndex]) {
                    newConditions[conditionIndex] = {
                      ...newConditions[conditionIndex],
                      target: params.target
                    };
                  }
                  return { ...n, data: { ...n.data, conditions: newConditions } };
                }
                return n;
              })
            );
          } else if (handleId === "else") {
            // ELSE handle → default_target 설정
            setNodes((nds) =>
              nds.map((n) => 
                n.id === params.source 
                  ? { ...n, data: { ...n.data, default_target: params.target } }
                  : n
              )
            );
          }
        } else {
          // 일반 노드의 output을 타겟 노드의 inputs에 자동 설정
          if (sourceNode.data.output && sourceNode.data.output.trim() !== "") {
            // {node_id}_{output_key} 형태로 참조 키 생성
            const referenceKey = `${sourceNode.id}_${sourceNode.data.output}`;
            
            // 타겟 노드 타입에 따라 자동 설정
            if (targetNode.data.nodeType === "RetrievalNode") {
              const currentInputs = targetNode.data.inputs || {};
              if (!currentInputs.query || currentInputs.query.value === "") {
                setNodes((nds) =>
                  nds.map((n) => 
                    n.id === params.target 
                      ? { 
                          ...n, 
                          data: { 
                            ...n.data, 
                            inputs: {
                              ...currentInputs,
                              query: { type: "reference", value: referenceKey }
                            }
                          } 
                        }
                      : n
                  )
                );
              }
            } else if (targetNode.data.nodeType === "PromptNode") {
              // PromptNode의 경우 첫 번째 빈 입력에 자동 설정
              const currentInputs = targetNode.data.inputs || {};
              const firstEmptyInput = Object.keys(currentInputs).find(key => 
                !currentInputs[key] || currentInputs[key].value === ""
              );
              
              if (firstEmptyInput) {
                setNodes((nds) =>
                  nds.map((n) => 
                    n.id === params.target 
                      ? { 
                          ...n, 
                          data: { 
                            ...n.data, 
                            inputs: {
                              ...currentInputs,
                              [firstEmptyInput]: { type: "reference", value: referenceKey }
                            }
                          } 
                        }
                      : n
                  )
                );
              }
            } else if (targetNode.data.nodeType === "OutputNode") {
              // OutputNode의 경우 첫 번째 빈 입력에 자동 설정
              const currentInputs = targetNode.data.inputs || {};
              const firstEmptyInput = Object.keys(currentInputs).find(key => 
                !currentInputs[key] || currentInputs[key].value === ""
              );
              
              if (firstEmptyInput) {
                setNodes((nds) =>
                  nds.map((n) => 
                    n.id === params.target 
                      ? { 
                          ...n, 
                          data: { 
                            ...n.data, 
                            inputs: {
                              ...currentInputs,
                              [firstEmptyInput]: { type: "reference", value: referenceKey }
                            }
                          } 
                        }
                      : n
                  )
                );
              }
            }
          }
        }
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
        style: {
          strokeWidth: 2,
          stroke: '#6b7280',
        },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges, setNodes, nodes]
  );

  const onAddNode = () => {
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
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const onAddRetrievalNode = () => {
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      type: "BaseNode",
      position: { x: 100 + nodes.length * 350, y: 200 },
      data: {
        nodeType: "RetrievalNode",
        top_k: 4,
        collection: "",
        inputs: {
          query: { type: "reference", value: "" }
        },
        output: "context",
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const onAddInputNode = () => {
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      type: "BaseNode",
      position: { x: 100 + nodes.length * 350, y: 200 },
      data: {
        nodeType: "InputNode",
        output: "user_input",
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const onAddOutputNode = () => {
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      type: "BaseNode",
      position: { x: 100 + nodes.length + 350, y: 200 },
      data: {
        nodeType: "OutputNode",
        wrap_template: "🤖 AI 답변:\n\n{answer}\n\n---\n질문: {user_input}",
        inputs: {
          answer: { type: "reference", value: "" },
          user_input: { type: "reference", value: "" }
        },
        output: "agent_output",
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const onAddConditionNode = () => {
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      type: "BaseNode",
      position: { x: 100 + nodes.length * 350, y: 200 },
      data: {
        nodeType: "ConditionNode",
        inputs: {
          answer: { type: "reference", value: "" }
        },
        conditions: [
          {
            variable: "answer",
            operator: "contains",
            value: "긍정적",
            target: ""
          }
        ],
        default_target: "",
        output: "condition_result",
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  // 스니펫 로드 함수
  const onLoadSnippet = (snippet: GraphSnippet) => {
    // 기존 노드와 엣지 초기화
    setNodes([]);
    setEdges([]);

    // 스니펫의 노드들을 ReactFlow 노드 형태로 변환
    const newNodes: Node[] = snippet.data.nodes.map((nodeData, index) => ({
      id: nodeData.id,
      type: "BaseNode",
      position: { 
        x: 100 + index * 350, 
        y: 200 
      },
      data: {
        nodeType: nodeData.type,
        // 노드 타입에 따른 데이터 설정
        ...(nodeData.type === "InputNode" ? {
          output: "user_input",
        } : nodeData.type === "OutputNode" ? {
          wrap_template: nodeData.params.wrap_template || "",
          inputs: nodeData.params.inputs || {},
          output: "agent_output",
        } : nodeData.type === "PromptNode" ? {
          system_prompt: nodeData.params.system_prompt || "",
          user_prompt: nodeData.params.user_prompt || "",
          assistant_prompt: nodeData.params.assistant_prompt || "",
          inputs: nodeData.params.inputs || {},
          output: nodeData.output || "answer",
        } : nodeData.type === "RetrievalNode" ? {
          top_k: nodeData.params.top_k || 4,
          collection: nodeData.params.collection || "",
          inputs: nodeData.params.inputs || {},
          output: nodeData.output || "context",
        } : nodeData.type === "ConditionNode" ? {
          inputs: nodeData.params.inputs || {},
          conditions: nodeData.params.conditions || [],
          default_target: nodeData.params.default_target || "",
          output: nodeData.output || "condition_result",
        } : {})
      }
    }));

    // 스니펫의 엣지들을 ReactFlow 엣지 형태로 변환 (화살표 포함)
    const newEdges = snippet.data.edges.map((edge, index) => {
      const sourceNode = snippet.data.nodes.find(n => n.id === edge.source);
      let sourceHandle = undefined;
      
      // ConditionNode에서 나오는 엣지인 경우 올바른 sourceHandle 설정
      if (sourceNode && sourceNode.type === "ConditionNode") {
        const conditionNode = sourceNode;
        const conditions = conditionNode.params?.conditions || [];
        const defaultTarget = conditionNode.params?.default_target || "";
        
        // 조건별 target과 매칭되는 sourceHandle 찾기
        const conditionIndex = conditions.findIndex((cond: any) => cond.target === edge.target);
        if (conditionIndex !== -1) {
          sourceHandle = `condition-${conditionIndex}`;
        } else if (edge.target === defaultTarget) {
          sourceHandle = "else";
        }
      }
      
      return {
        id: `edge-${index}`,
        source: edge.source,
        target: edge.target,
        sourceHandle: sourceHandle,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 15,
          height: 15,
          color: '#6b7280',
        },
        style: {
          strokeWidth: 2,
          stroke: '#6b7280',
        },
      };
    });

    setNodes(newNodes);
    setEdges(newEdges);
  };

  // 유저가 메시지 입력했을 때 → 그래프 실행
  const onSendMessage = async (userInput: string) => {
    setMessages((msgs) => [...msgs, { role: "user", content: userInput }]);
    setIsRunning(true);
  
    try {
      // input_state를 동적으로 생성
      const inputState: Record<string, string> = {};
      
      // InputNode가 있는지 확인
      const inputNode = nodes.find(n => n.data.nodeType === "InputNode");
      if (inputNode) {
        // InputNode가 있으면 "input" 키에 사용자 입력을 저장
        inputState.input = userInput;
      } else {
        // InputNode가 없으면 기본 키에 사용자 입력을 저장
        inputState.user_input = userInput;
      }
      
      const graph = {
        nodes: nodes.map((n) => {
          const baseNode = {
            id: n.id,
            type: n.data.nodeType || "PromptNode",
            output: n.data.output || "output",
          };

          // 노드 타입에 따른 params 설정
          if (n.data.nodeType === "InputNode") {
            return {
              ...baseNode,
              output: "user_input",
              params: {},
            };
          } else if (n.data.nodeType === "OutputNode") {
            return {
              ...baseNode,
              output: "agent_output",
              params: {
                wrap_template: n.data.wrap_template || "",
                inputs: n.data.inputs || {},
              },
            };
          } else if (n.data.nodeType === "PromptNode") {
            return {
              ...baseNode,
              output: n.data.output || "output",
              params: {
                system_prompt: n.data.system_prompt || "",
                user_prompt: n.data.user_prompt || "",
                assistant_prompt: n.data.assistant_prompt || "",
                inputs: n.data.inputs || {},
              },
            };
          } else if (n.data.nodeType === "RetrievalNode") {
            return {
              ...baseNode,
              output: n.data.output || "output",
              params: {
                top_k: n.data.top_k || 4,
                collection: n.data.collection || "",
                inputs: n.data.inputs || {},
              },
            };
          } else if (n.data.nodeType === "ConditionNode") {
            return {
              ...baseNode,
              output: n.data.output || "condition_result",
              params: {
                inputs: n.data.inputs || {},
                conditions: n.data.conditions || [],
                default_target: n.data.default_target || "",
              },
            };
          }

          return baseNode;
        }),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 15,
            height: 15,
            color: '#6b7280',
          },
          style: {
            strokeWidth: 2,
            stroke: '#6b7280',
          },
        })),
        input_state: inputState,
      };
  
      const res = await runGraph(graph);
  
      setMessages((msgs) => [
        ...msgs,
        { role: "agent", content: JSON.stringify(res.results ?? res, null, 2) },
      ]);
    } catch (error) {
      console.error("Failed to run graph:", error);
      setMessages((msgs) => [
        ...msgs,
        { role: "agent", content: "⚠️ Failed to run graph" },
      ]);
    } finally {
      setIsRunning(false);
    }
  };
  

  return (
    <div className="flex h-full max-h-screen overflow-hidden">
      <NodeSidebar 
        onAddNode={onAddNode} 
        onAddRetrievalNode={onAddRetrievalNode} 
        onAddInputNode={onAddInputNode}
        onAddOutputNode={onAddOutputNode}
        onAddConditionNode={onAddConditionNode}
        onLoadSnippet={onLoadSnippet}
      />

      <div className="flex-1 relative overflow-hidden min-h-0">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          className="bg-gray-100"
          style={{ 
            height: '100%', 
            width: '100%',
            overflow: 'hidden'
          }}
        >
          <MiniMap position="top-right" style={{ top: 10, right: 10 }} />
          <Controls />
          <Background />
          
          {/* 저장 버튼 - 오른쪽 하단 */}
          <div className="absolute bottom-4 right-4 z-10">
            <div className="flex flex-col gap-2">
              {onBack && (
                <Button variant="outline" onClick={onBack} className="bg-white shadow-lg">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  뒤로가기
                </Button>
              )}
              <Button 
                onClick={handleSaveGraph} 
                disabled={isSaving}
                className="bg-blue-600 hover:bg-blue-700 shadow-lg"
              >
                <Save className="h-4 w-4 mr-2" />
                {isSaving ? '저장 중...' : '저장'}
              </Button>
            </div>
          </div>
        </ReactFlow>
      </div>

      {/* 그래프 정보 입력 팝업 */}
      <GraphInfoDialog
        isOpen={isGraphInfoDialogOpen}
        onClose={() => setIsGraphInfoDialogOpen(false)}
        onConfirm={handleConfirmGraphInfo}
        graphData={tempGraphData}
        setGraphData={setTempGraphData}
      />

      {/* 오른쪽 채팅 패널 */}
      <ChatPanel
        messages={messages}
        onSendMessage={onSendMessage}
        isRunning={isRunning}
      />
    </div>
  );
}
