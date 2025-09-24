from pydantic import BaseModel


# 페이지네이션
class Pagination(BaseModel):
    total_count: int = 0
    total_pages: int = 0
    current_page: int = 0
    page_size: int = 0

    @classmethod
    def create(
        cls, total_count: int = 0, current_page: int = 0, page_size: int = 0
    ):
        # page_size가 0이거나 음수인 경우 안전하게 처리
        if page_size <= 0:
            total_pages = 1 if total_count > 0 else 0
        else:
            total_pages = (
                (total_count + page_size - 1) // page_size
                if total_count > 0
                else 0
            )

        return cls(
            total_count=total_count,
            total_pages=total_pages,
            current_page=current_page,
            page_size=page_size,
        )
