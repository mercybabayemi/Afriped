"""POST /api/v1/generate — content generation endpoint."""
from fastapi import APIRouter
from app.schemas.request import ContentGenerationRequest
from app.schemas.response import ContentGenerationResponse

router = APIRouter()

@router.post("/generate", response_model=ContentGenerationResponse)
async def generate(request: ContentGenerationRequest):
    # TODO: invoke LangGraph agent graph
    raise NotImplementedError
