from typing import Dict, Any, Optional, List
from langchain_community.vectorstores import Chroma
from .base import BaseNode
from app.utils.vector_store import (
    get_vector_store,
    search_documents,
    search_documents_with_score,
)


class RetrievalNode(BaseNode):
    """벡터 검색 노드"""

    def __init__(
        self,
        input_key: str,
        output_key: str,
        k: int = 4,
        vector_store: Optional[Chroma] = None,
        **kwargs,
    ):
        super().__init__(input_key, output_key, **kwargs)
        self.k = k  # 검색할 문서 개수
        self.vector_store = vector_store or get_vector_store()

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        # 1. input_key를 기준으로 state에서 검색 쿼리 추출
        query = state.get(self.input_key, "")
        if not query:
            raise ValueError(
                f"Query not found in state with key: {self.input_key}"
            )

        # 2. 벡터 검색 수행
        try:
            docs = search_documents(
                query, k=self.k, vector_store=self.vector_store
            )

            # 3. 검색 결과를 문자열로 변환
            retrieved_content = []
            for doc in docs:
                retrieved_content.append(doc.page_content)

            # 4. 결과를 output_key에 저장
            new_state = dict(state)
            new_state[self.output_key] = retrieved_content

            return new_state

        except Exception as e:
            raise RuntimeError(f"Vector search failed: {str(e)}")

    def similarity_search_with_score(
        self, query: str, k: int = None
    ) -> List[tuple]:
        """유사도 점수와 함께 검색"""
        k = k or self.k
        return search_documents_with_score(
            query, k=k, vector_store=self.vector_store
        )
