import os
from fastapi import UploadFile
from fastapi import status as http_status
from app.core.exception import (
    NotFoundError,
    ConflictError,
    InternalServerError,
    CustomException,
)
from app.database.crud.rag import document as document_crud
from app.database.crud.rag import chunk as chunk_crud
from app.schemas.rag.document import (
    DocumentDetail,
    DocumentResponse,
    DocumentsResponse,
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentDeleteRequest,
    DocumentIdResponse,
    DocumentIdsResponse,
)
from app.schemas.rag.chunk import ChunkCreateRequest, ChunkDetail
from app.schemas.enums import DocumentStatus
from app.schemas.pagination import Pagination
from app.utils.common import convert_sqlalchemy_to_pydantic
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import UUID4
from uuid import UUID
import shutil
from app.utils.chunking import extract_text, chunk_text
from app.utils.vector_store import get_vector_store

"""
여기에 Document 서비스 함수를 구현합니다.
서비스 레이어에는 아래와 같은 역할을 합니다.
    - 비즈니스 로직 구현
    - 데이터 유효성 검사
    - crud 상태를 보고 적절한 커스텀 에러 raise
    - 트랜잭션 관리(db commit, rollback)
    - sqlalchemy 객체를 pydantic model로 validation
    - API의 전체 로직 흐름 제어
"""


async def _upload_document(
    file: UploadFile,
):
    """
    문서 파일을 업로드하는 서비스 함수
    """
    try:
        doc_dir = os.path.join(settings.vector_store_data_dir, "doc")
        os.makedirs(doc_dir, exist_ok=True)
        file_path = os.path.join(doc_dir, file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            # raise ConflictError(
            #     message="문서 파일이 이미 존재합니다.",
            #     data=file.filename,
            # )
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return file_path
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def get_documents(
    db: AsyncSession,
    page: int = 0,
    size: int = 10,
    document_id: Optional[UUID4] = None,
    chunk_id: Optional[UUID4] = None,
    document_name: Optional[str] = None,
    chunk_content: Optional[str] = None,
    path: Optional[str] = None,
    status: Optional[DocumentStatus] = None,
    sort: Optional[str] = "created_at:desc",
):
    """
    문서 목록과 페이징 데이터를 조합하는 서비스 함수
    """
    try:
        # size None일 시 전체 목록 조회
        skip, limit = (0, None) if size is None else (page * size, size)

        # 문서 목록과 전체 문서 수 조회
        total_count, db_documents = await document_crud.read_documents(
            db,
            skip=skip,
            limit=limit,
            document_id=document_id,
            chunk_id=chunk_id,
            document_name=document_name,
            chunk_content=chunk_content,
            path=path,
            status=status,
            sort=sort,
        )

        # Pagination 객체 생성 (utils의 Pagination 사용하여 0으로 나누기 문제 해결)
        pagination = Pagination.create(
            total_count=total_count or 0,
            current_page=page,
            page_size=size if size is not None else (total_count or 0),
        )

        # 문서 데이터 변환
        documents = []
        for document in db_documents:
            # chunks 변환
            chunks = [
                convert_sqlalchemy_to_pydantic(chunk, ChunkDetail)
                for chunk in getattr(document, "chunks", [])
            ]

            # document 변환 (chunks 포함)
            document_dict = convert_sqlalchemy_to_pydantic(
                document, DocumentDetail, additional_fields={"chunks": chunks}
            )
            documents.append(document_dict)

        # 최종 응답 반환
        return pagination, DocumentsResponse(documents=documents)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def get_document(
    db: AsyncSession,
    document_id: UUID4,
) -> DocumentResponse:
    """
    문서 데이터를 가져오는 서비스 함수
    """
    try:
        db_document = await document_crud.read_document(
            db,
            document_id=document_id,
            is_deleted=False,
        )
        if db_document is None:
            raise NotFoundError()

        # chunks 변환
        chunks = [
            convert_sqlalchemy_to_pydantic(chunk, ChunkDetail)
            for chunk in getattr(db_document, "chunks", [])
        ]

        # document 변환 (chunks 포함)
        document_dict = convert_sqlalchemy_to_pydantic(
            db_document, DocumentDetail, additional_fields={"chunks": chunks}
        )

        return DocumentResponse(document=document_dict)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def create_document(
    db: AsyncSession,
    document: DocumentCreateRequest,
    file: UploadFile,
) -> DocumentIdResponse:
    """
    문서 데이터를 생성하는 서비스 함수
    """
    try:
        # 문서 파일 업로드
        file_path = await _upload_document(file)
        document.path = file_path

        # 문서 생성
        db_document = await document_crud.create_document(
            db,
            document=document,
        )

        # chunking 진행
        text = extract_text(file_path)
        chunks = chunk_text(
            text, document.chunk_size, document.overlap_size, document.method
        )

        # Vector Store에 저장
        vector_store = get_vector_store()
        metadatas = [
            {"document_id": str(db_document.id), "chunk_index": idx}
            for idx, _ in enumerate(chunks)
        ]
        ids = vector_store.add_texts(texts=chunks, metadatas=metadatas)

        # chunk RDB 저장
        for chunk_index, (chunk, embedding_id) in enumerate(zip(chunks, ids)):
            chunk_create_request = ChunkCreateRequest(
                document_id=UUID(str(db_document.id)),
                chunk_index=chunk_index,
                content=chunk,
                embedding_id=embedding_id,
                chunk_size=len(chunk),
                created_by=document.created_by,
                updated_by=document.updated_by,
            )
            await chunk_crud.create_chunk(
                db,
                chunk=chunk_create_request,
            )
        await db.commit()
        await db.refresh(db_document)

        return DocumentIdResponse(id=UUID(str(db_document.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def update_document(
    db: AsyncSession,
    document_id: UUID4,
    document: DocumentUpdateRequest,
) -> DocumentIdResponse:
    """
    문서 데이터를 수정하는 서비스 함수
    """
    try:
        db_document = await document_crud.read_document(
            db,
            document_id=document_id,
            update_lock=True,
        )
        if db_document is None:
            raise NotFoundError()

        # chunks 정보를 별도로 저장
        chunks_data = document.chunks
        # chunks를 제외한 document 객체 생성
        document_dict = document.model_dump(exclude={"chunks"})
        document_without_chunks = DocumentUpdateRequest(**document_dict)

        db_document = await document_crud.update_document(
            db_document=db_document,
            document=document_without_chunks,
        )

        # chunks가 있으면 기존 chunk들 삭제 후 새로운 chunk들 생성
        if chunks_data:
            # 기존 chunk들 조회 및 삭제
            existing_chunks = await chunk_crud.read_chunks(
                db,
                document_id=document_id,
                limit=None,  # 모든 chunks 조회
            )
            if existing_chunks[1]:  # chunks가 있으면
                for chunk in existing_chunks[1]:
                    await chunk_crud.delete_chunk(
                        db_chunk=chunk,
                    )

            # 새로운 chunk들 생성
            for chunk_data in chunks_data:
                chunk_create_request = ChunkCreateRequest(
                    document_id=UUID(str(db_document.id)),
                    chunk_index=chunk_data.chunk_index,
                    content=chunk_data.content,
                    embedding_id=chunk_data.embedding_id,
                    chunk_size=chunk_data.chunk_size,
                    created_by=document.updated_by,
                    updated_by=document.updated_by,
                )
                _ = await chunk_crud.create_chunk(
                    db,
                    chunk=chunk_create_request,
                )
        await db.commit()
        await db.refresh(db_document)
        return DocumentIdResponse(id=UUID(str(db_document.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_document(
    db: AsyncSession,
    document_id: UUID4,
    document: DocumentDeleteRequest,
) -> DocumentIdResponse:
    """
    문서 데이터를 삭제하는 서비스 함수
    """
    try:
        db_document = await document_crud.read_document(
            db,
            document_id=document_id,
            update_lock=True,
        )
        # Chunks 삭제
        existing_chunks = await chunk_crud.read_chunks(
            db,
            document_id=document_id,
            limit=None,  # 모든 chunks 조회
        )
        if existing_chunks[1]:  # chunks가 있으면
            for chunk in existing_chunks[1]:
                await chunk_crud.delete_chunk(
                    db_chunk=chunk,
                )
        db_document = await document_crud.delete_document(
            db_document=db_document,
            updated_by=document.updated_by,
        )
        if not db_document:
            raise NotFoundError()
        await db.commit()
        await db.refresh(db_document)
        return DocumentIdResponse(id=UUID(str(db_document.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_document_hard(
    db: AsyncSession,
    document_id: UUID4,
    document: DocumentDeleteRequest,
) -> DocumentIdResponse:
    """
    문서 데이터를 삭제하는 서비스 함수
    """
    try:
        db_document = await document_crud.read_document(
            db,
            document_id=document_id,
        )
        # Chunks 삭제
        if db_document.chunks:
            existing_chunks = await chunk_crud.read_chunks(
                db,
                document_id=document_id,
                limit=None,  # 모든 chunks 조회
            )
            if existing_chunks[1]:  # chunks가 있으면
                for chunk in existing_chunks[1]:
                    _ = await chunk_crud.delete_chunk_hard(
                        db_chunk=chunk,
                        db=db,
                    )
        db_document = await document_crud.delete_document_hard(
            db_document=db_document,
            db=db,
        )
        if not db_document:
            raise NotFoundError()
        await db.commit()
        await db.refresh(db_document)
        return DocumentIdResponse(id=UUID(str(db_document.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))
