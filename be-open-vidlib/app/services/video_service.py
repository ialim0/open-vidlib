from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models.video import Video
from app.models.transcript import Transcript
from app.models.flashcard import Flashcard
from app.schemas.video import VideoDetailResponse, VideoListItemResponse, VideoCreate, VideoUpdate

class VideoService:
    @staticmethod
    def get_videos(
        db: Session,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Video]:
        query = db.query(Video)
        if category and category.lower() != "all":
            query = query.filter(Video.category.ilike(category))
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Video.title.ilike(search_pattern)) | 
                (Video.description.ilike(search_pattern)) |
                (Video.category.ilike(search_pattern))
            )
        return query.order_by(Video.created_at.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_video_by_id(db: Session, video_id: str) -> Optional[Video]:
        return db.query(Video).filter(Video.id == video_id).first()

    @staticmethod
    def build_video_detail_response(video: Video, target_lang: str = "en") -> VideoDetailResponse:
        # Group flashcards by language
        flashcards_by_lang: Dict[str, list] = {}
        for fc in video.flashcards:
            flashcards_by_lang.setdefault(fc.language, []).append(fc)

        # Find best transcript matching target_lang or default
        selected_transcript = None
        for tr in video.transcripts:
            if tr.language == target_lang:
                selected_transcript = tr
                break
        if not selected_transcript and video.transcripts:
            selected_transcript = video.transcripts[0]

        transcript_text = selected_transcript.full_text if selected_transcript else None
        transcript_words = selected_transcript.words if selected_transcript else None

        response = VideoDetailResponse(
            id=video.id,
            slug=video.slug,
            title=video.title,
            description=video.description,
            category=video.category,
            url=video.url,
            cover_image=video.cover_image,
            duration_seconds=video.duration_seconds,
            created_at=video.created_at,
            updated_at=video.updated_at,
            transcripts=video.transcripts,
            flashcards=video.flashcards,
            transcript=transcript_text,
            transcript_words=transcript_words,
            flashcards_by_lang=flashcards_by_lang
        )
        return response

    @staticmethod
    def create_video(db: Session, video_in: VideoCreate) -> Video:
        video = Video(
            id=video_in.id,
            slug=video_in.slug or video_in.id,
            title=video_in.title,
            description=video_in.description,
            category=video_in.category,
            url=video_in.url,
            cover_image=video_in.cover_image,
            duration_seconds=video_in.duration_seconds
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        return video

    @staticmethod
    def update_video(db: Session, video: Video, video_in: VideoUpdate) -> Video:
        update_data = video_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(video, field, value)
        db.commit()
        db.refresh(video)
        return video

    @staticmethod
    def delete_video(db: Session, video: Video) -> None:
        db.delete(video)
        db.commit()
