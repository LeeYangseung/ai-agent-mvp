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
def get_vector_store():
    os.makedirs(DATA_DIR, exist_ok=True)
    return Chroma(
        persist_directory=DATA_DIR,
        embedding_function=embedding_model,
    )
