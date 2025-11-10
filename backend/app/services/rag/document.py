import os
from fastapi import UploadFile
from fastapi import status as http_status
from app.core.exception import (
    NotFoundError,
    ConflictError,
    InternalServerError,
    CustomException,
)
from app.schemas.rag.collection import CollectionDetail
from app.database.crud.rag import document as document_crud
from app.database.crud.rag import chunk as chunk_crud
from app.database.crud.rag import collection as collection_crud
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
from typing import Optional, Tuple
from pydantic import UUID4
from uuid import UUID
import shutil
from app.utils.chunking import (
    extract_text,
    chunk_text,
    validate_chunking_params,
)
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
    collection_id: Optional[UUID4] = None,
    collection_name: Optional[str] = None,
    chunk_id: Optional[UUID4] = None,
    document_name: Optional[str] = None,
    chunk_content: Optional[str] = None,
    path: Optional[str] = None,
    status: Optional[DocumentStatus] = None,
    sort: Optional[str] = "created_at:desc",
) -> Tuple[Pagination, DocumentsResponse]:
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
            collection_id=collection_id,
            collection_name=collection_name,
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
            # collection 변환
            collection = convert_sqlalchemy_to_pydantic(
                getattr(document, "collection", None), CollectionDetail
            )

            # document 변환 (chunks 포함)
            document_dict = convert_sqlalchemy_to_pydantic(
                document,
                DocumentDetail,
                additional_fields={"chunks": chunks, "collection": collection},
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
        # collection 변환
        collection = convert_sqlalchemy_to_pydantic(
            getattr(db_document, "collection", None), CollectionDetail
        )

        # document 변환 (chunks 포함)
        document_dict = convert_sqlalchemy_to_pydantic(
            db_document,
            DocumentDetail,
            additional_fields={"chunks": chunks, "collection": collection},
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
        # 컬렉션 존재 여부 확인
        collection_result = await collection_crud.read_collection(
            db,
            collection_id=document.collection_id,
            is_deleted=False,
        )
        if collection_result is None:
            raise NotFoundError(
                message="컬렉션을 찾을 수 없습니다.",
                data={"collection_id": str(document.collection_id)},
            )

        # 청킹 파라미터 검증
        validate_chunking_params(
            method=document.method,
            chunk_size=document.chunk_size,
            overlap_size=document.overlap_size,
            breakpoint_threshold_type=document.breakpoint_threshold_type,
        )

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
            text,
            document.chunk_size,
            document.overlap_size,
            document.method,
            document.breakpoint_threshold_type,
        )

        # Vector Store에 저장 (collection 이름 사용)
        collection_model = collection_result[0]
        vector_store = get_vector_store(collection_name=collection_model.name)
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

        # 문서 상태 업데이트
        update_document = DocumentUpdateRequest(
            status=DocumentStatus.indexed,
        )
        await document_crud.update_document(
            db_document=db_document,
            document=update_document,
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
            is_deleted=False,
        )
        if db_document is None:
            raise NotFoundError()

        db_document = await document_crud.update_document(
            db_document=db_document,
            document=document,
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
    Vector Store에서도 해당 문서의 chunks 삭제
    """
    try:
        db_document = await document_crud.read_document(
            db,
            document_id=document_id,
            update_lock=True,
            is_deleted=False,
        )
        if db_document is None:
            raise NotFoundError()

        # 컬렉션 정보 조회
        collection_result = await collection_crud.read_collection(
            db,
            collection_id=UUID(str(db_document.collection_id)),
            is_deleted=False,
        )
        if collection_result:
            collection_model = collection_result[0]
            vector_store = get_vector_store(
                collection_name=collection_model.name
            )

            # Chunks 조회 및 삭제
            existing_chunks = await chunk_crud.read_chunks(
                db,
                document_id=document_id,
                limit=None,  # 모든 chunks 조회
            )
            if existing_chunks[1]:  # chunks가 있으면
                # Vector Store에서 삭제
                embedding_ids = [
                    chunk.embedding_id for chunk in existing_chunks[1]
                ]
                if embedding_ids:
                    vector_store.delete(ids=embedding_ids)

                # RDB에서 삭제
                for chunk in existing_chunks[1]:
                    await chunk_crud.delete_chunk(
                        db_chunk=chunk,
                    )

        db_document = await document_crud.delete_document(
            db_document=db_document,
            updated_by=document.updated_by,
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


async def delete_document_hard(
    db: AsyncSession,
    document_id: UUID4,
) -> DocumentIdResponse:
    """
    문서 데이터를 Hard Delete하는 서비스 함수
    Vector Store에서도 해당 문서의 chunks 삭제
    """
    try:
        db_document = await document_crud.read_document(
            db,
            document_id=document_id,
            update_lock=True,
        )
        if db_document is None:
            raise NotFoundError()

        # 컬렉션 정보 조회
        collection_result = await collection_crud.read_collection(
            db,
            collection_id=UUID(str(db_document.collection_id)),
        )
        if collection_result:
            collection_model = collection_result[0]
            vector_store = get_vector_store(
                collection_name=collection_model.name
            )

            # Chunks 조회 및 삭제
            existing_chunks = await chunk_crud.read_chunks(
                db,
                document_id=document_id,
                limit=None,  # 모든 chunks 조회
            )
            if existing_chunks[1]:  # chunks가 있으면
                # Vector Store에서 삭제
                embedding_ids = [
                    chunk.embedding_id for chunk in existing_chunks[1]
                ]
                if embedding_ids:
                    vector_store.delete(ids=embedding_ids)

                # RDB에서 Hard Delete
                for chunk in existing_chunks[1]:
                    _ = await chunk_crud.delete_chunk_hard(
                        db_chunk=chunk,
                        db=db,
                    )

        document_id_to_return = UUID(str(db_document.id))
        await document_crud.delete_document_hard(
            db_document=db_document,
            db=db,
        )
        await db.commit()
        return DocumentIdResponse(id=document_id_to_return)
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))
