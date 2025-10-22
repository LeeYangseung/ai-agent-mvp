// 스니펫 데이터 타입
export type GraphSnippet = {
  name: string;
  data: {
    nodes: Array<{
      id: string;
      type: string;
      params: any;
      input_key: string;
      output_key: string;
    }>;
    edges: Array<{
      source: string;
      target: string;
    }>;
    input_state: Record<string, string>;
  };
};

// 미리 정의된 스니펫들
export const graphSnippets: GraphSnippet[] = [
  {
    name: "기본 검색 그래프",
    data: {
      nodes: [
        {
          id: "input-1",
          type: "InputNode",
          params: {},
          input_key: "",
          output_key: "user_input"
        },
        {
          id: "prompt-1",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 검색 쿼리를 최적화하는 AI입니다.",
            user_prompt: "사용자 질문을 검색에 적합한 형태로 변환하세요:\n{user_input}",
            assistant_prompt: "",
            inputs: {
              user_input: { type: "reference", value: "user_input" }
            }
          },
          input_key: "",
          output_key: "search_query"
        },
        {
          id: "retrieval-1",
          type: "RetrievalNode",
          params: {
            top_k: 4,
            collection: "",
            inputs: {
              query: { type: "reference", value: "search_query" }
            }
          },
          input_key: "",
          output_key: "context"
        },
        {
          id: "prompt-2",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 친절하고 정확한 답변을 제공하는 AI 어시스턴트입니다.",
            user_prompt: "다음 정보를 바탕으로 사용자 질문에 답변하세요:\n\n질문: {user_input}\n\n참고 자료: {context}",
            assistant_prompt: "",
            inputs: {
              user_input: { type: "reference", value: "user_input" },
              context: { type: "reference", value: "context" }
            }
          },
          input_key: "",
          output_key: "answer"
        },
        {
          id: "output-1",
          type: "OutputNode",
          params: {
            wrap_template: "🤖 AI 답변:\n\n{answer}",
            inputs: {
              answer: { type: "reference", value: "answer" }
            }
          },
          input_key: "",
          output_key: "agent_output"
        }
      ],
      edges: [
        { source: "input-1", target: "prompt-1" },
        { source: "prompt-1", target: "retrieval-1" },
        { source: "retrieval-1", target: "prompt-2" },
        { source: "prompt-2", target: "output-1" }
      ],
      input_state: { input: "보험 해지 시 환급금은 얼마나 받을 수 있나요?" }
    }
  }
];
