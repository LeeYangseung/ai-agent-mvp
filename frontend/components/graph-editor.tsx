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
import { ArrowLeft, Save, ChevronDown, ChevronRight, Eye, History, Database } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const nodeTypes = { BaseNode };

// 💬 메시지 타입
type ChatMessage = {
  role: "user" | "agent";
  content: string;
  timestamp?: Date;
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
// 확장 가능한 패널 컴포넌트
// ------------------------------------------------------------
function ExpandablePanel({
  title,
  icon: Icon,
  children,
  isExpanded,
  onToggle,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border-b">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50"
      >
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" />
          <span className="text-sm font-medium">{title}</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </button>
      {isExpanded && (
        <div className="p-3 bg-gray-50 max-h-60 overflow-y-auto">
          {children}
        </div>
      )}
    </div>
  );
}

// ------------------------------------------------------------
// 개선된 채팅 UI
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
  const [showNodeDetails, setShowNodeDetails] = useState(false);
  const [showGraphHistory, setShowGraphHistory] = useState(false);
  const [showGraphState, setShowGraphState] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;
    onSendMessage(input);
    setInput("");
  };

  // Agent 답변만 추출
  const getAgentResponse = (message: ChatMessage) => {
    if (message.role === "user") return null;
    
    try {
      const parsed = JSON.parse(message.content);
      
      if (parsed.results && Array.isArray(parsed.results)) {
        // 그래프 실행 실패 확인
        const failedNode = parsed.results.find((node: any) => 
          node.outputs && Object.values(node.outputs).some((output: any) => 
            typeof output === 'string' && output.startsWith('[ERROR]')
          )
        );
        
        if (failedNode) {
          const errorOutput = Object.values(failedNode.outputs).find((output: any) => 
            typeof output === 'string' && output.startsWith('[ERROR]')
          ) as string;
          const errorMessage = errorOutput?.replace('[ERROR]', '').trim() || '알 수 없는 오류가 발생했습니다.';
          return `❌ **그래프 실행 실패**\n\n${errorMessage}`;
        }
        
        // OutputNode에서 agent_output 찾기
        const outputNode = parsed.results.find((node: any) => 
          node.type === "OutputNode" && node.outputs?.agent_output
        );
        return outputNode?.outputs?.agent_output || null;
      }
      
      return null;
    } catch {
      return message.content;
    }
  };

  // 노드별 상세 정보 추출
  const getNodeDetails = (message: ChatMessage) => {
    if (message.role === "user") return null;
    
    try {
      const parsed = JSON.parse(message.content);
      
      if (parsed.results && Array.isArray(parsed.results)) {
        return parsed.results.reduce((acc: any, node: any) => {
          acc[node.node_id] = {
            type: node.type,
            input: node.inputs,
            output: node.outputs,
            status: node.status,
            error_message: node.error_message
          };
          return acc;
        }, {});
      }
      
      return null;
    } catch {
      return null;
    }
  };

  // 그래프 히스토리 추출
  const getGraphHistory = (message: ChatMessage) => {
    if (message.role === "user") return null;
    
    try {
      const parsed = JSON.parse(message.content);
      
      if (parsed.results && Array.isArray(parsed.results)) {
        const executionInfo = parsed.execution_info || {};
        return [
          { timestamp: new Date(), action: 'Graph Execution Started' },
          { timestamp: new Date(), action: `Executed ${executionInfo.executed_nodes || parsed.results.length} nodes` },
          { timestamp: new Date(), action: 'Graph Execution Completed' }
        ];
      }
      
      return [{ timestamp: new Date(), action: 'Graph Execution' }];
    } catch {
      return [{ timestamp: new Date(), action: 'Graph Execution' }];
    }
  };

  // 그래프 스테이트 추출
  const getGraphState = (message: ChatMessage) => {
    if (message.role === "user") return null;
    
    try {
      const parsed = JSON.parse(message.content);
      
      if (parsed.results && Array.isArray(parsed.results)) {
        return {
          structured_results: parsed.results,
          execution_info: parsed.execution_info,
          final_state: parsed.final_state
        };
      }
      
      return null;
    } catch {
      return null;
    }
  };

  return (
    <div className="flex flex-col border-l bg-white w-80 h-full max-h-screen">
      {/* 패널 토글 버튼들 */}
      <div className="flex border-b bg-gray-50 p-2 gap-1">
        <Button
          variant={showNodeDetails ? "default" : "outline"}
          size="sm"
          onClick={() => setShowNodeDetails(!showNodeDetails)}
          className="flex-1 text-xs"
        >
          <Eye className="h-3 w-3 mr-1" />
          노드
        </Button>
        <Button
          variant={showGraphHistory ? "default" : "outline"}
          size="sm"
          onClick={() => setShowGraphHistory(!showGraphHistory)}
          className="flex-1 text-xs"
        >
          <History className="h-3 w-3 mr-1" />
          히스토리
        </Button>
        <Button
          variant={showGraphState ? "default" : "outline"}
          size="sm"
          onClick={() => setShowGraphState(!showGraphState)}
          className="flex-1 text-xs"
        >
          <Database className="h-3 w-3 mr-1" />
          스테이트
        </Button>
      </div>

      {/* 채팅 영역 */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {messages.length === 0 ? (
          /* 채팅이 시작되기 전: 안내 메시지 */
          <div className="flex items-center justify-center h-full p-4">
            <div className="text-center text-gray-500">
              <div className="text-lg mb-2">🤖 AI Agent</div>
              <div className="text-sm">아래에서 메시지를 입력하여 그래프를 실행해보세요</div>
            </div>
          </div>
        ) : (
          /* 채팅 메시지들 */
          <div>
            {messages.map((m, i) => {
              const agentResponse = getAgentResponse(m);
              const nodeDetails = getNodeDetails(m);
              const graphHistory = getGraphHistory(m);
              const graphState = getGraphState(m);

              return (
                <div key={i} className="border-b">
                  {/* 사용자 메시지 */}
                  {m.role === "user" && (
                    <div className="p-3 bg-blue-50">
                      <div className="text-sm font-medium text-blue-800 mb-1">사용자</div>
                      <div className="text-sm">{m.content}</div>
                    </div>
                  )}

                  {/* Agent 답변 */}
                  {m.role === "agent" && agentResponse && (
                    <div className="p-3 bg-gray-50">
                      <div className="text-sm font-medium text-gray-800 mb-2">AI 답변</div>
                      <div className="prose text-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {agentResponse}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}

                  {/* 확장 가능한 패널들 */}
                  {m.role === "agent" && (
                    <div className="bg-white">
                      {nodeDetails && (
                        <ExpandablePanel
                          title="노드별 입출력"
                          icon={Eye}
                          isExpanded={showNodeDetails}
                          onToggle={() => setShowNodeDetails(!showNodeDetails)}
                        >
                          <div className="space-y-2 text-xs">
                            {Object.entries(nodeDetails).map(([nodeId, details]: [string, any]) => (
                              <div key={nodeId} className="border rounded p-2">
                                <div className="flex items-center justify-between">
                                  <div className="font-medium text-gray-700">{nodeId}</div>
                                  <div className="flex items-center gap-1">
                                    <span className="text-xs px-1 py-0.5 bg-blue-100 text-blue-700 rounded">
                                      {details.type}
                                    </span>
                                  {details.status && (
                                    <span className={`text-xs px-1 py-0.5 rounded ${
                                      details.status === 'success' 
                                        ? 'bg-green-100 text-green-700' 
                                        : details.status === 'failed'
                                        ? 'bg-red-100 text-red-700'
                                        : 'bg-yellow-100 text-yellow-700'
                                    }`}>
                                      {details.status === 'pending' ? 'pending' : details.status}
                                    </span>
                                  )}
                                  </div>
                                </div>
                                
                                {/* 입력값 표시 */}
                                {details.input && Object.keys(details.input).length > 0 && (
                                  <div className="mt-2">
                                    <div className="text-gray-600 mb-1">입력:</div>
                                    <div className="space-y-1">
                                      {Object.entries(details.input).map(([key, value]: [string, any]) => (
                                        <div key={key} className="bg-blue-50 p-1 rounded text-xs">
                                          <span className="font-medium text-blue-800">{key}:</span>
                                          <span className="ml-1">
                                            {typeof value === 'string' 
                                              ? value.substring(0, 80) + (value.length > 80 ? '...' : '')
                                              : JSON.stringify(value).substring(0, 80) + '...'
                                            }
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {/* 출력값 표시 */}
                                {details.output && Object.keys(details.output).length > 0 && (
                                  <div className="mt-2">
                                    <div className="text-gray-600 mb-1">출력:</div>
                                    <div className="space-y-1">
                                      {Object.entries(details.output).map(([key, value]: [string, any]) => (
                                        <div key={key} className="bg-green-50 p-1 rounded text-xs">
                                          <span className="font-medium text-green-800">{key}:</span>
                                          <span className="ml-1">
                                            {typeof value === 'string' 
                                              ? value.substring(0, 80) + (value.length > 80 ? '...' : '')
                                              : JSON.stringify(value).substring(0, 80) + '...'
                                            }
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* 에러 메시지 표시 */}
                                {details.error_message && (
                                  <div className="mt-2">
                                    <div className="text-gray-600 mb-1">에러:</div>
                                    <div className="bg-red-50 p-2 rounded text-xs border border-red-200">
                                      <div className="font-medium text-red-800 mb-1">❌ 실행 실패</div>
                                      <div className="text-red-700">
                                        {details.error_message}
                                      </div>
                                    </div>
                                  </div>
                                )}

                                {/* Pending 상태 안내 */}
                                {details.status === 'pending' && (
                                  <div className="mt-2">
                                    <div className="bg-yellow-50 p-2 rounded text-xs border border-yellow-200">
                                      <div className="font-medium text-yellow-800 mb-1">⏳ 실행 대기</div>
                                      <div className="text-yellow-700">
                                        이전 노드에서 오류가 발생하여 실행되지 않았습니다.
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </ExpandablePanel>
                      )}

                      {graphHistory && (
                        <ExpandablePanel
                          title="그래프 히스토리"
                          icon={History}
                          isExpanded={showGraphHistory}
                          onToggle={() => setShowGraphHistory(!showGraphHistory)}
                        >
                          <div className="space-y-1 text-xs">
                            {graphHistory.map((item, idx) => (
                              <div key={idx} className="flex justify-between items-center p-1 bg-gray-100 rounded">
                                <span>{item.action}</span>
                                <span className="text-gray-500">
                                  {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : '방금 전'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </ExpandablePanel>
                      )}

                      {graphState && (
                        <ExpandablePanel
                          title="그래프 스테이트"
                          icon={Database}
                          isExpanded={showGraphState}
                          onToggle={() => setShowGraphState(!showGraphState)}
                        >
                          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(graphState, null, 2)}
                          </pre>
                        </ExpandablePanel>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 입력 폼 - 항상 맨 아래에 고정 */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="border-t p-2 flex space-x-2 flex-shrink-0 bg-white"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="메시지를 입력하세요..."
          className="flex-1 border rounded px-2 py-1 text-sm"
        />
        <Button type="submit" disabled={isRunning}>
          {isRunning ? "..." : "전송"}
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
  onAddMergeNode,
  onLoadSnippet 
}: { 
  onAddNode: () => void;
  onAddRetrievalNode: () => void;
  onAddInputNode: () => void;
  onAddOutputNode: () => void;
  onAddConditionNode: () => void;
  onAddMergeNode: () => void;
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
        onClick={onAddMergeNode}
      >
        🔗 Add Merge Node
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
                  evaluation_mode: n.data.evaluation_mode || "first_match",
                } : n.data.nodeType === "MergeNode" ? {
                  inputs: n.data.inputs || {},
                  merge_strategy: n.data.merge_strategy || "concat",
                  separator: n.data.separator || "\n\n---\n\n",
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
          onBack(true); // 목록 리프레시
        }
      } else if (graphId) {
        // 기존 그래프 업데이트
        console.log('기존 그래프 업데이트 시도...');
        const response = await updateGraph(graphId, graphData);
        console.log('그래프 업데이트 성공:', response);
        alert('그래프가 성공적으로 저장되었습니다.');
      }
    } catch (error: any) {
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
      position: { x: 100 + nodes.length * 350, y: 200 },
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
        evaluation_mode: "first_match",
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

  const onAddMergeNode = () => {
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      type: "BaseNode",
      position: { x: 100 + nodes.length * 350, y: 200 },
      data: {
        nodeType: "MergeNode",
        merge_strategy: "concat",
        separator: "\n\n---\n\n",
        inputs: {
          result_1: { type: "reference", value: "" },
          result_2: { type: "reference", value: "" }
        },
        output: "merged_output",
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  // 스니펫 로드 함수
  const onLoadSnippet = (snippet: GraphSnippet) => {
    // 기존 노드와 엣지 초기화
    setNodes([]);
    setEdges([]);

    // 자동 레이아웃을 위한 노드 위치 계산
    const calculateNodePositions = () => {
      const positions: Record<string, { x: number; y: number }> = {};
      const visited = new Set<string>();
      const levelX: Record<number, number> = {};
      
      // ConditionNode의 분기 타겟들을 찾기
      const conditionBranches = new Map<string, string[]>(); // conditionNodeId -> [targets]
      snippet.data.nodes.forEach(node => {
        if (node.type === "ConditionNode") {
          const targets = new Set<string>();
          (node.params?.conditions || []).forEach((cond: any) => {
            if (cond.target) targets.add(cond.target);
          });
          if (node.params?.default_target) {
            targets.add(node.params.default_target);
          }
          conditionBranches.set(node.id, Array.from(targets));
        }
      });

      // BFS로 레벨별 노드 배치
      const queue: Array<{ id: string; level: number; branchIndex?: number; parentId?: string }> = [];
      const firstNode = snippet.data.nodes[0];
      if (firstNode) {
        queue.push({ id: firstNode.id, level: 0 });
      }

      while (queue.length > 0) {
        const { id, level, branchIndex, parentId } = queue.shift()!;
        if (visited.has(id)) continue;
        visited.add(id);

        // x 좌표: 레벨 기반
        const x = 100 + level * 550;
        
        // y 좌표: 일반 노드는 현재 레벨의 카운터, 분기 노드는 branchIndex 사용
        let y: number;
        if (branchIndex !== undefined && parentId) {
          // 분기 노드: 부모 ConditionNode 기준으로 수직 배치
          const parentY = positions[parentId]?.y || 200;
          const branches = conditionBranches.get(parentId) || [];
          const branchCount = branches.length;
          
          // 노드 간격: 노드 높이 + 여유 공간 (최소 350px)
          const spacing = 350;
          
          // 중앙 정렬: 전체 분기의 중간을 부모 y에 맞춤
          const totalHeight = (branchCount - 1) * spacing;
          const startY = parentY - (totalHeight / 2);
          
          y = startY + branchIndex * spacing;
        } else {
          // 일반 노드: 레벨별 카운터
          levelX[level] = (levelX[level] || 0) + 1;
          y = 200 + (levelX[level] - 1) * 400; // 간격 증가
        }

        positions[id] = { x, y };

        // 다음 노드 찾기
        const currentNode = snippet.data.nodes.find(n => n.id === id);
        
        // ConditionNode인 경우: 모든 분기를 같은 레벨에 배치
        if (currentNode && conditionBranches.has(id)) {
          const branches = conditionBranches.get(id)!;
          branches.forEach((targetId, idx) => {
            queue.push({ 
              id: targetId, 
              level: level + 1, 
              branchIndex: idx,
              parentId: id
            });
          });
        } else {
          // 일반 노드: 연결된 다음 노드 찾기
          snippet.data.edges
            .filter(e => e.source === id)
            .forEach(edge => {
              queue.push({ id: edge.target, level: level + 1 });
            });
        }
      }

      return positions;
    };

    const nodePositions = calculateNodePositions();

    // 스니펫의 노드들을 ReactFlow 노드 형태로 변환
    const newNodes: Node[] = snippet.data.nodes.map((nodeData, index) => ({
      id: nodeData.id,
      type: "BaseNode",
      position: nodePositions[nodeData.id] || { 
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
          evaluation_mode: nodeData.params.evaluation_mode || "first_match",
          output: nodeData.output || "condition_result",
        } : nodeData.type === "MergeNode" ? {
          inputs: nodeData.params.inputs || {},
          merge_strategy: nodeData.params.merge_strategy || "concat",
          separator: nodeData.params.separator || "\n\n---\n\n",
          output: nodeData.output || "merged_output",
        } : {})
      }
    }));

    // 스니펫의 엣지들을 ReactFlow 엣지 형태로 변환 (화살표 포함)
    // ConditionNode의 경우 conditions에서 자동으로 엣지 생성
    const edgesWithHandles: any[] = [];
    const processedConditionNodes = new Set<string>();
    
    snippet.data.edges.forEach((edge, index) => {
      const sourceNode = snippet.data.nodes.find(n => n.id === edge.source);
      
      // ConditionNode에서 나오는 엣지인 경우
      if (sourceNode && sourceNode.type === "ConditionNode") {
        // 아직 처리하지 않은 ConditionNode라면 모든 조건에 대해 엣지 생성
        if (!processedConditionNodes.has(edge.source)) {
          processedConditionNodes.add(edge.source);
          
          const conditionNode = sourceNode;
          const conditions = conditionNode.params?.conditions || [];
          const defaultTarget = conditionNode.params?.default_target || "";
          
          // 각 조건마다 엣지 생성
          conditions.forEach((cond: any, condIndex: number) => {
            edgesWithHandles.push({
              id: `edge-${edge.source}-condition-${condIndex}`,
              source: edge.source,
              target: cond.target,
              sourceHandle: `condition-${condIndex}`,
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
            });
          });
          
          // default_target (ELSE)가 있으면 추가
          if (defaultTarget) {
            edgesWithHandles.push({
              id: `edge-${edge.source}-else`,
              source: edge.source,
              target: defaultTarget,
              sourceHandle: "else",
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
            });
          }
        }
        // 이미 처리한 ConditionNode는 스킵
      } else {
        // 일반 엣지는 그대로 추가
        edgesWithHandles.push({
          id: `edge-${index}`,
          source: edge.source,
          target: edge.target,
          sourceHandle: undefined,
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
        });
      }
    });
    
    const newEdges = edgesWithHandles;

    // 디버그 로깅
    console.log('[DEBUG] Loaded snippet nodes:', newNodes.map(n => ({
      id: n.id,
      type: n.data.nodeType,
      inputs: n.data.inputs,
      output: n.data.output
    })));

    setNodes(newNodes);
    setEdges(newEdges);
  };

  // 유저가 메시지 입력했을 때 → 그래프 실행
  const onSendMessage = async (userInput: string) => {
    setMessages((msgs) => [...msgs, { 
      role: "user", 
      content: userInput,
      timestamp: new Date()
    }]);
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
            // 디버그 로깅
            console.log(`[DEBUG] ConditionNode ${n.id} inputs:`, n.data.inputs);
            return {
              ...baseNode,
              output: n.data.output || "condition_result",
              params: {
                inputs: n.data.inputs || {},
                conditions: n.data.conditions || [],
                default_target: n.data.default_target || "",
                evaluation_mode: n.data.evaluation_mode || "first_match",
              },
            };
          } else if (n.data.nodeType === "MergeNode") {
            // 디버그 로깅
            console.log(`[DEBUG] MergeNode ${n.id} inputs:`, n.data.inputs);
            return {
              ...baseNode,
              output: n.data.output || "merged_output",
              params: {
                inputs: n.data.inputs || {},
                merge_strategy: n.data.merge_strategy || "concat",
                separator: n.data.separator || "\n\n---\n\n",
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
        { 
          role: "agent", 
          content: JSON.stringify(res.results, null, 2),
          timestamp: new Date()
        },
      ]);
    } catch (error: any) {
      console.error("Failed to run graph:", error);
      
      // 에러 발생 시에도 구조화된 데이터로 응답
      const errorResults = nodes.map((node, index) => ({
        node_id: node.id,
        type: node.type,
        inputs: {},
        outputs: {},
        status: "pending",
        error_message: null
      }));
      
      setMessages((msgs) => [
        ...msgs,
        { 
          role: "agent", 
          content: JSON.stringify({
            results: errorResults,
            execution_info: {
              total_nodes: nodes.length,
              executed_nodes: 0,
            }
          }),
          timestamp: new Date()
        },
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
        onAddMergeNode={onAddMergeNode}
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
