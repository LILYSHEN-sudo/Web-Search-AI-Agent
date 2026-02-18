import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import research_agent
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Deep Research Agent API...")
    logger.info(f"Using model: {settings.zeabur_model}")
    logger.info(f"CORS origins: {settings.cors_origins}")

    if not settings.zeabur_api_token:
        logger.warning("ZEABUR_API_TOKEN is not set")
    if not settings.brightdata_api_token:
        logger.warning("BRIGHTDATA_API_TOKEN is not set")

    yield

    # Shutdown
    logger.info("Shutting down Deep Research Agent API...")


app = FastAPI(
    title="Deep Research Agent API",
    description="AI agent that answers questions using web search when needed",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    use_web_search: bool = True


class QueryResponse(BaseModel):
    answer: str
    used_search: bool = False
    search_results: list[dict] = []
    reason: str = ""


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Received query: {request.query[:100]}...")

    result = await research_agent.answer(
        question=request.query,
        use_web_search=request.use_web_search,
    )

    return QueryResponse(
        answer=result["answer"],
        used_search=result["used_search"],
        search_results=result["search_results"],
        reason=result["reason"],
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
