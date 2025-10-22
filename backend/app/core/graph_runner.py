from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from app.nodes.prompt_node import PromptNode
from app.nodes.retrieval_node import RetrievalNode
from app.nodes.input_node import InputNode
from app.nodes.output_node import OutputNode
import logging

logger = logging.getLogger(__name__)


async def run_graph(graph_json: Dict[str, Any], llm):
    """
    그래프를 실행하는 메인 함수

    graph_json 구조 (최신 버전):
    {
      "nodes": [
        {
          "id": "input-1",
          "type": "InputNode",
          "params": {},
          "output_key": "user_input"  # 기본값: "user_input"
        },
        {
          "id": "retrieval-1",
          "type": "RetrievalNode",
          "params": {
            "top_k": 4,
            "collection": "",
            "inputs": {
              "query": {"type": "reference", "value": "user_input"}
            }
          },
          "output_key": "context"
        },
        {
          "id": "prompt-1",
          "type": "PromptNode",
          "params": {
            "system_prompt": "당신은 친절한 AI 어시스턴트입니다.",
            "user_prompt": "질문: {user_input}\\n참고 문서: {context}",
            "assistant_prompt": "",  # Few-shot용 (선택적)
            "inputs": {
              "user_input": {"type": "reference", "value": "user_input"},
              "context": {"type": "reference", "value": "context"}
            }
          },
          "output_key": "answer"
        },
        {
          "id": "output-1",
          "type": "OutputNode",
          "params": {
            "wrap_template": "답변: {answer}",
            "inputs": {
              "answer": {"type": "reference", "value": "answer"}
            }
          },
          "output_key": "agent_output"
        }
      ],
      "edges": [
        {"source": "input-1", "target": "retrieval-1"},
        {"source": "retrieval-1", "target": "prompt-1"},
        {"source": "prompt-1", "target": "output-1"}
      ],
      "input_state": {
        "input": "서울 날씨 어때?"
      }
    }

    하위 호환성:
    - 구버전 input_key/output_key 형식도 지원
    - template → user_prompt 자동 변환
    - variables → inputs 자동 변환
    """
    nodes = graph_json.get("nodes", [])
    edges = graph_json.get("edges", [])
    input_state = graph_json.get("input_state", {})

    logger.info(f"Starting graph execution with {len(nodes)} nodes")

    workflow = StateGraph(dict)
    node_map = {}

    # 1. 노드 생성
    for node in nodes:
        node_id = node["id"]
        node_type = node["type"]
        params = node.get("params", {})
        output_key = node.get("output_key", "output")

        logger.debug(f"Creating node: {node_id} (type: {node_type})")

        try:
            node_impl = _create_node(
                node_type, node_id, params, output_key, node, llm
            )
            workflow.add_node(node_id, node_impl)
            node_map[node_id] = node_impl
        except Exception as e:
            logger.error(f"Failed to create node {node_id}: {e}")
            raise

    # 2. 엣지 연결
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        workflow.add_edge(source, target)
        logger.debug(f"Added edge: {source} -> {target}")

    # 3. 시작/끝 연결
    if nodes:
        workflow.add_edge(START, nodes[0]["id"])
        workflow.add_edge(nodes[-1]["id"], END)
        logger.debug(
            f"Graph flow: START -> {nodes[0]['id']} ... "
            f"{nodes[-1]['id']} -> END"
        )

    # 4. 컴파일
    app = workflow.compile()
    logger.info("Graph compiled successfully")

    # 5. 실행
    logger.info(f"Executing graph with input_state: {input_state}")
    final_state = await app.ainvoke(input_state)
    logger.info("Graph execution completed")

    return final_state


def _create_node(
    node_type: str,
    node_id: str,
    params: Dict[str, Any],
    output_key: str,
    node: Dict[str, Any],
    llm,
):
    """
    노드 타입에 따라 적절한 노드 인스턴스 생성

    하위 호환성을 위한 변환 로직 포함
    """
    if node_type == "InputNode":
        # output_key가 있으면 사용, 없으면 기본값 "user_input"
        return InputNode(
            output=output_key if output_key != "output" else "user_input",
            **params,
        )

    elif node_type == "OutputNode":
        wrap_template = params.get("wrap_template", "")
        inputs = params.get("inputs", {})

        # 하위 호환성: 구버전 input_key 지원
        input_key = node.get("input_key", "")
        if input_key and not inputs:
            logger.warning(
                f"OutputNode({node_id}): Converting legacy input_key "
                f"'{input_key}' to inputs format"
            )
            inputs = {input_key: {"type": "reference", "value": input_key}}

        return OutputNode(
            output=output_key if output_key != "output" else "agent_output",
            wrap_template=wrap_template,
            inputs=inputs,
        )

    elif node_type == "PromptNode":
        system_prompt = params.get("system_prompt", "")
        user_prompt = params.get("user_prompt", "")
        assistant_prompt = params.get("assistant_prompt", "")
        inputs = params.get("inputs", {})

        # 하위 호환성: 구버전 template → user_prompt
        if "template" in params and not user_prompt:
            logger.warning(
                f"PromptNode({node_id}): Converting legacy 'template' "
                f"to 'user_prompt'"
            )
            user_prompt = params["template"]

        # 하위 호환성: 구버전 variables → inputs
        if "variables" in params and not inputs:
            old_vars = params["variables"]
            if isinstance(old_vars, dict):
                logger.warning(
                    f"PromptNode({node_id}): Converting legacy 'variables' "
                    f"to 'inputs' format"
                )
                inputs = {
                    key: {"type": "fixed", "value": val}
                    for key, val in old_vars.items()
                }

        return PromptNode(
            output=output_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            assistant_prompt=assistant_prompt,
            inputs=inputs,
            llm=llm,
        )

    elif node_type == "RetrievalNode":
        top_k = params.get("top_k", 4)
        collection = params.get("collection", "")
        inputs = params.get("inputs", {})

        # 하위 호환성: 구버전 input_key 지원
        input_key = node.get("input_key", "")
        if input_key and not inputs:
            logger.warning(
                f"RetrievalNode({node_id}): Converting legacy input_key "
                f"'{input_key}' to inputs format"
            )
            inputs = {"query": {"type": "reference", "value": input_key}}

        return RetrievalNode(
            output=output_key,
            top_k=top_k,
            collection=collection,
            inputs=inputs,
        )

    else:
        raise ValueError(f"Unknown node type: {node_type}")
