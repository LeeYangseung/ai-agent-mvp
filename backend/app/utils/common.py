from typing import List, Type, TypeVar, Any, Dict, Union
from app.core.exception import BadRequestError

T = TypeVar("T")  # Model 타입을 일반화하기 위해 Generic 사용


def get_column_attr(model: Type[T], field: str) -> Any:
    """
    주어진 모델에서 dot(.) 구분자로 표현된 필드
    (예: "role_system_auth.system_auth.system_auth_name")
    를 따라가 최종 컬럼을 반환합니다.
    만약 첫 번째 토큰이 모델명(소문자)와 같다면 이를 생략합니다.
    """
    parts = field.split(".")
    model_name = model.__name__.lower()
    if parts[0] == model_name:
        parts.pop(0)

    current_model = model
    # 마지막 필드 전까지 관계를 따라감
    for relation_name in parts[:-1]:
        if not hasattr(current_model, relation_name):
            raise BadRequestError(
                data=f"Invalid nested field '{relation_name}' "
                f"in filter/search condition '{field}'."
            )
        relation = getattr(current_model, relation_name)
        try:
            current_model = relation.property.mapper.class_
        except AttributeError:
            raise BadRequestError(
                data=f"Attribute '{relation_name}' in '{field}' "
                f"is not a valid relationship."
            )
    # 마지막 부분은 컬럼명이어야 함
    last_field = parts[-1]
    if not hasattr(current_model, last_field):
        raise BadRequestError(
            data=f"Invalid field '{last_field}' in nested condition '{field}'."
        )
    return getattr(current_model, last_field)


def parse_sort_conditions(sort: str, model: Type[T]) -> List[Any]:
    """
    "컬럼명:정렬순서,컬럼명:정렬순서" 형태의 문자열을 파싱하여 정렬 조건을 반환합니다.
    예: "created_at:asc,user_name:desc"
    """
    columns = []
    if not sort:
        return columns

    for sort_item in sort.split(","):
        sort_item = sort_item.strip()
        if not sort_item:
            continue

        # "컬럼명:정렬순서" 형태로 분리
        if ":" not in sort_item:
            raise BadRequestError(
                data=f"Invalid sort format '{sort_item}'. "
                f"Expected format: 'column:order' (e.g., 'created_at:asc')"
            )

        column_name, order = sort_item.split(":", 1)
        column_name = column_name.strip()
        order = order.strip().lower()

        # 컬럼 속성 가져오기
        column_attr = get_column_attr(model, column_name)

        # 정렬 순서 적용
        if order == "asc":
            columns.append(column_attr.asc())
        elif order == "desc":
            columns.append(column_attr.desc())
        else:
            raise BadRequestError(
                data=f"Invalid sort order '{order}' in '{sort_item}'. "
                f"Only 'asc' or 'desc' are allowed."
            )
    return columns


def sqlalchemy_to_dict(
    obj: Any,
    field_mapping: Dict[str, str] = None,
    additional_fields: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    SQLAlchemy 객체를 딕셔너리로 변환하는 공통 함수

    Args:
        obj: SQLAlchemy 모델 객체
        field_mapping: 필드명 매핑 (obj_field: dict_key)
        additional_fields: 추가로 포함할 필드들

    Returns:
        딕셔너리 형태의 데이터
    """
    if obj is None:
        return {}

    result = {}

    # 기본 필드들 (객체의 직접 속성들)
    for attr_name in dir(obj):
        if attr_name.startswith("_"):
            continue

        try:
            # 속성 접근 가능 여부를 먼저 체크
            if not hasattr(obj, attr_name):
                continue

            value = getattr(obj, attr_name)

            # callable 체크 (함수/메서드 제외)
            if callable(value):
                continue

            # SQLAlchemy 컬럼이나 일반 속성인 경우
            # relationship 필드는 제외 (hasattr(value, "property")로 체크)
            if not hasattr(value, "__table__") and not hasattr(
                value, "property"
            ):
                result[attr_name] = value
        except Exception:
            # 접근할 수 없는 속성은 무시
            continue

    # 필드 매핑 적용
    if field_mapping:
        for obj_field, dict_key in field_mapping.items():
            if hasattr(obj, obj_field):
                result[dict_key] = getattr(obj, obj_field)

    # 추가 필드들
    if additional_fields:
        result.update(additional_fields)

    return result


def convert_sqlalchemy_to_pydantic(
    sqlalchemy_obj: Any,
    pydantic_model: Type[T],
    field_mapping: Dict[str, str] = None,
    additional_fields: Dict[str, Any] = None,
) -> T:
    """
    SQLAlchemy 객체를 Pydantic 모델로 변환하는 공통 함수

    Args:
        sqlalchemy_obj: SQLAlchemy 모델 객체
        pydantic_model: 변환할 Pydantic 모델 클래스
        field_mapping: 필드명 매핑
        additional_fields: 추가 필드들

    Returns:
        Pydantic 모델 인스턴스
    """
    obj_dict = sqlalchemy_to_dict(
        sqlalchemy_obj, field_mapping, additional_fields
    )
    return pydantic_model.model_validate(obj_dict)
