import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from typing import Any, Optional, Dict
from app.core.config import settings
import json
from enum import Enum

import urllib3

urllib3.disable_warnings()

"""
로거 정의
1. 로컬 파일, 콘솔에 로그를 전송하는 사용자 정의 로깅 핸들러를 정의합니다.
    1.2 Local File Handler
        - 로컬 파일에 로그를 저장하는 핸들러를 정의합니다.
        - TimedRotatingFileHandler를 사용해 매일 파일을 생성하고, 최대 7일의 파일을 유지합니다.
    1.3 Console Handler
        - 콘솔에 로그를 출력하는 핸들러를 정의합니다.
3. 로그 레벨은 설정 파일에서 설정합니다.
    - error: 개발/운영에서 알림을 받아 확인하고 인지하여 제거해야하는 오류
    - warn: 개발/운영에서 주기적으로 확인하고 인지하여 줄여야하는 오류
    - info: API 호출이나 주요 메서드 호출 등 로그에 기록하여 찾고 싶은 정보성 로그
    - debug: API 호출이나 메서드 호출 등 프로그램 디버깅에 필요한 로그 출력
    - trace: API 의 호출 및 성능, 외부 I/F에 관한 모든 로그 출력
4. 로그 형식은 카테고리별 json 형식으로 전송합니다.
    4.1 MANAGE 카테고리 : 사용자의 ACTION 에 따라 실행된 관리기능 및 이 동작과 관련한 API 들
        {
            "category": "MANAGE",
            "level": "{logLevel}",
            "event": "{event}",
            "timestamp": "{timestamp}",
            "thread": "{thread}",
            "context": {
                "userId": "{userId}"
            },
            "extensions": "{extensions}"
        }
    4.2 SYSTEM 카테고리 - 시스템 자체의 동작과 관련한 API 들 (ex. 스케쥴러 동작 ...)
        {
            "category": "SYSTEM",
            "level": "{logLevel}",
            "event": "{event}",
            "timestamp": "{timestamp}",
            "thread": "{thread}",
            "extensions": "{extensions}"
        }
    4.3 ERROR 카테고리 - 에러 발생 시 로그를 저장합니다.
        {
            "category": "ERROR",
            "level": "{logLevel}",
            "event": "{event}",
            "timestamp": "{timestamp}",
            "thread": "{thread}",
            "extensions": "{extensions}"
        }
    4.4 PERFORM - 성능측정을 위한 로그 (ex. 요청 처리 시간, 메모리 사용량, 디스크 사용량 등)
        {
            "category": "PERFORM",
            "level": "{logLevel}",
            "event": "{event}",
            "timestamp": "{timestamp}",
            "thread": "{thread}",
            "context": {
                "elapsedMilliseconds": "{elapsedMilliseconds}",
                "requestTimestamp": "{requestTimestamp}",
                "responseTimestamp": "{responseTimestamp}",
                "timestampDiff": "{timestampDiff}"
            },
            "extensions": "{extensions}"
        }
"""


class LogCategory(Enum):
    """로그 카테고리 정의"""

    MANAGE = "MANAGE"
    SYSTEM = "SYSTEM"
    ERROR = "ERROR"
    PERFORM = "PERFORM"


class CategoryLogRecord(logging.LogRecord):
    """카테고리 정보를 포함한 LogRecord"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category: Optional[str] = None
        self.log_data: Optional[Dict[str, Any]] = None


class StructuredJSONFormatter(logging.Formatter):
    """카테고리별 구조화된 JSON 포맷터"""

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        # 구조화된 로그 데이터가 있는 경우 그대로 사용
        if hasattr(record, "log_data") and getattr(record, "log_data", None):
            return json.dumps(getattr(record, "log_data"), ensure_ascii=False)

        # 기본 로그 메시지인 경우 SYSTEM 카테고리로 처리
        log_data = {
            "category": "SYSTEM",
            "level": record.levelname.lower(),
            "event": "system_log",
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "thread": record.threadName or str(record.thread),
            "extensions": {"detailMessage": record.getMessage()},
        }

        return json.dumps(log_data, ensure_ascii=False)


class CategoryLoggerAdapter(logging.LoggerAdapter):
    """카테고리 지원 로거 어댑터"""

    def __init__(self, logger: logging.Logger):
        super().__init__(logger, {})

    def _log_with_category(
        self,
        level: int,
        msg: str,
        args: tuple,
        category: Optional[str] = None,
        **kwargs,
    ) -> None:
        """카테고리를 포함한 로그 처리"""
        if category:
            # 로그 레벨 이름 가져오기
            level_name = logging.getLevelName(level)

            # 카테고리별 구조화된 로그 생성
            log_data = self._build_category_log(
                category, msg, level_name, **kwargs
            )

            # 특별한 LogRecord 생성
            record = CategoryLogRecord(
                name=self.logger.name,
                level=level,
                pathname="",
                lineno=0,
                msg=json.dumps(log_data, ensure_ascii=False),
                args=(),
                exc_info=None,
            )
            record.log_data = log_data

            self.logger.handle(record)
        else:
            # 일반 로그 처리
            if self.isEnabledFor(level):
                self.logger._log(level, msg, args, **kwargs)

    def _build_category_log(
        self, category: str, message: str, level: str = "info", **kwargs
    ) -> Dict[str, Any]:
        """카테고리별 로그 데이터 구조 생성"""
        import threading

        base_data = {
            "category": category.upper(),
            "level": level.lower(),
            "event": kwargs.get("event", "user_action"),
            "timestamp": datetime.now().isoformat(),
            "thread": threading.current_thread().name,
            "extensions": {"detailMessage": message},
        }

        if category.upper() == "MANAGE":
            base_data["context"] = {
                "userId": kwargs.get("user_id", ""),
            }
        elif category.upper() == "SYSTEM":
            # SYSTEM 카테고리는 context가 없고 extensions만 있음
            pass
        elif category.upper() == "ERROR":
            # ERROR 카테고리는 context가 없고 extensions만 있음
            pass
        elif category.upper() == "PERFORM":
            base_data["context"] = {
                "elapsedMilliseconds": str(kwargs.get("elapsed_ms", 0)),
                "requestTimestamp": kwargs.get(
                    "request_timestamp", datetime.now().isoformat()
                ),
                "responseTimestamp": kwargs.get(
                    "response_timestamp", datetime.now().isoformat()
                ),
                "timestampDiff": str(kwargs.get("elapsed_ms", 0)),
            }

        return base_data

    def debug(
        self, msg: str, *args, category: Optional[str] = None, **kwargs
    ) -> None:
        """DEBUG 레벨 로그"""
        self._log_with_category(logging.DEBUG, msg, args, category, **kwargs)

    def info(
        self, msg: str, *args, category: Optional[str] = None, **kwargs
    ) -> None:
        """INFO 레벨 로그"""
        self._log_with_category(logging.INFO, msg, args, category, **kwargs)

    def warning(
        self, msg: str, *args, category: Optional[str] = None, **kwargs
    ) -> None:
        """WARNING 레벨 로그"""
        self._log_with_category(logging.WARNING, msg, args, category, **kwargs)

    def error(
        self, msg: str, *args, category: Optional[str] = None, **kwargs
    ) -> None:
        """ERROR 레벨 로그"""
        if category is None:
            category = "ERROR"  # ERROR 로그는 기본적으로 ERROR 카테고리
        self._log_with_category(logging.ERROR, msg, args, category, **kwargs)

    def critical(
        self, msg: str, *args, category: Optional[str] = None, **kwargs
    ) -> None:
        """CRITICAL 레벨 로그"""
        if category is None:
            category = "ERROR"  # CRITICAL 로그도 ERROR 카테고리
        self._log_with_category(
            logging.CRITICAL, msg, args, category, **kwargs
        )


# 전역 카테고리 로거 어댑터
category_logger: Optional[CategoryLoggerAdapter] = None


def setup_logger() -> CategoryLoggerAdapter:
    print("================================================")
    print("Setup Logger")
    logger = logging.getLogger("app")

    LOG_LEVEL_MAP = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
        "trace": logging.DEBUG,
    }

    loglevel = LOG_LEVEL_MAP.get(settings.log_level.lower(), logging.INFO)
    logger.setLevel(loglevel)
    print(f"Log level: {settings.log_level.lower()}")

    # JSON 포맷터 생성
    json_formatter = StructuredJSONFormatter()

    # 콘솔 핸들러 등록
    console_handler: logging.StreamHandler = logging.StreamHandler()
    console_handler.setLevel(loglevel)
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    print("Console handler registered with JSON formatter")

    # 파일 핸들러 등록
    os.makedirs(os.path.dirname(settings.log_file_path), exist_ok=True)
    file_handler: TimedRotatingFileHandler = TimedRotatingFileHandler(
        filename=settings.log_file_path,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(loglevel)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    file_msg = (
        f"File handler registered with JSON formatter : "
        f"{settings.log_file_path}"
    )
    print(file_msg)

    # 전역 카테고리 로거 초기화
    global category_logger
    category_logger = CategoryLoggerAdapter(logger)
    print("Category logger adapter initialized")

    print("================================================")
    return category_logger  # CategoryLoggerAdapter 반환


def get_logger(name: str = "app") -> CategoryLoggerAdapter:
    """카테고리 지원 로거 반환 (기존 방식 호환)"""
    global category_logger
    if category_logger is None:
        app_logger = logging.getLogger(name)
        category_logger = CategoryLoggerAdapter(app_logger)
    return category_logger


# 편의 함수들
def log_manage(
    message: str,
    event: str = "user_action",
    user_id: Optional[str] = None,
    level: str = "info",
    **kwargs,
) -> None:
    """MANAGE 카테고리 로그 편의 함수"""
    logger = get_logger()
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(
        message, category="MANAGE", event=event, user_id=user_id, **kwargs
    )


def log_system(
    message: str,
    event: str = "system_action",
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    level: str = "info",
    **kwargs,
) -> None:
    """SYSTEM 카테고리 로그 편의 함수"""
    logger = get_logger()
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(
        message,
        category="SYSTEM",
        event=event,
        session_id=session_id,
        request_id=request_id,
        **kwargs,
    )


def log_error(
    message: str, event: str = "error_occurred", level: str = "error", **kwargs
) -> None:
    """ERROR 카테고리 로그 편의 함수"""
    logger = get_logger()
    log_method = getattr(logger, level.lower(), logger.error)
    log_method(message, category="ERROR", event=event, **kwargs)


def log_perform(
    message: str,
    event: str = "performance_measure",
    elapsed_ms: float = 0,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    level: str = "info",
    **kwargs,
) -> None:
    """PERFORM 카테고리 로그 편의 함수"""
    logger = get_logger()
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(
        message,
        category="PERFORM",
        event=event,
        elapsed_ms=elapsed_ms,
        session_id=session_id,
        request_id=request_id,
        **kwargs,
    )
