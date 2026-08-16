from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.video import Video
from app.schemas.video import (
    VideoListItemResponse,
    VideoDetailResponse,
    VideoCreate,
    VideoUpdate
)
from app.services.video_service import VideoService

router = APIRouter()

@router.get("", response_model=List[VideoListItemResponse], summary="List all videos")
def list_videos(
    category: Optional[str] = Query(None, description="Filter by category: Science, Technology, Engineering, Mathematics, All"),
    search: Optional[str] = Query(None, description="Search in title or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve all educational videos with optional filtering by category and search."""
    videos = VideoService.get_videos(db=db, category=category, search=search, skip=skip, limit=limit)
    return videos

@router.get("/{video_id}", response_model=VideoDetailResponse, summary="Get video details")
def get_video(
    video_id: str,
    lang: str = Query("en", description="Target transcript language"),
    db: Session = Depends(get_db)
):
    """Get full details of a specific video including transcripts and flashcards."""
    video = VideoService.get_video_by_id(db=db, video_id=video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video with id '{video_id}' not found")
    return VideoService.build_video_detail_response(video, target_lang=lang)

@router.post("", response_model=VideoListItemResponse, status_code=status.HTTP_201_CREATED, summary="Create a new video")
def create_video(
    video_in: VideoCreate,
    db: Session = Depends(get_db)
):
    """Add a new educational video to the database."""
    existing = VideoService.get_video_by_id(db=db, video_id=video_in.id)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Video with id '{video_in.id}' already exists")
    return VideoService.create_video(db=db, video_in=video_in)

@router.put("/{video_id}", response_model=VideoListItemResponse, summary="Update video")
def update_video(
    video_id: str,
    video_in: VideoUpdate,
    db: Session = Depends(get_db)
):
    """Update metadata for an existing video."""
    video = VideoService.get_video_by_id(db=db, video_id=video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video with id '{video_id}' not found")
    return VideoService.update_video(db=db, video=video, video_in=video_in)

@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete video")
def delete_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """Delete a video and all associated transcripts, flashcards, and chat logs."""
    video = VideoService.get_video_by_id(db=db, video_id=video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video with id '{video_id}' not found")
    VideoService.delete_video(db=db, video=video)
    return None
