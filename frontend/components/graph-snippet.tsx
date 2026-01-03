// 스니펫 데이터 타입
export type GraphSnippet = {
  name: string;
  data: {
    nodes: Array<{
      id: string;
      type: string;
      params: any;
      output: string;
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
          output: "user_input"
        },
        {
          id: "prompt-1",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 검색 쿼리를 최적화하는 AI입니다.",
            user_prompt: "사용자 질문을 검색에 적합한 형태로 변환하세요:\n{user_input}",
            assistant_prompt: "",
            inputs: {
              user_input: { type: "reference", value: "input-1_user_input" }
            }
          },
          output: "search_query"
        },
        {
          id: "retrieval-1",
          type: "RetrievalNode",
          params: {
            top_k: 4,
            collection: "",
            inputs: {
              query: { type: "reference", value: "prompt-1_search_query" }
            }
          },
          output: "context"
        },
        {
          id: "prompt-2",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 친절하고 정확한 답변을 제공하는 AI 어시스턴트입니다.",
            user_prompt: "다음 정보를 바탕으로 사용자 질문에 답변하세요:\n\n질문: {user_input}\n\n참고 자료: {context}",
            assistant_prompt: "",
            inputs: {
              user_input: { type: "reference", value: "input-1_user_input" },
              context: { type: "reference", value: "retrieval-1_context" }
            }
          },
          output: "answer"
        },
        {
          id: "output-1",
          type: "OutputNode",
          params: {
            wrap_template: "🤖 AI 답변:\n\n{answer}",
            inputs: {
              answer: { type: "reference", value: "prompt-2_answer" }
            }
          },
          output: "agent_output"
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
  },
  {
    name: "병렬 분기 + 병합 테스트",
    data: {
      nodes: [
        {
          id: "node-1",
          type: "InputNode",
          params: {},
          output: "user_input"
        },
        {
          id: "node-2",
          type: "ConditionNode",
          params: {
            evaluation_mode: "all_matches",
            inputs: {
              answer: { type: "reference", value: "node-1_user_input" }
            },
            conditions: [
              {
                variable: "answer",
                operator: "==",
                value: "일번",
                target: "node-3"
              },
              {
                variable: "answer",
                operator: "==",
                value: "일번",
                target: "node-4"
              }
            ],
            default_target: "node-5"
          },
          output: "condition_result"
        },
        {
          id: "node-3",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 첫 번째 분기 전문가입니다.",
            user_prompt: "첫 번째 분기로 들어왔습니다: {answer}",
            assistant_prompt: "",
            inputs: {
              answer: { type: "reference", value: "node-1_user_input" }
            }
          },
          output: "branch1_result"
        },
        {
          id: "node-4",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 두 번째 분기 전문가입니다.",
            user_prompt: "두 번째 분기로 들어왔습니다: {answer}",
            assistant_prompt: "",
            inputs: {
              answer: { type: "reference", value: "node-1_user_input" }
            }
          },
          output: "branch2_result"
        },
        {
          id: "node-5",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 기본 경로 전문가입니다.",
            user_prompt: "기본 경로로 들어왔습니다: {answer}",
            assistant_prompt: "",
            inputs: {
              answer: { type: "reference", value: "node-1_user_input" }
            }
          },
          output: "default_result"
        },
        {
          id: "node-6",
          type: "MergeNode",
          params: {
            merge_strategy: "concat",
            separator: "\n\n--- 다음 분기 ---\n\n",
            inputs: {
              branch1: { type: "reference", value: "node-3_branch1_result" },
              branch2: { type: "reference", value: "node-4_branch2_result" }
            }
          },
          output: "merged_output"
        },
        {
          id: "node-7",
          type: "OutputNode",
          params: {
            wrap_template: "🤖 병합된 AI 답변:\n\n{merged}",
            inputs: {
              merged: { type: "reference", value: "node-6_merged_output" }
            }
          },
          output: "agent_output"
        }
      ],
      edges: [
        { source: "node-1", target: "node-2" },
        { source: "node-2", target: "node-3" },
        { source: "node-2", target: "node-4" },
        { source: "node-2", target: "node-5" },
        { source: "node-3", target: "node-6" },
        { source: "node-4", target: "node-6" },
        { source: "node-6", target: "node-7" }
      ],
      input_state: { input: "일번" }
    }
  },
  {
    name: "조건 분기 (First Match)",
    data: {
      nodes: [
        {
          id: "node-1",
          type: "InputNode",
          params: {},
          output: "user_input"
        },
        {
          id: "node-2",
          type: "ConditionNode",
          params: {
            evaluation_mode: "first_match",
            inputs: {
              sentiment: { type: "reference", value: "node-1_user_input" }
            },
            conditions: [
              {
                variable: "sentiment",
                operator: "contains",
                value: "좋아",
                target: "node-3"
              },
              {
                variable: "sentiment",
                operator: "contains",
                value: "나쁘",
                target: "node-4"
              },
              {
                variable: "sentiment",
                operator: "contains",
                value: "싫어",
                target: "node-4"
              }
            ],
            default_target: "node-5"
          },
          output: "condition_result"
        },
        {
          id: "node-3",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 긍정적인 피드백에 공감하는 AI입니다.",
            user_prompt: "사용자가 긍정적인 의견을 주셨습니다: {sentiment}\n\n감사 인사와 함께 더 나은 서비스를 제공하겠다는 메시지를 전달하세요.",
            assistant_prompt: "",
            inputs: {
              sentiment: { type: "reference", value: "node-1_user_input" }
            }
          },
          output: "positive_response"
        },
        {
          id: "node-4",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 부정적인 피드백을 진심으로 경청하는 AI입니다.",
            user_prompt: "사용자가 부정적인 의견을 주셨습니다: {sentiment}\n\n사과와 함께 구체적인 개선 방안을 제시하세요.",
            assistant_prompt: "",
            inputs: {
              sentiment: { type: "reference", value: "node-1_user_input" }
            }
          },
          output: "negative_response"
        },
        {
          id: "node-5",
          type: "PromptNode",
          params: {
            system_prompt: "당신은 중립적인 문의에 친절하게 응대하는 AI입니다.",
            user_prompt: "사용자 의견: {sentiment}\n\n친절하게 추가 정보를 요청하거나 도움을 제공하세요.",
            assistant_prompt: "",
            inputs: {
              sentiment: { type: "reference", value: "node-1_user_input" }
            }
          },
          output: "neutral_response"
        },
        {
          id: "node-6",
          type: "OutputNode",
          params: {
            wrap_template: "💬 고객 센터 응답 (긍정):\n\n{response}",
            inputs: {
              response: { type: "reference", value: "node-3_positive_response" }
            }
          },
          output: "agent_output"
        },
        {
          id: "node-7",
          type: "OutputNode",
          params: {
            wrap_template: "💬 고객 센터 응답 (부정):\n\n{response}",
            inputs: {
              response: { type: "reference", value: "node-4_negative_response" }
            }
          },
          output: "agent_output"
        },
        {
          id: "node-8",
          type: "OutputNode",
          params: {
            wrap_template: "💬 고객 센터 응답 (중립):\n\n{response}",
            inputs: {
              response: { type: "reference", value: "node-5_neutral_response" }
            }
          },
          output: "agent_output"
        }
      ],
      edges: [
        { source: "node-1", target: "node-2" },
        { source: "node-2", target: "node-3" },
        { source: "node-2", target: "node-4" },
        { source: "node-2", target: "node-5" },
        { source: "node-3", target: "node-6" },
        { source: "node-4", target: "node-7" },
        { source: "node-5", target: "node-8" }
      ],
      input_state: { input: "서비스가 좋아요!" }
    }
  }
];
