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
    name: "검색 그래프",
    data: {
      nodes: [
        {
          id: "node-1",
          type: "PromptNode",
          params: {
            template: "사용자 입력을 받아 검색을 위한 질문 형태로 변환하세요.\n## 사용자 입력\n{input}\n## 질문",
            variables: { input: "" }
          },
          input_key: "input",
          output_key: "query"
        },
        {
          id: "node-2",
          type: "RetrievalNode",
          params: {
            template: "",
            variables: {}
          },
          input_key: "query",
          output_key: "context"
        },
        {
          id: "node-3",
          type: "PromptNode",
          params: {
            template: "당신은 사용자 질문에 자세히 답변하는 도우미입니다.\n사용자 입력과 질문, 문맥을 참고해 답변하세요.\n\n## 사용자 입력\n{input}\n\n## 질문\n{query}\n\n## 문맥\n{context}\n\n## 답변",
            variables: { input: "", query: "", context: "" }
          },
          input_key: "context",
          output_key: "output"
        }
      ],
      edges: [
        { source: "node-1", target: "node-2" },
        { source: "node-2", target: "node-3" }
      ],
      input_state: { input: "해지환급금 기준 알려줘" }
    }
  }
];
