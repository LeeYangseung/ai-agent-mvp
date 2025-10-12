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

  // 노드 삭제
  const deleteNode = () => {
    if (window.confirm("이 노드를 삭제하시겠습니까?")) {
      setNodes((nds) => nds.filter((n) => n.id !== id));
    }
  };

  // 노드 타입에 따른 배경색 설정
  const getNodeStyle = () => {
    switch (data?.nodeType) {
      case "InputNode":
        return "p-3 rounded-lg shadow-md bg-blue-50 border border-blue-200 min-w-[240px]";
      case "OutputNode":
        return "p-3 rounded-lg shadow-md bg-green-50 border border-green-200 min-w-[240px]";
      case "RetrievalNode":
        return "p-3 rounded-lg shadow-md bg-purple-50 border border-purple-200 min-w-[240px]";
      case "PromptNode":
      default:
        return "p-3 rounded-lg shadow-md bg-white border border-gray-200 min-w-[240px]";
    }
  };

  return (
    <div className={getNodeStyle()}>
      {/* 상단 헤더 */}
      <div className="flex justify-between items-center mb-2">
        {/* 노드 타입 표시 */}
        <div className="text-sm font-bold">
          {data?.nodeType === "InputNode" && "📥 Input Node"}
          {data?.nodeType === "PromptNode" && "💬 Prompt Node"}
          {data?.nodeType === "RetrievalNode" && "🔍 Retrieval Node"}
          {data?.nodeType === "OutputNode" && "📤 Output Node"}
        </div>
        
        {/* 오른쪽 버튼들 */}
        <div className="flex items-center space-x-1">
          {/* 정보 아이콘 (모든 노드) */}
          <div className="relative group">
            <div className="w-5 h-5 bg-blue-200 hover:bg-blue-300 text-blue-600 hover:text-blue-700 rounded flex items-center justify-center cursor-help transition-colors duration-200">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4M12 8h.01"/>
              </svg>
            </div>
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-20 w-64">
              {data?.nodeType === "InputNode" && (
                <div>
                  <div className="font-bold mb-1">📥 Input Node</div>
                  <div>외부 입력을 그래프 state로 변환합니다.</div>
                  <div className="mt-1 text-gray-300">• output_key: 결과를 저장할 키</div>
                </div>
              )}
              {data?.nodeType === "PromptNode" && (
                <div>
                  <div className="font-bold mb-1">💬 Prompt Node</div>
                  <div>LLM에 프롬프트를 전송하여 답변을 생성합니다.</div>
                  <div className="mt-1 text-gray-300">
                    <div>• template: LLM에 보낼 프롬프트 템플릿</div>
                    <div>• variables: 템플릿에서 사용할 변수들</div>
                    <div>• input_key: 입력 데이터의 키</div>
                    <div>• output_key: 결과를 저장할 키</div>
                  </div>
                </div>
              )}
              {data?.nodeType === "RetrievalNode" && (
                <div>
                  <div className="font-bold mb-1">🔍 Retrieval Node</div>
                  <div>벡터 데이터베이스에서 관련 문서를 검색합니다.</div>
                  <div className="mt-1 text-gray-300">
                    <div>• top_k: 검색할 상위 문서 개수</div>
                    <div>• collection: 검색할 컬렉션 이름</div>
                    <div>• input_key: 검색 쿼리의 키</div>
                    <div>• output_key: 검색 결과를 저장할 키</div>
                  </div>
                </div>
              )}
              {data?.nodeType === "OutputNode" && (
                <div>
                  <div className="font-bold mb-1">📤 Output Node</div>
                  <div>최종 결과를 포맷팅하여 출력합니다.</div>
                  <div className="mt-1 text-gray-300">
                    <div>• wrap_template: 출력 포맷 템플릿</div>
                    <div>• input_key: 포맷팅할 데이터의 키</div>
                    <div>• output_key: 최종 결과를 저장할 키</div>
                  </div>
                </div>
              )}
            </div>
          </div>
          {/* 삭제 버튼 */}
          <button
            onClick={deleteNode}
            className="w-5 h-5 bg-red-200 hover:bg-red-300 text-red-600 hover:text-red-700 rounded flex items-center justify-center transition-colors duration-200"
            title="노드 삭제"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M10 11v6M14 11v6"/>
            </svg>
          </button>
        </div>
      </div>

      {/* 타입 선택 */}
      <div className="mb-2">
        <label className="text-xs font-bold mr-2">Type:</label>
        <select
          value={data?.nodeType || "PromptNode"}
          onChange={(e) => updateNodeData({ nodeType: e.target.value })}
          className="text-xs border rounded px-1"
        >
          <option value="InputNode">Input Node</option>
          <option value="PromptNode">Prompt Node</option>
          <option value="RetrievalNode">Retrieval Node</option>
          <option value="OutputNode">Output Node</option>
          {/* RAGNode, AlertNode 등 추가 가능 */}
        </select>
      </div>

      {/* input_key / output_key - InputNode는 input_key가 필요 없음 */}
      {data?.nodeType !== "InputNode" && (
        <div className="flex space-x-1 mb-2">
          <label className="text-xs font-bold mr-2">
            {data?.nodeType === "RetrievalNode" ? "query:" : "input_key:"}
          </label>
          <input
            value={data?.input_key || ""}
            onChange={(e) => updateNodeData({ input_key: e.target.value })}
            placeholder="input_key"
            className="flex-1 border rounded px-1 text-xs"
          />
        </div>
      )}
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
                    value={val as string}
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

      {/* InputNode UI */}
      {data?.nodeType === "InputNode" && (
        <>
          <div className="p-2 bg-blue-50 rounded text-xs text-blue-700">
          </div>
        </>
      )}

      {/* OutputNode UI */}
      {data?.nodeType === "OutputNode" && (
        <>
          <div className="space-y-2">
            <div>
              <label className="text-xs font-bold mr-2">wrap_template:</label>
              <textarea
                value={data?.wrap_template || ""}
                onChange={(e) => updateNodeData({ wrap_template: e.target.value })}
                placeholder="AI의 답변입니다:\n{answer}"
                className="w-full border rounded p-1 text-xs"
                rows={3}
              />
            </div>
          </div>
        </>
      )}

      {/* RetrievalNode UI */}
      {data?.nodeType === "RetrievalNode" && (
        <>
          <div className="space-y-2">
            <div>
              <label className="text-xs font-bold mr-2">top_k:</label>
              <input
                value={data?.top_k || ""}
                onChange={(e) => updateNodeData({ top_k: e.target.value })}
                placeholder="상위 결과 개수"
                type="number"
                className="w-full border rounded p-1 text-xs"
              />
            </div>
            
            <div>
              <label className="text-xs font-bold mr-2">collection:</label>
              <input
                value={data?.collection || ""}
                onChange={(e) => updateNodeData({ collection: e.target.value })}
                placeholder="컬렉션 이름(추가 예정)"
                className="w-full border rounded p-1 text-xs"
              />
            </div>
          </div>
        </>
      )}

      <Handle 
        type="target" 
        position={Position.Left} 
        style={{
          width: 12,
          height: 12,
          background: '#6b7280',
          border: '2px solid white',
          borderRadius: '50%',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}
        className="hover:scale-110 transition-transform duration-200"
        title="입력 연결점 (Input)"
      />
      <Handle 
        type="source" 
        position={Position.Right}
        style={{
          width: 12,
          height: 12,
          background: '#6b7280',
          border: '2px solid white',
          borderRadius: '50%',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}
        className="hover:scale-110 transition-transform duration-200"
        title="출력 연결점 (Output)"
      />
    </div>
  );
}
