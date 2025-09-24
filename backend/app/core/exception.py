from http import HTTPStatus
from typing import Any, Optional

from app.schemas.base import ResponseModel


class CustomException(Exception):
    """
    커스텀 예외 기본 클래스입니다.
    ResponseModel 형식으로 에러 응답을 반환합니다.
    임의의 에러를 발생시킬 때 이 클래스를 상속한 다른 예외 클래스를 만들거나,
    이 클래스에 원하는 `status_code`와 `detail`을 입력하여 직접 raise 시킵니다.
    `detail`은 jsonable 한 데이터라면, 사용자에게 그 어떠한 내용이라도 전달할 수 있습니다.
    """

    status: int
    message: str
    data: Optional[Any]

    def __init__(
        self,
        *args,
        status: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        message: str = "서버에서 처리 중 오류가 발생했습니다.",
        data: Optional[Any] = None,
        **kwargs,
    ):
        self.status = status
        self.message = message
        self.data = data if data else args

        self.response = ResponseModel(
            status=self.status,
            message=self.message,
            data=self.data,
        )
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: \
            {str(self.data) if self.data else ''}"


# 400
class BadRequestError(CustomException):
    """잘못된 요청을 처리하는 예외"""

    def __init__(
        self,
        message: str = "잘못된 요청입니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.BAD_REQUEST,
            message=message,
            data=data,
        )


class UnauthorizedError(CustomException):
    """인증 되지 않은 요청을 처리하는 예외"""

    def __init__(
        self,
        message: str = "인증 되지 않은 요청입니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.UNAUTHORIZED,
            message=message,
            data=data,
        )


class ForbiddenError(CustomException):
    """접근 권한이 없는 요청을 처리하는 예외"""

    def __init__(
        self,
        message: str = "접근 권한이 없습니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.FORBIDDEN,
            message=message,
            data=data,
        )


class NotFoundError(CustomException):
    """리소스를 찾을 수 없을 때 발생하는 예외"""

    def __init__(
        self,
        message: str = "요청하신 리소스를 찾을 수 없습니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.NOT_FOUND,
            message=message,
            data=data,
        )


class ConflictError(CustomException):
    def __init__(
        self,
        message: str = "리소스가 이미 존재합니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.CONFLICT,
            message=message,
            data=data,
        )


class ValidationError(CustomException):
    """입력값이 올바르지 않을 때 발생하는 예외"""

    def __init__(
        self,
        message: str = "입력값이 올바르지 않습니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
            message=message,
            data=data,
        )


class TooManyRequestsError(CustomException):
    """요청이 너무 많을 때 발생하는 예외"""

    def __init__(
        self,
        message: str = "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.TOO_MANY_REQUESTS,
            message=message,
            data=data,
        )


# 500
class InternalServerError(CustomException):
    """서버에서 처리 중 알 수 없는 오류가 발생했을 때 발생하는 예외"""

    def __init__(
        self,
        message: str = "서버에서 처리 중 알 수 없는 오류가 발생했습니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=500,
            message=message,
            data=str(data) if isinstance(data, BaseException) else data,
        )


class BadGatewayError(CustomException):
    """게이트웨이로부터 잘못된 응답을 수신했을 때 발생하는 예외"""

    def __init__(
        self,
        message: str = "게이트웨이로부터 잘못된 응답을 수신했습니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.BAD_GATEWAY,
            message=message,
            data=data,
        )


class ServiceUnavailableError(CustomException):
    """서비스를 일시적으로 이용할 수 없을 때 발생하는 예외"""

    def __init__(
        self,
        message: str = "서비스를 일시적으로 이용할 수 없습니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            message=message,
            data=data,
        )


class GatewayTimeoutError(CustomException):
    """게이트웨이 서버가 백엔드 서버로부터 응답을 받지 못했을 때 발생하는 예외"""

    def __init__(
        self,
        message: str = "게이트웨이 서버가 백엔드 서버로부터 응답을 받지 못했습니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=HTTPStatus.GATEWAY_TIMEOUT,
            message=message,
            data=data,
        )


class DatabaseError(CustomException):
    """데이터베이스 오류가 발생했을 때 발생하는 예외"""

    def __init__(
        self,
        message: str = "데이터베이스 오류가 발생했습니다.",
        data: Optional[Any] = None,
    ):
        super().__init__(
            status=520,
            message=message,
            data=data,
        )


class ExternalApiError(CustomException):
    """외부 서비스 연동 중 오류가 발생했을 때 발생하는 예외"""

    def __init__(
        self,
        message: str = "서비스 연동 중 오류가 발생했습니다. 관리자에게 문의하세요.",
        data: Optional[Any] = None,
        *,
        status: int = 521,
    ):
        super().__init__(
            status=status,
            message=message,
            data=data,
        )


# Custom Error
class ModelAPIError(ExternalApiError):
    """Model API 연동 중 오류가 발생했을 때 발생하는 예외"""

    def __init__(self, data: Optional[Any] = None):
        super().__init__(
            message="Model API 연동 중 오류가 발생했습니다. 관리자에게 문의하세요.",
            data=data,
        )
