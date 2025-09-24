from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.graph_runner import run_graph
from app.core.logging import get_logger
from app.core.deps import get_llm

logger = get_logger("app")

router = APIRouter()


class GraphRequest(BaseModel):
    nodes: list
    edges: list


@router.post("/run-graph")
async def run_graph_api(req: GraphRequest, llm=Depends(get_llm)):
    logger.info(f"Running graph: {req.dict()}")
    result = await run_graph(req.dict(), llm)
    return {"results": result}
