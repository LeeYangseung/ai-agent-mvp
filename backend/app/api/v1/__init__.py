from fastapi.routing import APIRouter
from app.api.v1.graph.graph import router as graph_router
from app.api.v1.rag.chunk import router as chunk_router
from app.api.v1.rag.document import router as document_router

"""
이곳에서 v1 버전 API의 라우터를 통합합니다.
통합된 v1 라우터는 app.main 에서 어플리케이션에 추가됩니다.
"""
root_router = APIRouter()

# v1 router setup
router = APIRouter(prefix="/v1")
router.include_router(graph_router, prefix="/graph", tags=["그래프"])
router.include_router(chunk_router, prefix="/chunk", tags=["청크"])
router.include_router(document_router, prefix="/document", tags=["문서"])


@router.get("/health")
async def root_default():
    return {"message": "health check"}  # 문자열로 직접 반환
