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
function NodeSidebar({ onAddNode }: { onAddNode: (type: string) => void }) {
  return (
    <div className="p-4 border-r bg-gray-50 w-64">
      <h3 className="font-bold mb-4">Nodes</h3>
      <Button
        className="w-full mb-2"
        onClick={() => onAddNode("BaseNode")}
      >
        Add Node
      </Button>
    </div>
  );
}

export function GraphEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onAddNode = () => {
    const template = "질문으로 만드세요 : {question}";
    const variables = autoExtractVariables(template);
  
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      type: "BaseNode",
      position: { x: Math.random() * 300 + 100, y: Math.random() * 300 + 100 },
      data: {
        nodeType: "PromptNode",
        template,
        variables,
        input_key: "question", // 기본값
        output_key: "output",  // 기본값
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  // 유저가 메시지 입력했을 때 → 그래프 실행
  const onSendMessage = async (userInput: string) => {
    setMessages((msgs) => [...msgs, { role: "user", content: userInput }]);
    setIsRunning(true);
  
    try {
      const graph = {
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.data.nodeType || "PromptNode", // 실제 타입
          params: {
            template: n.data.template,
            variables: n.data.variables,
          },
          input_key: n.data.input_key || "",
          output_key: n.data.output_key || "",
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
        })),
        input_state: {
          question: userInput, // ✅ 항상 사용자 입력을 question으로 전달
        },
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
      <NodeSidebar onAddNode={onAddNode} />

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
