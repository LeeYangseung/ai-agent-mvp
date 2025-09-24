from .base import BaseNode
from langchain.prompts import ChatPromptTemplate


class PromptNode(BaseNode):
    """단순 프롬프트 실행 노드"""

    async def run(self, context):
        if not self.llm:
            raise ValueError("LLM이 제공되지 않았습니다.")
        template = self.params.get("template", "Hello {name}")
        variables = self.params.get("variables", {})

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        result = await chain.ainvoke(variables)

        return {"output": result.content}
