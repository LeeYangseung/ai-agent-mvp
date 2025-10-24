"use client"

import React, { useCallback, useState } from "react";
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
import { runGraph } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { GraphSnippet, graphSnippets } from "./graph-snippet";

const nodeTypes = { BaseNode };

// 💬 메시지 타입
type ChatMessage = {
  role: "user" | "agent";
  content: string;
};

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
    <div className="flex flex-col border-l bg-white w-80 h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
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
        className="border-t p-2 flex space-x-2"
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

export function GraphEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

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
            // 타겟 노드가 RetrievalNode이고 query 입력이 비어있으면 자동 설정
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
                              query: { type: "reference", value: sourceNode.data.output }
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
    <div className="flex h-full">
      <NodeSidebar 
        onAddNode={onAddNode} 
        onAddRetrievalNode={onAddRetrievalNode} 
        onAddInputNode={onAddInputNode}
        onAddOutputNode={onAddOutputNode}
        onAddConditionNode={onAddConditionNode}
        onLoadSnippet={onLoadSnippet}
      />

      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          className="bg-gray-100"
        >
          <MiniMap position="top-right" style={{ top: 10, right: 10 }} />
          <Controls />
          <Background />
        </ReactFlow>
      </div>

      {/* 오른쪽 채팅 패널 */}
      <ChatPanel
        messages={messages}
        onSendMessage={onSendMessage}
        isRunning={isRunning}
      />
    </div>
  );
}
