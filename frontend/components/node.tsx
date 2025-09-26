"use client"

import { Handle, Position, NodeProps, useReactFlow } from "reactflow";
import { useCallback } from "react";

function autoExtractVariables(template: string, currentVars: Record<string, string>) {
  const regex = /\{([^}]+)\}/g;
  const matches = template.matchAll(regex);
  const newVars: Record<string, string> = {};

  for (const m of matches) {
    const key = m[1].trim();
    newVars[key] = currentVars[key] ?? "";
  }

  return newVars;
}

export default function BaseNode({ id, data }: NodeProps) {
  const { setNodes } = useReactFlow();

  // 공통 데이터 업데이트
  const updateNodeData = (patch: Record<string, any>) => {
    setNodes((nds) =>
      nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, ...patch } } : n))
    );
  };

  return (
    <div className="p-3 rounded-lg shadow-md bg-white border border-gray-200 min-w-[240px]">
      {/* 타입 선택 */}
      <div className="mb-2">
        <label className="text-xs font-bold mr-2">Type:</label>
        <select
          value={data?.nodeType || "PromptNode"}
          onChange={(e) => updateNodeData({ nodeType: e.target.value })}
          className="text-xs border rounded px-1"
        >
          <option value="PromptNode">Prompt Node</option>
          {/* RAGNode, AlertNode 등 추가 가능 */}
        </select>
      </div>

      {/* input_key / output_key */}
      <div className="flex space-x-1 mb-2">
        <label className="text-xs font-bold mr-2">input_key:</label>
        <input
          value={data?.input_key || ""}
          onChange={(e) => updateNodeData({ input_key: e.target.value })}
          placeholder="input_key"
          className="flex-1 border rounded px-1 text-xs"
        />
      </div>
      <div className="flex space-x-1 mb-2">
        <label className="text-xs font-bold mr-2">output_key:</label>
        <input
          value={data?.output_key || ""}
          onChange={(e) => updateNodeData({ output_key: e.target.value })}
          placeholder="output_key"
          className="flex-1 border rounded px-1 text-xs"
        />
      </div>

      {/* PromptNode UI */}
      {data?.nodeType === "PromptNode" && (
        <>
          <label className="text-xs font-bold mr-2">template:</label>
          <textarea
            value={data?.template || ""}
            onChange={(e) =>
              updateNodeData({
                template: e.target.value,
                variables: autoExtractVariables(e.target.value, data.variables || {}),
              })
            }
            placeholder="Enter prompt with {variables}"
            className="w-full border rounded p-1 text-xs mb-2"
            rows={3}
          />

          <div className="space-y-1">
            <label className="text-xs font-bold mr-2">variables:</label>
            {data?.variables &&
              Object.entries(data.variables).map(([key, val]) => (
                <div key={key} className="flex items-center space-x-1">
                  <span className="text-[10px] font-mono bg-gray-100 px-1 rounded">
                    {key}
                  </span>
                  <input
                    value={val}
                    onChange={(e) =>
                      updateNodeData({
                        variables: { ...data.variables, [key]: e.target.value },
                      })
                    }
                    className="flex-1 border rounded px-1 text-xs"
                    placeholder="value"
                  />
                </div>
              ))}
          </div>
        </>
      )}

      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
