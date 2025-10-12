from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from app.nodes.prompt_node import PromptNode
from app.nodes.retrieval_node import RetrievalNode
from app.nodes.input_node import InputNode
from app.nodes.output_node import OutputNode

# TODO: RetrievalNode, AlertNode도 같은 방식으로 구현


async def run_graph(graph_json: Dict[str, Any], llm):
    """
    graph_json 예시:
    {
      "nodes": [
        {
          "id": "n1",
          "type": "InputNode",
          "params": {},
          "output_key": "user_question"
        },
        {
          "id": "n2",
          "type": "PromptNode",
          "params": {
            "template": "Rephrase the question: {user_question}"
          },
          "input_key": "user_question",
          "output_key": "query"
        },
        {
          "id": "n3",
          "type": "RetrievalNode",
          "params": {},
          "input_key": "query",
          "output_key": "context"
        },
        {
          "id": "n4",
          "type": "PromptNode",
          "params": {
            "template": "Answer the question: {user_question}\n"
                       "Context: {context}"
          },
          "input_key": "context",
          "output_key": "answer"
        },
        {
          "id": "n5",
          "type": "OutputNode",
          "params": {
            "wrap_template": "AI의 답변입니다:\n{answer}"
          },
          "input_key": "answer",
          "output_key": "final_output"
        }
      ],
      "edges": [
        {"source": "n1", "target": "n2"},
        {"source": "n2", "target": "n3"},
        {"source": "n3", "target": "n4"},
        {"source": "n4", "target": "n5"}
      ],
      "input_state": {
        "input": "서울 날씨 어때?"
      }
    }
    """
    nodes = graph_json.get("nodes", [])
    edges = graph_json.get("edges", [])
    input_state = graph_json.get("input_state", {})

    workflow = StateGraph(dict)
    node_map = {}

    # 1. 노드 생성
    for node in nodes:
        node_id = node["id"]
        node_type = node["type"]
        params = node.get("params", {})
        input_key = node.get("input_key", "input")
        output_key = node.get("output_key", "output")
        k = node.get("k", 4)

        if node_type == "InputNode":
            node_impl = InputNode(
                output_key=output_key,
                **params,
            )
        elif node_type == "OutputNode":
            node_impl = OutputNode(
                input_key=input_key,
                output_key=output_key,
                **params,
            )
        elif node_type == "PromptNode":
            node_impl = PromptNode(
                input_key=input_key,
                output_key=output_key,
                llm=llm,
                **params,
            )
        elif node_type == "RetrievalNode":
            node_impl = RetrievalNode(
                input_key=input_key,
                output_key=output_key,
                k=k,
                **params,
            )
        # elif node_type == "AlertNode":
        #     node_impl = AlertNode(
        #         input_key=input_key, output_key=output_key, **params
        #     )
        else:
            raise ValueError(f"Unknown node type: {node_type}")

        workflow.add_node(node_id, node_impl)
        node_map[node_id] = node_impl

    # 2. 엣지 연결
    for edge in edges:
        workflow.add_edge(edge["source"], edge["target"])

    # 시작/끝 연결
    if nodes:
        workflow.add_edge(START, nodes[0]["id"])
    workflow.add_edge(nodes[-1]["id"], END)

    # 3. 컴파일
    app = workflow.compile()

    # 4. 실행 (초기 state = 사용자 입력)
    final_state = await app.ainvoke(input_state)
    return final_state
