import { getVideos, getVideoById, VideoDetail, VideoItem, TranscriptWord, Flashcard } from './api/videos'

export type ResourceType = "video"

export interface Resource {
    id: string
    title: string
    type: ResourceType
    url: string
    category?: string
    coverImage?: string
    description?: string
    duration_seconds?: number
    transcript?: string
    transcriptWords?: TranscriptWord[]
    flashcards?: Flashcard[]
    flashcardsByLang?: Record<string, Flashcard[]>
}

export type { TranscriptWord, Flashcard }

export async function getResources(): Promise<Resource[]> {
    const videos = await getVideos()
    return videos.map(v => ({
        id: v.id,
        title: v.title,
        type: 'video' as ResourceType,
        url: v.url,
        category: v.category,
        coverImage: v.cover_image || v.coverImage,
        description: v.description,
        duration_seconds: v.duration_seconds
    }))
}

export async function getResourceById(id: string, lang: string = "en"): Promise<Resource | undefined> {
    const video = await getVideoById(id, lang)
    if (!video) return undefined

    return {
        id: video.id,
        title: video.title,
        type: 'video' as ResourceType,
        url: video.url,
        category: video.category,
        coverImage: video.cover_image || video.coverImage,
        description: video.description,
        duration_seconds: video.duration_seconds,
        transcript: video.transcript,
        transcriptWords: video.transcript_words || video.transcriptWords,
        flashcards: video.flashcards,
        flashcardsByLang: video.flashcards_by_lang || video.flashcardsByLang
    }
}
