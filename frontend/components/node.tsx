"use client"

import { Handle, Position, NodeProps, useReactFlow } from "reactflow";
import { useState } from "react";

// template에서 {변수} 추출하여 inputs 구조로 변환
function autoExtractInputs(
  systemPrompt: string = "",
  userPrompt: string = "",
  assistantPrompt: string = "",
  currentInputs: Record<string, { type: string; value: string }> = {}
) {
  const regex = /\{([^}]+)\}/g;
  const allText = `${systemPrompt} ${userPrompt} ${assistantPrompt}`;
  const matches = allText.matchAll(regex);

  // 기존 inputs를 먼저 복사 (수동으로 추가한 변수 유지)
  const newInputs: Record<string, { type: string; value: string }> = { ...currentInputs };

  // 프롬프트에서 찾은 변수들을 추가 (이미 있으면 유지)
  for (const m of matches) {
    const key = m[1].trim();
    if (!newInputs[key]) {
      // 새로운 변수만 추가
      newInputs[key] = { type: "reference", value: "" };
    }
  }

  return newInputs;
}

export default function BaseNode({ id, data }: NodeProps) {
  const { setNodes, setEdges, getNodes } = useReactFlow();
  
  // 확장/축소 상태 관리
  const [systemExpanded, setSystemExpanded] = useState(true);
  const [userExpanded, setUserExpanded] = useState(true);
  const [assistantExpanded, setAssistantExpanded] = useState(false);
  
  // 임시 ID 상태 (편집 중인 ID)
  const [tempId, setTempId] = useState(data?.tempId || id);

  // 공통 데이터 업데이트
  const updateNodeData = (patch: Record<string, any>) => {
    setNodes((nds) =>
      nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, ...patch } } : n))
    );
  };

  // 노드 ID 업데이트 (blur 시에만 실제 ID 변경)
  const commitNodeId = () => {
    const newId = tempId.trim();
    if (newId && newId !== id) {
      // 중복 확인
      const nodes = getNodes();
      const isDuplicate = nodes.some(n => n.id === newId && n.id !== id);
      
      if (isDuplicate) {
        alert(`ID "${newId}"는 이미 사용 중입니다.`);
        setTempId(id); // 원래 ID로 되돌림
        return;
      }
      
      setNodes((nds) =>
        nds.map((n) => (n.id === id ? { ...n, id: newId, data: { ...n.data, tempId: newId } } : n))
      );
      // 연결된 엣지들도 업데이트
      setEdges((eds) =>
        eds.map((e) => ({
          ...e,
          source: e.source === id ? newId : e.source,
          target: e.target === id ? newId : e.target,
        }))
      );
    } else if (!newId) {
      // 빈 값이면 원래 ID로 되돌림
      setTempId(id);
    }
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
        return "p-3 rounded-lg shadow-md bg-blue-50 border border-blue-200 w-[380px]";
      case "OutputNode":
        return "p-3 rounded-lg shadow-md bg-green-50 border border-green-200 w-[380px]";
      case "RetrievalNode":
        return "p-3 rounded-lg shadow-md bg-purple-50 border border-purple-200 w-[380px]";
      case "ConditionNode":
        return "p-3 rounded-lg shadow-md bg-yellow-50 border border-yellow-200 w-[480px]";
      case "PromptNode":
      default:
        return "p-3 rounded-lg shadow-md bg-white border border-gray-200 w-[480px]";
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
          {data?.nodeType === "ConditionNode" && "🔀 Condition Node"}
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
                  <div className="mt-1 text-gray-300">
                    <div>• output: user_input (고정값)</div>
                    <div className="text-gray-400 text-[10px] mt-1">
                      사용자 입력이 항상 'user_input' 키로 저장됩니다
                    </div>
                  </div>
                </div>
              )}
              {data?.nodeType === "PromptNode" && (
                <div>
                  <div className="font-bold mb-1">💬 Prompt Node</div>
                  <div>LLM에 프롬프트를 전송하여 답변을 생성합니다.</div>
                  <div className="mt-1 text-gray-300">
                    <div>• system_prompt: 시스템 역할 정의</div>
                    <div>• user_prompt: 사용자 요청 프롬프트</div>
                    <div>• assistant_prompt: Few-shot 예시 (선택)</div>
                    <div>• inputs: 프롬프트에 사용할 변수들</div>
                    <div>• output: 생성된 답변을 저장할 키</div>
                  </div>
                </div>
              )}
              {data?.nodeType === "RetrievalNode" && (
                <div>
                  <div className="font-bold mb-1">🔍 Retrieval Node</div>
                  <div>벡터 데이터베이스에서 관련 문서를 검색합니다.</div>
                  <div className="mt-1 text-gray-300">
                    <div>• top_k: 검색할 상위 문서 개수</div>
                    <div>• collection: 검색할 컬렉션 (추후 구현)</div>
                    <div>• inputs: 검색에 사용할 변수 (query 등)</div>
                    <div>• output: 검색 결과를 저장할 키</div>
                  </div>
                </div>
              )}
              {data?.nodeType === "OutputNode" && (
                <div>
                  <div className="font-bold mb-1">📤 Output Node</div>
                  <div>최종 결과를 포맷팅하여 출력합니다.</div>
                  <div className="mt-1 text-gray-300">
                    <div>• wrap_template: 출력 포맷 템플릿</div>
                    <div>• inputs: 템플릿에 사용할 변수들</div>
                    <div>• output: agent_output (고정값)</div>
                    <div className="text-gray-400 text-[10px] mt-1">
                      최종 결과가 항상 'agent_output' 키로 저장됩니다
                    </div>
                  </div>
                </div>
              )}
              {data?.nodeType === "ConditionNode" && (
                <div>
                  <div className="font-bold mb-1">🔀 Condition Node</div>
                  <div>조건에 따라 다른 노드로 분기합니다.</div>
                  <div className="mt-1 text-gray-300">
                    <div>• inputs: 조건 평가에 사용할 변수들</div>
                    <div>• conditions: IF/ELSE IF/ELSE 조건 목록</div>
                    <div className="text-gray-400 text-[10px] mt-1">
                      각 조건마다 연결선으로 다음 노드 지정
                    </div>
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

      {/* 노드 ID 편집 */}
      <div className="mb-2 flex items-center">
        <label className="text-xs font-bold mr-2">ID:</label>
        <input
          value={tempId}
          onChange={(e) => setTempId(e.target.value)}
          onBlur={commitNodeId}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.currentTarget.blur(); // Enter 시 blur 트리거
            }
          }}
          placeholder="node-id"
          className="flex-1 border rounded px-1 text-xs w-full"
        />
      </div>

      {/* PromptNode UI */}
      {data?.nodeType === "PromptNode" && (
        <>
          {/* System Prompt */}
          <div className="mb-2">
            <button
              onClick={() => setSystemExpanded(!systemExpanded)}
              className="flex items-center justify-between w-full text-xs font-bold mb-1 hover:text-blue-600"
            >
              <span>System Prompt:</span>
              <span>{systemExpanded ? "▼" : "▶"}</span>
            </button>
            {systemExpanded && (
              <textarea
                value={data?.system_prompt || ""}
                onChange={(e) =>
                  updateNodeData({
                    system_prompt: e.target.value,
                    inputs: autoExtractInputs(
                      e.target.value,
                      data?.user_prompt || "",
                      data?.assistant_prompt || "",
                      data?.inputs || {}
                    ),
                  })
                }
                placeholder="You are a helpful assistant..."
                className="w-full border rounded p-1 text-xs"
                rows={2}
              />
            )}
          </div>

          {/* User Prompt */}
          <div className="mb-2">
            <button
              onClick={() => setUserExpanded(!userExpanded)}
              className="flex items-center justify-between w-full text-xs font-bold mb-1 hover:text-blue-600"
            >
              <span>User Prompt:</span>
              <span>{userExpanded ? "▼" : "▶"}</span>
            </button>
            {userExpanded && (
          <textarea
                value={data?.user_prompt || ""}
            onChange={(e) =>
              updateNodeData({
                    user_prompt: e.target.value,
                    inputs: autoExtractInputs(
                      data?.system_prompt || "",
                      e.target.value,
                      data?.assistant_prompt || "",
                      data?.inputs || {}
                    ),
                  })
                }
                placeholder="Answer the question: {user_question}"
                className="w-full border rounded p-1 text-xs"
            rows={3}
          />
            )}
          </div>

          {/* Assistant Prompt (선택적) */}
          <div className="mb-2">
            <button
              onClick={() => setAssistantExpanded(!assistantExpanded)}
              className="flex items-center justify-between w-full text-xs font-bold mb-1 hover:text-blue-600"
            >
              <span>Assistant Prompt (선택):</span>
              <span>{assistantExpanded ? "▼" : "▶"}</span>
            </button>
            {assistantExpanded && (
              <textarea
                value={data?.assistant_prompt || ""}
                onChange={(e) =>
                  updateNodeData({
                    assistant_prompt: e.target.value,
                    inputs: autoExtractInputs(
                      data?.system_prompt || "",
                      data?.user_prompt || "",
                      e.target.value,
                      data?.inputs || {}
                    ),
                  })
                }
                placeholder="Few-shot example..."
                className="w-full border rounded p-1 text-xs"
                rows={2}
              />
            )}
          </div>

          {/* Inputs / Output 레이아웃 */}
          <div className="mt-3 pt-3 border-t space-y-2">
            {/* Inputs */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-bold">Inputs:</label>
                <button
                  onClick={() => {
                    const newKey = `var_${Object.keys(data?.inputs || {}).length + 1}`;
                    const newInputs = { 
                      ...(data?.inputs || {}), 
                      [newKey]: { type: "reference", value: "" } 
                    };
                    updateNodeData({ inputs: newInputs });
                  }}
                  className="text-[10px] px-2 py-0.5 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded"
                  title="입력 추가"
                >
                  + 추가
                </button>
              </div>
          <div className="space-y-1">
                {data?.inputs &&
                  Object.entries(data.inputs).map(([key, config]: [string, any], index: number) => {
                    // 사용 가능한 output 목록 가져오기
                    const availableOutputs = getNodes()
                      .filter((n) => n.id !== id) // 자기 자신 제외
                      .map((n) => {
                        // InputNode는 user_input을 출력
                        if (n.data?.nodeType === "InputNode") {
                          return { id: n.id, output: "user_input" };
                        }
                        // OutputNode는 agent_output을 출력
                        if (n.data?.nodeType === "OutputNode") {
                          return { id: n.id, output: "agent_output" };
                        }
                        // 기타 노드는 data.output 사용
                        return { 
                          id: n.id, 
                          output: n.data?.output  || "output" 
                        };
                      });

                    return (
                      <div key={index} className="flex items-center gap-1">
                        {/* 변수명 */}
                        <input
                          value={key}
                          onChange={(e) => {
                            const newInputs = { ...data.inputs };
                            const value = newInputs[key];
                            delete newInputs[key];
                            newInputs[e.target.value] = value;
                            updateNodeData({ inputs: newInputs });
                          }}
                          className="w-20 border rounded px-1 text-[10px] font-mono bg-gray-50"
                          placeholder="변수명"
                        />
                        
                        {/* 타입 전환 버튼 */}
                        <button
                          onClick={() => {
                            const newInputs = { ...data.inputs };
                            const newType = config.type === "fixed" ? "reference" : "fixed";
                            newInputs[key] = { ...config, type: newType, value: "" };
                            updateNodeData({ inputs: newInputs });
                          }}
                          className="w-5 h-5 border rounded text-[9px] font-bold bg-white hover:bg-gray-100"
                          title={config.type === "fixed" ? "고정값 → 참조" : "참조 → 고정값"}
                        >
                          {config.type === "fixed" ? "T" : "→"}
                        </button>

                        {/* 값 입력 */}
                        {config.type === "fixed" ? (
                          <input
                            value={config.value || ""}
                            onChange={(e) => {
                              const newInputs = { ...data.inputs };
                              newInputs[key] = { ...config, value: e.target.value };
                              updateNodeData({ inputs: newInputs });
                            }}
                            placeholder="고정값"
                            className="flex-1 border rounded px-1 text-[10px]"
                          />
                        ) : (
                          <select
                            value={config.value || ""}
                            onChange={(e) => {
                              const newInputs = { ...data.inputs };
                              newInputs[key] = { ...config, value: e.target.value };
                              updateNodeData({ inputs: newInputs });
                            }}
                            className="flex-1 border rounded px-1 text-[10px]"
                          >
                            <option value="">선택하세요</option>
                            {availableOutputs.map((opt) => (
                              <option key={opt.id} value={opt.output}>
                                {opt.id}.{opt.output}
                              </option>
                            ))}
                          </select>
                        )}

                        {/* 삭제 버튼 */}
                        <button
                          onClick={() => {
                            const newInputs = { ...data.inputs };
                            delete newInputs[key];
                            updateNodeData({ inputs: newInputs });
                          }}
                          className="w-5 h-5 bg-red-100 hover:bg-red-200 text-red-600 rounded flex items-center justify-center text-xs"
                          title="삭제"
                        >
                          ×
                        </button>
                      </div>
                    );
                  })}
                {(!data?.inputs || Object.keys(data.inputs).length === 0) && (
                  <div className="text-[10px] text-gray-400 italic">
                    프롬프트에 {"{변수}"} 추가하거나 + 추가 버튼 클릭
                  </div>
                )}
              </div>
            </div>

            {/* Output */}
            <div className="flex items-center gap-2">
              <label className="text-xs font-bold w-16">Output:</label>
                  <input
                value={data?.output || ""}
                    onChange={(e) =>
                      updateNodeData({
                    output: e.target.value,
                      })
                    }
                placeholder="answer"
                    className="flex-1 border rounded px-1 text-xs"
                  />
                </div>
          </div>
        </>
      )}

      {/* InputNode UI */}
      {data?.nodeType === "InputNode" && (
        <>
          <div className="mb-2">
            <label className="text-xs font-bold mr-2">Output:</label>
            <input
              value="user_input"
              readOnly
              className="w-full border rounded p-1 text-xs bg-gray-100 cursor-not-allowed"
              title="InputNode의 출력은 항상 'user_input'으로 고정됩니다"
            />
            <div className="mt-1 text-[10px] text-gray-500 italic">
              * 사용자 입력이 이 키로 저장됩니다 (수정 불가)
            </div>
          </div>
        </>
      )}

      {/* OutputNode UI */}
      {data?.nodeType === "OutputNode" && (
        <>
          {/* wrap_template */}
          <div className="mb-2">
              <label className="text-xs font-bold mr-2">wrap_template:</label>
              <textarea
                value={data?.wrap_template || ""}
              onChange={(e) =>
                updateNodeData({
                  wrap_template: e.target.value,
                  inputs: autoExtractInputs(
                    "",
                    e.target.value,
                    "",
                    data?.inputs || {}
                  ),
                })
              }
              placeholder="🤖 AI 답변:\n\n{answer}\n\n---\n질문: {user_input}"
                className="w-full border rounded p-1 text-xs"
              rows={4}
            />
          </div>

          {/* Inputs / Output 레이아웃 */}
          <div className="mt-3 pt-3 border-t space-y-2">
            {/* Inputs */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-bold">Inputs:</label>
                <button
                  onClick={() => {
                    const newKey = `var_${Object.keys(data?.inputs || {}).length + 1}`;
                    const newInputs = { 
                      ...(data?.inputs || {}), 
                      [newKey]: { type: "reference", value: "" } 
                    };
                    updateNodeData({ inputs: newInputs });
                  }}
                  className="text-[10px] px-2 py-0.5 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded"
                  title="입력 추가"
                >
                  + 추가
                </button>
              </div>
              <div className="space-y-1">
                {data?.inputs &&
                  Object.entries(data.inputs).map(([key, config]: [string, any], index: number) => {
                    const availableOutputs = getNodes()
                      .filter((n) => n.id !== id)
                      .map((n) => {
                        // InputNode는 user_input을 출력
                        if (n.data?.nodeType === "InputNode") {
                          return { id: n.id, output: "user_input" };
                        }
                        // OutputNode는 agent_output을 출력
                        if (n.data?.nodeType === "OutputNode") {
                          return { id: n.id, output: "agent_output" };
                        }
                        // 기타 노드는 data.output 사용
                        return { 
                          id: n.id, 
                          output: n.data?.output || "output" 
                        };
                      });

                    return (
                      <div key={index} className="flex items-center gap-1">
                        {/* 변수명 */}
                        <input
                          value={key}
                          onChange={(e) => {
                            const newInputs = { ...data.inputs };
                            const value = newInputs[key];
                            delete newInputs[key];
                            newInputs[e.target.value] = value;
                            updateNodeData({ inputs: newInputs });
                          }}
                          className="w-20 border rounded px-1 text-[10px] font-mono bg-gray-50"
                          placeholder="변수명"
                        />
                        
                        {/* 타입 전환 버튼 */}
                        <button
                          onClick={() => {
                            const newInputs = { ...data.inputs };
                            const newType = config.type === "fixed" ? "reference" : "fixed";
                            newInputs[key] = { ...config, type: newType, value: "" };
                            updateNodeData({ inputs: newInputs });
                          }}
                          className="w-5 h-5 border rounded text-[9px] font-bold bg-white hover:bg-gray-100"
                          title={config.type === "fixed" ? "고정값 → 참조" : "참조 → 고정값"}
                        >
                          {config.type === "fixed" ? "T" : "→"}
                        </button>

                        {/* 값 입력 */}
                        {config.type === "fixed" ? (
                          <input
                            value={config.value || ""}
                            onChange={(e) => {
                              const newInputs = { ...data.inputs };
                              newInputs[key] = { ...config, value: e.target.value };
                              updateNodeData({ inputs: newInputs });
                            }}
                            placeholder="고정값"
                            className="flex-1 border rounded px-1 text-[10px]"
                          />
                        ) : (
                          <select
                            value={config.value || ""}
                            onChange={(e) => {
                              const newInputs = { ...data.inputs };
                              newInputs[key] = { ...config, value: e.target.value };
                              updateNodeData({ inputs: newInputs });
                            }}
                            className="flex-1 border rounded px-1 text-[10px]"
                          >
                            <option value="">선택하세요</option>
                            {availableOutputs.map((opt) => (
                              <option key={opt.id} value={opt.output}>
                                {opt.id}.{opt.output}
                              </option>
                            ))}
                          </select>
                        )}

                        {/* 삭제 버튼 */}
                        <button
                          onClick={() => {
                            const newInputs = { ...data.inputs };
                            delete newInputs[key];
                            updateNodeData({ inputs: newInputs });
                          }}
                          className="w-5 h-5 bg-red-100 hover:bg-red-200 text-red-600 rounded flex items-center justify-center text-xs"
                          title="삭제"
                        >
                          ×
                        </button>
                      </div>
                    );
                  })}
                {(!data?.inputs || Object.keys(data.inputs).length === 0) && (
                  <div className="text-[10px] text-gray-400 italic">
                    wrap_template에 {"{변수}"} 추가하거나 + 추가 버튼 클릭
                  </div>
                )}
              </div>
            </div>

            {/* Output (고정값) */}
            <div>
              <label className="text-xs font-bold mr-2">Output:</label>
              <input
                value="agent_output"
                readOnly
                className="w-full border rounded p-1 text-xs bg-gray-100 cursor-not-allowed"
                title="OutputNode의 출력은 항상 'agent_output'으로 고정됩니다"
              />
              <div className="mt-1 text-[10px] text-gray-500 italic">
                * 최종 결과가 이 키로 저장됩니다 (수정 불가)
              </div>
            </div>
          </div>
        </>
      )}

      {/* RetrievalNode UI */}
      {data?.nodeType === "RetrievalNode" && (
        <>
          {/* top_k */}
          <div className="mb-2">
              <label className="text-xs font-bold mr-2">top_k:</label>
              <input
              value={data?.top_k || 4}
              onChange={(e) => updateNodeData({ top_k: parseInt(e.target.value) || 4 })}
              placeholder="4"
                type="number"
                className="w-full border rounded p-1 text-xs"
              />
            </div>
            
          {/* collection */}
          <div className="mb-2">
              <label className="text-xs font-bold mr-2">collection:</label>
              <input
                value={data?.collection || ""}
                onChange={(e) => updateNodeData({ collection: e.target.value })}
              placeholder="컬렉션 이름 (추후 구현)"
                className="w-full border rounded p-1 text-xs"
            />
          </div>

          {/* Inputs / Output 레이아웃 */}
          <div className="mt-3 pt-3 border-t space-y-2">
            {/* Inputs */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-bold">Inputs:</label>
                <button
                  onClick={() => {
                    const newKey = `var_${Object.keys(data?.inputs || {}).length + 1}`;
                    const newInputs = { 
                      ...(data?.inputs || {}), 
                      [newKey]: { type: "reference", value: "" } 
                    };
                    updateNodeData({ inputs: newInputs });
                  }}
                  className="text-[10px] px-2 py-0.5 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded"
                  title="입력 추가"
                >
                  + 추가
                </button>
              </div>
              <div className="space-y-1">
                {data?.inputs &&
                  Object.entries(data.inputs).map(([key, config]: [string, any], index: number) => {
                    const availableOutputs = getNodes()
                      .filter((n) => n.id !== id)
                      .map((n) => {
                        // InputNode는 user_input을 출력
                        if (n.data?.nodeType === "InputNode") {
                          return { id: n.id, output: "user_input" };
                        }
                        // OutputNode는 agent_output을 출력
                        if (n.data?.nodeType === "OutputNode") {
                          return { id: n.id, output: "agent_output" };
                        }
                        // 기타 노드는 data.output 사용
                        return { 
                          id: n.id, 
                          output: n.data?.output || "output" 
                        };
                      });

                    return (
                      <div key={index} className="flex items-center gap-1">
                        {/* 변수명 */}
                        <input
                          value={key}
                          onChange={(e) => {
                            const newInputs = { ...data.inputs };
                            const value = newInputs[key];
                            delete newInputs[key];
                            newInputs[e.target.value] = value;
                            updateNodeData({ inputs: newInputs });
                          }}
                          className="w-20 border rounded px-1 text-[10px] font-mono bg-gray-50"
                          placeholder="변수명"
                        />
                        
                        {/* 타입 전환 버튼 */}
                        <button
                          onClick={() => {
                            const newInputs = { ...data.inputs };
                            const newType = config.type === "fixed" ? "reference" : "fixed";
                            newInputs[key] = { ...config, type: newType, value: "" };
                            updateNodeData({ inputs: newInputs });
                          }}
                          className="w-5 h-5 border rounded text-[9px] font-bold bg-white hover:bg-gray-100"
                          title={config.type === "fixed" ? "고정값 → 참조" : "참조 → 고정값"}
                        >
                          {config.type === "fixed" ? "T" : "→"}
                        </button>

                        {/* 값 입력 */}
                        {config.type === "fixed" ? (
                          <input
                            value={config.value || ""}
                            onChange={(e) => {
                              const newInputs = { ...data.inputs };
                              newInputs[key] = { ...config, value: e.target.value };
                              updateNodeData({ inputs: newInputs });
                            }}
                            placeholder="고정값"
                            className="flex-1 border rounded px-1 text-[10px]"
                          />
                        ) : (
                          <select
                            value={config.value || ""}
                            onChange={(e) => {
                              const newInputs = { ...data.inputs };
                              newInputs[key] = { ...config, value: e.target.value };
                              updateNodeData({ inputs: newInputs });
                            }}
                            className="flex-1 border rounded px-1 text-[10px]"
                          >
                            <option value="">선택하세요</option>
                            {availableOutputs.map((opt) => (
                              <option key={opt.id} value={opt.output}>
                                {opt.id}.{opt.output}
                              </option>
                            ))}
                          </select>
                        )}

                        {/* 삭제 버튼 */}
                        <button
                          onClick={() => {
                            const newInputs = { ...data.inputs };
                            delete newInputs[key];
                            updateNodeData({ inputs: newInputs });
                          }}
                          className="w-5 h-5 bg-red-100 hover:bg-red-200 text-red-600 rounded flex items-center justify-center text-xs"
                          title="삭제"
                        >
                          ×
                        </button>
                      </div>
                    );
                  })}
                {(!data?.inputs || Object.keys(data.inputs).length === 0) && (
                  <div className="text-[10px] text-gray-400 italic">
                    + 추가 버튼으로 입력 변수 추가
                  </div>
                )}
              </div>
            </div>

            {/* Output */}
            <div className="flex items-center gap-2">
              <label className="text-xs font-bold w-16">Output:</label>
              <input
                value={data?.output || ""}
                onChange={(e) =>
                  updateNodeData({
                    output: e.target.value,
                  })
                }
                placeholder="context"
                className="flex-1 border rounded px-1 text-xs"
              />
            </div>
          </div>
        </>
      )}

      {/* ConditionNode UI */}
      {data?.nodeType === "ConditionNode" && (
        <>
            {/* Conditions 섹션 */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-bold">Conditions:</label>
                <button
                  onClick={() => {
                    const newConditions = [...(data.conditions || [])];
                    const availableInputs = Object.keys(data.inputs || {});
                    newConditions.push({
                      variable: availableInputs[0] || "",
                      operator: "==",
                      value: "",
                      target: "",
                    });
                    updateNodeData({ conditions: newConditions });
                  }}
                  className="px-2 py-0.5 bg-yellow-100 hover:bg-yellow-200 text-yellow-700 rounded text-[10px]"
                >
                  + 조건 추가
                </button>
              </div>
              <div className="space-y-2">
                {data?.conditions &&
                  data.conditions.map((cond: any, index: number) => {
                    const inputVars = Object.keys(data.inputs || {});

                    return (
                      <div key={index} className="border border-yellow-300 rounded p-2 bg-yellow-50 relative">
                        <div className="text-[10px] font-bold text-yellow-700 mb-1">
                          {index === 0 ? "IF" : `ELSE IF ${index}`}
                        </div>
                        <div className="space-y-1">
                          {/* Variable selector */}

                          <div className="flex gap-1">
                            <select
                              value={cond.variable || ""}
                              onChange={(e) => {
                                const newConditions = [...(data.conditions || [])];
                                newConditions[index] = { ...cond, variable: e.target.value };
                                updateNodeData({ conditions: newConditions });
                              }}
                              className="w-full border rounded px-1 text-[10px]"
                            >
                              <option value="">변수 선택</option>
                              {inputVars.map((v) => (
                                <option key={v} value={v}>
                                  {v}
                                </option>
                              ))}
                            </select>
                            <button
                              onClick={() => {
                                const newConditions = [...(data.conditions || [])];
                                newConditions.splice(index, 1);
                                updateNodeData({ conditions: newConditions });
                              }}
                              className="w-5 h-5 bg-red-100 hover:bg-red-200 text-red-600 rounded flex items-center justify-center text-xs"
                              title="조건 삭제"
                            >
                              ×
                            </button>
                          </div>

                          <div className="flex gap-1">
                            {/* Operator selector */}
                            <select
                              value={cond.operator || "=="}
                              onChange={(e) => {
                                const newConditions = [...(data.conditions || [])];
                                newConditions[index] = { ...cond, operator: e.target.value };
                                updateNodeData({ conditions: newConditions });
                              }}
                              className="flex-1 border rounded px-1 text-[10px]"
                            >
                              <option value="==">==</option>
                              <option value="!=">!=</option>
                              <option value="<>">{"<>"}</option>
                              <option value=">">{">"}</option>
                              <option value=">=">{">="}</option>
                              <option value="<">{"<"}</option>
                              <option value="<=">{"<="}</option>
                              <option value="contains">포함</option>
                              <option value="not_contains">불포함</option>
                              <option value="starts_with">시작</option>
                              <option value="ends_with">종료</option>
                            </select>

                            {/* Comparison value */}
                            <input
                              value={cond.value || ""}
                              onChange={(e) => {
                                const newConditions = [...(data.conditions || [])];
                                newConditions[index] = { ...cond, value: e.target.value };
                                updateNodeData({ conditions: newConditions });
                              }}
                              placeholder="비교값"
                              className="flex-1 border rounded px-1 text-[10px]"
                            />
                          </div>
                        </div>
                        
                      </div>
                    );
                  })}
                {(!data?.conditions || data.conditions.length === 0) && (
                  <div className="text-[10px] text-gray-400 italic">
                    + 조건 추가 버튼으로 IF/ELSE IF 조건 추가
                  </div>
                )}
              </div>
            </div>

            {/* ELSE (default_target) 섹션 */}
            <div className="mt-2">
              <div className="border border-yellow-300 rounded p-2 bg-yellow-50 relative">
                <div className="text-[10px] font-bold text-yellow-700 mb-1">ELSE</div>
                <div className="text-[10px] text-gray-600">
                  모든 조건이 거짓일 때 실행되는 기본 경로입니다.
                  <br />
                  연결선을 통해 다음 노드를 지정하세요.
                </div>
              </div>
            </div>
            {/* Inputs 섹션 */}
            <div className="space-y-2 mt-2">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-bold">Inputs:</label>
                  <button
                    onClick={() => {
                      const newInputs = { ...data.inputs };
                      const newKey = `var_${Object.keys(newInputs).length + 1}`;
                      newInputs[newKey] = { type: "reference", value: "" };
                      updateNodeData({ inputs: newInputs });
                    }}
                    className="px-2 py-0.5 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded text-[10px]"
                  >
                    + 추가
                  </button>
                </div>
                <div className="space-y-1">
                  {data?.inputs &&
                    Object.entries(data.inputs).map(([key, config]: [string, any], index) => {
                      const availableOutputs = getNodes()
                        .filter((n) => n.id !== id)
                        .map((n) => {
                          // InputNode는 user_input을 출력
                          if (n.data?.nodeType === "InputNode") {
                            return { id: n.id, output: "user_input" };
                          }
                          // OutputNode는 agent_output을 출력
                          if (n.data?.nodeType === "OutputNode") {
                            return { id: n.id, output: "agent_output" };
                          }
                          // 기타 노드는 data.output 사용
                          return { 
                            id: n.id, 
                            output: n.data?.output || "output" 
                          };
                        });

                      return (
                        <div key={index} className="flex items-center gap-1">
                          <input
                            value={key}
                            onChange={(e) => {
                              const newInputs = { ...data.inputs };
                              const value = newInputs[key];
                              delete newInputs[key];
                              newInputs[e.target.value] = value;
                              updateNodeData({ inputs: newInputs });
                            }}
                            className="w-20 border rounded px-1 text-[10px] font-mono bg-gray-50"
                            placeholder="변수명"
                          />
                          
                          <button
                            onClick={() => {
                              const newInputs = { ...data.inputs };
                              const newType = config.type === "fixed" ? "reference" : "fixed";
                              newInputs[key] = { ...config, type: newType, value: "" };
                              updateNodeData({ inputs: newInputs });
                            }}
                            className="w-5 h-5 border rounded text-[9px] font-bold bg-white hover:bg-gray-100"
                            title={config.type === "fixed" ? "고정값 → 참조" : "참조 → 고정값"}
                          >
                            {config.type === "fixed" ? "T" : "→"}
                          </button>

                          {config.type === "fixed" ? (
                            <input
                              value={config.value || ""}
                              onChange={(e) => {
                                const newInputs = { ...data.inputs };
                                newInputs[key] = { ...config, value: e.target.value };
                                updateNodeData({ inputs: newInputs });
                              }}
                              placeholder="고정값"
                              className="flex-1 border rounded px-1 text-[10px]"
                            />
                          ) : (
                            <select
                              value={config.value || ""}
                              onChange={(e) => {
                                const newInputs = { ...data.inputs };
                                newInputs[key] = { ...config, value: e.target.value };
                                updateNodeData({ inputs: newInputs });
                              }}
                              className="flex-1 border rounded px-1 text-[10px]"
                            >
                              <option value="">선택하세요</option>
                              {availableOutputs.map((opt) => (
                                <option key={opt.id} value={opt.output}>
                                  {opt.id}.{opt.output}
                                </option>
                              ))}
                            </select>
                          )}

                          <button
                            onClick={() => {
                              const newInputs = { ...data.inputs };
                              delete newInputs[key];
                              updateNodeData({ inputs: newInputs });
                            }}
                            className="w-5 h-5 bg-red-100 hover:bg-red-200 text-red-600 rounded flex items-center justify-center text-xs"
                            title="삭제"
                          >
                            ×
                          </button>
                        </div>
                      );
                    })}
                  {(!data?.inputs || Object.keys(data.inputs).length === 0) && (
                    <div className="text-[10px] text-gray-400 italic">
                      + 추가 버튼으로 입력 변수 추가
                    </div>
                  )}
                </div>
              </div>
            </div>
        </>
      )}

      {/* Input Handle (모든 노드 공통) */}
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

      {/* Output Handles - ConditionNode는 조건별로 여러 개 */}
      {data?.nodeType === "ConditionNode" ? (
        <>
          {/* 각 조건마다 별도의 source handle */}
          {data?.conditions && data.conditions.map((cond: any, index: number) => {
            // 각 조건 블록의 중간 지점에 위치하도록 계산
            // 헤더(80px) + 조건들 위쪽 여백(8px) + 각 조건 블록 높이(85px) * index + 조건 블록 높이의 절반(42.5px)
            const topPosition = 80 + 8 + (index * 85) + 42.5;
            
            return (
              <Handle
                key={`condition-${index}`}
                type="source"
                position={Position.Right}
                id={`condition-${index}`}
                style={{
                  top: `${topPosition}px`,
                  width: 12,
                  height: 12,
                  background: '#6b7280',
                  border: '2px solid white',
                  borderRadius: '50%',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                }}
                className="hover:scale-110 transition-transform duration-200"
                title={`${index === 0 ? 'IF' : `ELSE IF ${index}`} 경로`}
              />
            );
          })}
          
          {/* ELSE handle */}
          <Handle
            key="else"
            type="source"
            position={Position.Right}
            id="else"
            style={{
              top: 'calc(100% - 95px)', // ELSE 섹션의 중간 지점
              width: 12,
              height: 12,
              background: '#6b7280',
              border: '2px solid white',
              borderRadius: '50%',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
            }}
            className="hover:scale-110 transition-transform duration-200"
            title="ELSE 경로"
          />
        </>
      ) : (
        /* 일반 노드는 단일 source handle */
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
      )}
    </div>
  );
}
