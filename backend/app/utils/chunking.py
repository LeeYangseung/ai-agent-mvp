from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import (
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter,
)
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.core.exception import ValidationError
from typing import Optional
import os


def validate_chunking_params(
    method: str,
    chunk_size: Optional[int] = None,
    overlap_size: Optional[int] = None,
    breakpoint_threshold_type: Optional[str] = None,
) -> None:
    """
    청킹 방법에 따라 필요한 파라미터를 검증하는 함수

    Args:
        method: 청킹 방법 (length, semantic, hybrid, paragraph)
        chunk_size: 청크 크기
        overlap_size: 청크 중복 크기
        breakpoint_threshold_type: 시맨틱 청킹 임계값 유형

    Raises:
        ValidationError: 필수 파라미터가 누락되었거나 유효하지 않은 경우
    """
    if method == "length":
        # length 방법은 breakpoint_threshold_type 사용 불가
        if breakpoint_threshold_type is not None:
            raise ValidationError(
                message="length 청킹 방법에는 "
                "breakpoint_threshold_type을 사용할 수 없습니다.",
                data={
                    "method": method,
                    "invalid_param": "breakpoint_threshold_type",
                },
            )
        if chunk_size is None:
            raise ValidationError(
                message="length 청킹 방법에는 chunk_size가 필수입니다.",
                data={"method": method, "missing": "chunk_size"},
            )
        if overlap_size is None:
            raise ValidationError(
                message="length 청킹 방법에는 overlap_size가 필수입니다.",
                data={"method": method, "missing": "overlap_size"},
            )
        if chunk_size <= 0:
            raise ValidationError(
                message="chunk_size는 0보다 커야 합니다.",
                data={"chunk_size": chunk_size},
            )
        if overlap_size < 0:
            raise ValidationError(
                message="overlap_size는 0 이상이어야 합니다.",
                data={"overlap_size": overlap_size},
            )
        if overlap_size >= chunk_size:
            raise ValidationError(
                message="overlap_size는 chunk_size보다 작아야 합니다.",
                data={"chunk_size": chunk_size, "overlap_size": overlap_size},
            )

    elif method == "semantic":
        # semantic 방법은 chunk_size, overlap_size 사용 불가
        if chunk_size is not None:
            raise ValidationError(
                message="semantic 청킹 방법에는 chunk_size를 "
                "사용할 수 없습니다.",
                data={"method": method, "invalid_param": "chunk_size"},
            )
        if overlap_size is not None:
            raise ValidationError(
                message="semantic 청킹 방법에는 overlap_size를 "
                "사용할 수 없습니다.",
                data={"method": method, "invalid_param": "overlap_size"},
            )
        if breakpoint_threshold_type is None:
            raise ValidationError(
                message="semantic 청킹에는 "
                "breakpoint_threshold_type이 필수입니다.",
                data={
                    "method": method,
                    "missing": "breakpoint_threshold_type",
                },
            )
        valid_types = ["percentile", "standard_deviation", "interquartile"]
        if breakpoint_threshold_type not in valid_types:
            raise ValidationError(
                message="breakpoint_threshold_type은 "
                f"{valid_types} 중 하나여야 합니다.",
                data={
                    "breakpoint_threshold_type": breakpoint_threshold_type,
                    "valid_types": valid_types,
                },
            )

    elif method == "hybrid":
        if chunk_size is None:
            raise ValidationError(
                message="hybrid 청킹 방법에는 chunk_size가 필수입니다.",
                data={"method": method, "missing": "chunk_size"},
            )
        if overlap_size is None:
            raise ValidationError(
                message="hybrid 청킹 방법에는 overlap_size가 필수입니다.",
                data={"method": method, "missing": "overlap_size"},
            )
        if breakpoint_threshold_type is None:
            raise ValidationError(
                message="hybrid 청킹에는 "
                "breakpoint_threshold_type이 필수입니다.",
                data={
                    "method": method,
                    "missing": "breakpoint_threshold_type",
                },
            )
        if chunk_size <= 0:
            raise ValidationError(
                message="chunk_size는 0보다 커야 합니다.",
                data={"chunk_size": chunk_size},
            )
        if overlap_size < 0:
            raise ValidationError(
                message="overlap_size는 0 이상이어야 합니다.",
                data={"overlap_size": overlap_size},
            )
        if overlap_size >= chunk_size:
            raise ValidationError(
                message="overlap_size는 chunk_size보다 작아야 합니다.",
                data={"chunk_size": chunk_size, "overlap_size": overlap_size},
            )
        valid_types = ["percentile", "standard_deviation", "interquartile"]
        if breakpoint_threshold_type not in valid_types:
            raise ValidationError(
                message="breakpoint_threshold_type은 "
                f"{valid_types} 중 하나여야 합니다.",
                data={
                    "breakpoint_threshold_type": breakpoint_threshold_type,
                    "valid_types": valid_types,
                },
            )

    elif method == "paragraph":
        # paragraph 방법은 chunk_size, overlap_size 사용 불가
        if chunk_size is not None:
            raise ValidationError(
                message="paragraph 청킹 방법에는 chunk_size를 "
                "사용할 수 없습니다.",
                data={"method": method, "invalid_param": "chunk_size"},
            )
        if overlap_size is not None:
            raise ValidationError(
                message="paragraph 청킹 방법에는 overlap_size를 "
                "사용할 수 없습니다.",
                data={"method": method, "invalid_param": "overlap_size"},
            )
        if breakpoint_threshold_type is not None:
            raise ValidationError(
                message="paragraph 청킹 방법에는 "
                "breakpoint_threshold_type을 사용할 수 없습니다.",
                data={
                    "method": method,
                    "invalid_param": "breakpoint_threshold_type",
                },
            )

    else:
        raise ValidationError(
            message="지원하지 않는 청킹 방법입니다.",
            data={
                "method": method,
                "valid_methods": ["length", "semantic", "hybrid", "paragraph"],
            },
        )


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
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
    method: str = "length",
    breakpoint_threshold_type: Optional[str] = None,
):
    """
    문서를 청킹하는 함수
    method: length | semantic | hybrid | paragraph
    breakpoint_threshold_type: percentile | standard_deviation | interquartile

    - length: RecursiveCharacterTextSplitter를 사용한 길이 기반 청킹
    - semantic: SemanticChunker를 사용한 의미 기반 청킹 (임베딩 기반)
    - hybrid: length 청킹 후 semantic 청킹을 적용하는 하이브리드 방식
    - paragraph: 문단 단위로 청킹 (Markdown/HTML 헤더 기반)
    """
    # 파라미터 검증
    validate_chunking_params(
        method=method,
        chunk_size=chunk_size,
        overlap_size=overlap,
        breakpoint_threshold_type=breakpoint_threshold_type,
    )

    if method == "length":
        # 기본 길이 기반 청킹
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_text(text)

    elif method == "semantic":
        # 의미 기반 청킹 (임베딩 사용)
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_secret_key,
        )
        splitter = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type=breakpoint_threshold_type,
        )
        documents = splitter.create_documents([text])
        chunks = [doc.page_content for doc in documents]

    elif method == "hybrid":
        # 하이브리드 청킹: length 청킹 후 semantic 청킹
        # 1단계: length 기반으로 큰 청크 생성
        length_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        initial_chunks = length_splitter.split_text(text)

        # 2단계: 각 청크에 semantic 청킹 적용
        embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_secret_key
        )
        semantic_splitter = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type=breakpoint_threshold_type,
        )

        chunks = []
        for chunk in initial_chunks:
            documents = semantic_splitter.create_documents([chunk])
            chunks.extend([doc.page_content for doc in documents])

    elif method == "paragraph":
        # 문단 기반 청킹 (Markdown 또는 HTML)
        # 텍스트 형식 감지
        if text.strip().startswith("#") or "\n#" in text:
            # Markdown 형식
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
            splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
            documents = splitter.split_text(text)
            chunks = [doc.page_content for doc in documents]
        elif "<html" in text.lower() or "<body" in text.lower():
            # HTML 형식
            headers_to_split_on = [
                ("h1", "Header 1"),
                ("h2", "Header 2"),
                ("h3", "Header 3"),
            ]
            splitter = HTMLHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
            documents = splitter.split_text(text)
            chunks = [doc.page_content for doc in documents]
        else:
            # 일반 텍스트는 문단 구분(\n\n)으로 분리
            text_chunks = text.split("\n\n")
            chunks = [c.strip() for c in text_chunks if c.strip()]

    else:
        # 기본값: length 방식
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_text(text)

    return chunks
