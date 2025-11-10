from typing import Dict, Any, Optional, List
from langchain_community.vectorstores import Chroma
from .base import BaseNode
from app.utils.vector_store import (
    get_vector_store,
    search_documents,
    search_documents_with_score,
)
import logging

logger = logging.getLogger(__name__)


class RetrievalNode(BaseNode):
    """벡터 검색 노드"""

    def __init__(
        self,
        output: str,
        top_k: int = 4,
        collection: str = "default",
        inputs: Dict[str, Dict[str, str]] = None,
        vector_store: Optional[Chroma] = None,
        **kwargs,
    ):
        """
        Args:
            output: 출력을 저장할 키
            top_k: 검색할 상위 문서 개수
            collection: 검색할 컬렉션 이름
            inputs: 입력 변수들
                   예: {"query": {"type": "reference", "value": "user_input"}}
            vector_store: 벡터 스토어 인스턴스
        """
        super().__init__(output=output, **kwargs)
        self.top_k = top_k
        self.collection = collection or "default"
        self.inputs = inputs or {}

        # collection 이름으로 vector_store 초기화
        if vector_store:
            self.vector_store = vector_store
        else:
            self.vector_store = get_vector_store(
                collection_name=self.collection
            )

        logger.info(
            f"RetrievalNode({self.output}): "
            f"Initialized with collection='{self.collection}'"
        )

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        try:
            # 0. 그래프 상태 확인
            if state.get("graph_status") == "failed":
                return state
            # 1. BaseNode의 공통 메서드로 inputs 처리
            input_vars = self._resolve_inputs(self.inputs, state)

            # 2. query 추출 (우선순위: "query" 키 → 첫 번째 input)
            query = ""
            if "query" in input_vars:
                query = input_vars["query"]
            elif input_vars:
                # query가 없으면 첫 번째 input 사용
                first_key = next(iter(input_vars))
                query = input_vars[first_key]
                logger.info(
                    f"RetrievalNode({self.output}): "
                    f"Using '{first_key}' as query (no 'query' key found)"
                )

            if not query:
                raise ValueError(
                    f"RetrievalNode({self.output}): "
                    f"Query not found. "
                    f"Available inputs: {list(self.inputs.keys())}, "
                    f"Resolved values: {input_vars}, "
                    f"State keys: {list(state.keys())}"
                )

            # 3. 벡터 검색 수행
            logger.debug(
                f"RetrievalNode({self.output}): "
                f"Searching with query='{query[:50]}...', top_k={self.top_k}"
            )

            docs = search_documents(
                query,
                k=self.top_k,
                collection_name=self.collection,
                vector_store=self.vector_store,
            )

            # 4. 검색 결과를 문자열 리스트로 변환
            retrieved_content = []
            for i, doc in enumerate(docs):
                retrieved_content.append(doc.page_content)
                logger.debug(
                    f"RetrievalNode({self.output}): "
                    f"Doc {i+1}: {doc.page_content[:100]}..."
                )

            # 5. 결과를 output에 저장
            new_state = dict(state)
            new_state[self._get_state_key()] = retrieved_content

            logger.info(
                f"RetrievalNode({self.output}): "
                f"Retrieved {len(retrieved_content)} documents"
            )

            return new_state

        except Exception as e:
            return self._handle_error(e, state)

    def similarity_search_with_score(
        self, query: str, k: int = None
    ) -> List[tuple]:
        """유사도 점수와 함께 검색"""
        k = k or self.top_k
        return search_documents_with_score(
            query,
            k=k,
            collection_name=self.collection,
            vector_store=self.vector_store,
        )
