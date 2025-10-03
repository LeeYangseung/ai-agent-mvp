from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import os


def extract_text(file_path: str) -> str:
    """
    파일에서 텍스트를 추출하는 함수
    지원 파일 형식: txt, pdf
    """
    ext = os.path.splitext(file_path)[-1].lower()

    if ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
        return "\n\n".join([doc.page_content for doc in documents])
    elif ext == ".pdf":
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        return "\n\n".join([doc.page_content for doc in documents])
    else:
        raise ValueError(
            f"Unsupported file type: {ext}. Supported types: .txt, .pdf"
        )


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
    method: str = "overlap",
):
    """
    문서를 청킹하는 함수
    method: overlap | semantic | hybrid (추후 확장)
    """
    if method == "overlap":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_text(text)
    else:
        # TODO: semantic / hybrid 방식 구현 가능
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=overlap
        )
        chunks = splitter.split_text(text)

    return chunks
