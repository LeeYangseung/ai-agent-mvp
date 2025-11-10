import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings

DATA_DIR = f"{settings.vector_store_data_dir}/index"

# 임베딩 모델 (OpenAI)
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.openai_secret_key,
)


# Chroma 벡터DB 초기화
def get_vector_store(collection_name: str = "default"):
    """
    Chroma 벡터 스토어 초기화

    Args:
        collection_name: 컬렉션 이름. 기본값은 "default"

    Returns:
        Chroma 벡터 스토어 인스턴스
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    return Chroma(
        persist_directory=DATA_DIR,
        embedding_function=embedding_model,
        collection_name=collection_name,
    )


# 검색 관련 유틸리티 함수들
def search_documents(
    query: str,
    k: int = 4,
    collection_name: str = "default",
    vector_store: Chroma = None,
):
    """
    문서 검색

    Args:
        query: 검색 쿼리
        k: 반환할 문서 수
        collection_name: 검색할 컬렉션 이름
        vector_store: 기존 벡터 스토어 인스턴스 (선택사항)

    Returns:
        검색된 문서 목록
    """
    if vector_store is None:
        vector_store = get_vector_store(collection_name=collection_name)

    return vector_store.similarity_search(query, k=k)


def search_documents_with_score(
    query: str,
    k: int = 4,
    collection_name: str = "default",
    vector_store: Chroma = None,
):
    """
    유사도 점수와 함께 문서 검색

    Args:
        query: 검색 쿼리
        k: 반환할 문서 수
        collection_name: 검색할 컬렉션 이름
        vector_store: 기존 벡터 스토어 인스턴스 (선택사항)

    Returns:
        (문서, 유사도 점수) 튜플 목록
    """
    if vector_store is None:
        vector_store = get_vector_store(collection_name=collection_name)

    return vector_store.similarity_search_with_score(query, k=k)


def get_retriever(
    k: int = 4, collection_name: str = "default", vector_store: Chroma = None
):
    """
    검색기(Retriever) 반환

    Args:
        k: 반환할 문서 수
        collection_name: 검색할 컬렉션 이름
        vector_store: 기존 벡터 스토어 인스턴스 (선택사항)

    Returns:
        Retriever 인스턴스
    """
    if vector_store is None:
        vector_store = get_vector_store(collection_name=collection_name)

    return vector_store.as_retriever(search_kwargs={"k": k})
