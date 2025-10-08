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

// {} 감싸진 변수 자동 추출
function autoExtractVariables(template: string, currentVars: Record<string, string> = {}) {
  const regex = /\{([^}]+)\}/g;
  const matches = template.matchAll(regex);
  const newVars: Record<string, string> = { ...currentVars };

  for (const m of matches) {
    const key = m[1].trim();
    if (!(key in newVars)) {
      newVars[key] = "";
    }
  }
  return newVars;
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
  onLoadSnippet 
}: { 
  onAddNode: () => void;
  onAddRetrievalNode: () => void;
  onLoadSnippet: (snippet: GraphSnippet) => void;
}) {
  return (
    <div className="p-4 border-r bg-gray-50 w-64">
      <h3 className="font-bold mb-4">Nodes</h3>
      <Button
        className="w-full mb-2"
        onClick={onAddNode}
      >
        Add Prompt Node
      </Button>
      <Button
        className="w-full mb-2"
        onClick={onAddRetrievalNode}
      >
        Add Retrieval Node
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
        // 소스 노드의 output_key를 타겟 노드의 input_key로 설정
        if (sourceNode.data.output_key && sourceNode.data.output_key.trim() !== "") {
          setNodes((nds) =>
            nds.map((n) => 
              n.id === params.target 
                ? { ...n, data: { ...n.data, input_key: sourceNode.data.output_key } }
                : n
            )
          );
        }
      }
      
      // 엣지 추가
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges, setNodes, nodes]
  );

  const onAddNode = () => {
    const template = "";
    const variables: string[] = [];
  
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      type: "BaseNode",
      position: { x: Math.random() * 300 + 100, y: Math.random() * 300 + 100 },
      data: {
        nodeType: "PromptNode",
        template,
        variables,
        input_key: "", // placeholder
        output_key: "",  // placeholder
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const onAddRetrievalNode = () => {
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      type: "BaseNode",
      position: { x: Math.random() * 300 + 100, y: Math.random() * 300 + 100 },
      data: {
        nodeType: "RetrievalNode",
        query: "",
        top_k: "",
        collection: "",
        input_key: "query", // 기본값으로 query 설정
        output_key: "",  // placeholder
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
        x: 100 + (index % 3) * 300, 
        y: 100 + Math.floor(index / 3) * 200 
      },
      data: {
        nodeType: nodeData.type,
        input_key: nodeData.input_key,
        output_key: nodeData.output_key,
        // 노드 타입에 따른 데이터 설정
        ...(nodeData.type === "PromptNode" ? {
          template: nodeData.params.template,
          variables: nodeData.params.variables,
        } : nodeData.type === "RetrievalNode" ? {
          query: nodeData.params.template || "",
          top_k: "",
          collection: "",
        } : {})
      }
    }));

    // 스니펫의 엣지들을 ReactFlow 엣지 형태로 변환
    const newEdges = snippet.data.edges.map((edge, index) => ({
      id: `edge-${index}`,
      source: edge.source,
      target: edge.target,
    }));

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
      
      // 첫 번째 노드의 input_key에만 사용자 입력을 매핑
      if (nodes.length > 0) {
        const firstNode = nodes[0];
        const inputKey = firstNode.data.input_key;
        if (inputKey && inputKey.trim() !== "") {
          inputState[inputKey] = userInput;
        } else {
          // input_key가 없는 경우 기본값으로 question 사용
          inputState.question = userInput;
        }
      }
      
      const graph = {
        nodes: nodes.map((n) => {
          const baseNode = {
            id: n.id,
            type: n.data.nodeType || "PromptNode",
            input_key: n.data.input_key || "",
            output_key: n.data.output_key || "",
          };

          // 노드 타입에 따른 params 설정
          if (n.data.nodeType === "PromptNode") {
            return {
              ...baseNode,
              params: {
                template: n.data.template,
                variables: n.data.variables,
              },
            };
          } else if (n.data.nodeType === "RetrievalNode") {
            return {
              ...baseNode,
              params: {
                template: n.data.query, // query를 template으로 매핑
                variables: {}, // RetrievalNode는 variables가 필요 없음
                // collection: n.data.collection,
              },
              k: n.data.top_k,
            };
          }

          return baseNode;
        }),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
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
