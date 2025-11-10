from fastapi import status as http_status
from app.core.exception import (
    NotFoundError,
    ConflictError,
    InternalServerError,
    CustomException,
    ValidationError,
)
from app.database.crud.rag import collection as collection_crud
from app.schemas.rag.collection import (
    CollectionDetail,
    CollectionResponse,
    CollectionsResponse,
    CollectionCreateRequest,
    CollectionUpdateRequest,
    CollectionDeleteRequest,
    CollectionIdResponse,
)
from app.schemas.pagination import Pagination
from app.utils.common import convert_sqlalchemy_to_pydantic
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple
from pydantic import UUID4
from uuid import UUID
import re

"""
여기에 Collection 서비스 함수를 구현합니다.
서비스 레이어에는 아래와 같은 역할을 합니다.
    - 비즈니스 로직 구현
    - 데이터 유효성 검사
    - crud 상태를 보고 적절한 커스텀 에러 raise
    - 트랜잭션 관리(db commit, rollback)
    - sqlalchemy 객체를 pydantic model로 validation
    - API의 전체 로직 흐름 제어
"""


def validate_collection_name(name: str) -> None:
    """
    컬렉션 이름 검증
    - 1-255자 사이
    - 영문, 숫자, 언더스코어, 하이픈만 허용
    - 공백 불가
    """
    if not name or len(name) < 1 or len(name) > 255:
        raise ValidationError(
            message="컬렉션 이름은 1-255자 사이여야 합니다.",
            data={"name": name},
        )

    # 영문, 숫자, 언더스코어, 하이픈만 허용
    if not re.match(r"^[a-zA-Z0-9_\-]+$", name):
        raise ValidationError(
            message="컬렉션 이름은 영문, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능합니다.",
            data={"name": name},
        )


async def get_collections(
    db: AsyncSession,
    page: int = 0,
    size: int = 10,
    collection_id: Optional[UUID4] = None,
    collection_name: Optional[str] = None,
    sort: Optional[str] = "created_at:desc",
) -> Tuple[Pagination, CollectionsResponse]:
    """
    컬렉션 목록과 페이징 데이터를 조합하는 서비스 함수
    """
    try:
        # size None일 시 전체 목록 조회
        skip, limit = (0, None) if size is None else (page * size, size)

        # 컬렉션 목록과 전체 컬렉션 수 조회
        total_count, db_collections = await collection_crud.read_collections(
            db,
            skip=skip,
            limit=limit,
            collection_id=collection_id,
            collection_name=collection_name,
            sort=sort,
        )

        # Pagination 객체 생성
        pagination = Pagination.create(
            total_count=total_count or 0,
            current_page=page,
            page_size=size if size is not None else (total_count or 0),
        )

        # 컬렉션 데이터 변환
        collections = []
        for collection_tuple in db_collections:
            collection_model = collection_tuple[0]
            document_count = collection_tuple[1]

            # collection 변환 (document_count 포함)
            collection_dict = convert_sqlalchemy_to_pydantic(
                collection_model,
                CollectionDetail,
                additional_fields={"document_count": document_count},
            )
            collections.append(collection_dict)

        # 최종 응답 반환
        return pagination, CollectionsResponse(collections=collections)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def get_collection(
    db: AsyncSession,
    collection_id: UUID4,
) -> CollectionResponse:
    """
    컬렉션 데이터를 가져오는 서비스 함수
    """
    try:
        result = await collection_crud.read_collection(
            db,
            collection_id=collection_id,
            is_deleted=False,
        )
        if result is None:
            raise NotFoundError(message="컬렉션을 찾을 수 없습니다.")

        db_collection = result[0]
        document_count = result[1]

        # collection 변환 (document_count 포함)
        collection_dict = convert_sqlalchemy_to_pydantic(
            db_collection,
            CollectionDetail,
            additional_fields={"document_count": document_count},
        )

        return CollectionResponse(collection=collection_dict)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def create_collection(
    db: AsyncSession,
    collection: CollectionCreateRequest,
) -> CollectionIdResponse:
    """
    컬렉션 데이터를 생성하는 서비스 함수
    """
    try:
        # 컬렉션 이름 검증
        validate_collection_name(collection.name)

        # 컬렉션 이름 중복 체크
        existing_collection = await collection_crud.read_collection_by_name(
            db,
            name=collection.name,
            is_deleted=False,
        )
        if existing_collection:
            raise ConflictError(
                message="이미 존재하는 컬렉션 이름입니다.",
                data={"name": collection.name},
            )

        # 컬렉션 생성
        db_collection = await collection_crud.create_collection(
            db,
            collection=collection,
        )

        await db.commit()
        await db.refresh(db_collection)

        return CollectionIdResponse(id=UUID(str(db_collection.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def update_collection(
    db: AsyncSession,
    collection_id: UUID4,
    collection: CollectionUpdateRequest,
) -> CollectionIdResponse:
    """
    컬렉션 데이터를 수정하는 서비스 함수
    """
    try:
        # 컬렉션 이름 검증 (이름이 제공된 경우)
        if collection.name:
            validate_collection_name(collection.name)

            # 컬렉션 이름 중복 체크 (자기 자신 제외)
            existing_collection = (
                await collection_crud.read_collection_by_name(
                    db,
                    name=collection.name,
                    is_deleted=False,
                )
            )
            if existing_collection and str(existing_collection.id) != str(
                collection_id
            ):
                raise ConflictError(
                    message="이미 존재하는 컬렉션 이름입니다.",
                    data={"name": collection.name},
                )

        result = await collection_crud.read_collection(
            db,
            collection_id=collection_id,
            update_lock=True,
            is_deleted=False,
        )
        if result is None:
            raise NotFoundError(message="컬렉션을 찾을 수 없습니다.")

        db_collection = result[0]

        db_collection = await collection_crud.update_collection(
            db_collection=db_collection,
            collection=collection,
        )

        await db.commit()
        await db.refresh(db_collection)
        return CollectionIdResponse(id=UUID(str(db_collection.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_collection(
    db: AsyncSession,
    collection_id: UUID4,
    collection: CollectionDeleteRequest,
) -> CollectionIdResponse:
    """
    컬렉션 데이터를 삭제하는 서비스 함수
    컬렉션에 문서가 있으면 삭제 불가
    """
    try:
        result = await collection_crud.read_collection(
            db,
            collection_id=collection_id,
            update_lock=True,
            is_deleted=False,
        )
        if result is None:
            raise NotFoundError(message="컬렉션을 찾을 수 없습니다.")

        db_collection = result[0]
        document_count = result[1]

        # 컬렉션에 문서가 있으면 삭제 불가
        if document_count > 0:
            raise ConflictError(
                message="컬렉션에 문서가 존재하여 삭제할 수 없습니다. 먼저 문서를 삭제해주세요.",
                data={"document_count": document_count},
            )

        db_collection = await collection_crud.delete_collection(
            db_collection=db_collection,
            updated_by=collection.updated_by,
        )
        await db.commit()
        await db.refresh(db_collection)
        return CollectionIdResponse(id=UUID(str(db_collection.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_collection_hard(
    db: AsyncSession,
    collection_id: UUID4,
) -> CollectionIdResponse:
    """
    컬렉션 데이터를 Hard Delete하는 서비스 함수
    컬렉션에 문서가 있으면 삭제 불가
    """
    try:
        result = await collection_crud.read_collection(
            db,
            collection_id=collection_id,
            update_lock=True,
        )
        if result is None:
            raise NotFoundError(message="컬렉션을 찾을 수 없습니다.")

        db_collection = result[0]
        document_count = result[1]

        # 컬렉션에 문서가 있으면 삭제 불가
        if document_count > 0:
            raise ConflictError(
                message="컬렉션에 문서가 존재하여 삭제할 수 없습니다. 먼저 문서를 삭제해주세요.",
                data={"document_count": document_count},
            )

        collection_id_to_return = UUID(str(db_collection.id))
        await collection_crud.delete_collection_hard(
            db_collection=db_collection,
            db=db,
        )
        await db.commit()
        return CollectionIdResponse(id=collection_id_to_return)
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))
