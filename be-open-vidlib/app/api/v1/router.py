from fastapi import APIRouter
from app.api.v1.endpoints import videos, transcripts, flashcards, chat, health, mistral_endpoints

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])
api_router.include_router(mistral_endpoints.router, prefix="/videos", tags=["Mistral AI & PGVector"])
api_router.include_router(transcripts.router, prefix="/transcripts", tags=["Transcripts"])
api_router.include_router(flashcards.router, prefix="/flashcards", tags=["Flashcards"])
api_router.include_router(chat.router, prefix="/chat", tags=["Video Chat"])
