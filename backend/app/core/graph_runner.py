from typing import Dict, Any
from app.nodes.prompt_node import PromptNode
from langchain_openai import ChatOpenAI

NODE_REGISTRY = {
    "PromptNode": PromptNode,
}


async def run_graph(
    graph_def: Dict[str, Any], llm: ChatOpenAI
) -> Dict[str, Any]:
    """
    graph_def 예시:
    {
      "nodes": [
        {
          "id": "n1",
          "type": "PromptNode",
          "params": {"template": "Hello {name}", "variables": {"name":"Alice"}}
        }
      ],
      "edges": []
    }
    """
    results = {}

    for node_def in graph_def["nodes"]:
        node_type = node_def["type"]
        node_class = NODE_REGISTRY[node_type]
        node = node_class(node_def["id"], node_def["params"], llm=llm)
        results[node.node_id] = await node.run(results)

    return results
