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
} from "reactflow";
import "reactflow/dist/style.css";
import PromptNode from "./prompt-node";
import { runGraph } from "@/lib/api";
import { Button } from "@/components/ui/button";

const nodeTypes = { PromptNode };

// 사이드바 컴포넌트
function NodeSidebar({ onAddNode }: { onAddNode: (type: string) => void }) {
  return (
    <div className="p-4 border-r bg-gray-50 w-64">
      <h3 className="font-bold mb-4">Nodes</h3>
      <Button
        className="w-full mb-2"
        onClick={() => onAddNode("PromptNode")}
      >
        Add Prompt Node
      </Button>
    </div>
  );
}

export function GraphEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [results, setResults] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onAddNode = (type: string) => {
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      type,
      position: { x: Math.random() * 300 + 100, y: Math.random() * 300 + 100 },
      data: {
        template: "Hello {name}",
        variables: { name: "Alice" },
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const onRun = async () => {
    setIsRunning(true);
    try {
      const graph = { nodes, edges };
      const res = await runGraph(graph);
      setResults(res.results);
    } catch (error) {
      console.error("Failed to run graph:", error);
      setResults({ error: "Failed to run graph" });
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
        
        <div className="absolute bottom-4 right-4 space-y-2">
          <Button
            onClick={onRun}
            disabled={isRunning || nodes.length === 0}
            className="bg-green-500 hover:bg-green-600"
          >
            {isRunning ? "Running..." : "Run Graph"}
          </Button>
        </div>

        {results && (
          <div className="absolute bottom-20 right-4 bg-white p-4 shadow-lg rounded-lg max-w-sm max-h-64 overflow-auto">
            <h4 className="font-bold mb-2">Results:</h4>
            <pre className="text-xs whitespace-pre-wrap">
              {JSON.stringify(results, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
