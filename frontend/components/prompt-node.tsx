"use client"

import { Handle, Position } from "reactflow";

function PromptNode({ data }: any) {
  return (
    <div className="p-3 rounded-lg shadow-md bg-white border border-gray-200 min-w-[200px]">
      <div className="font-bold text-sm mb-1">Prompt Node</div>
      <div className="text-xs text-gray-600 mb-2">{data?.template || "No template"}</div>
      {data?.variables && (
        <div className="text-xs text-gray-500">
          Variables: {Object.keys(data.variables).join(", ")}
        </div>
      )}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export default PromptNode;
