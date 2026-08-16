export interface TranscriptWord {
    word: string
    start: number
    end: number
}

export interface Flashcard {
    question: string
    options: string[]
    correctOption: number
    source: string
}

export interface VideoItem {
    id: string
    slug?: string
    title: string
    description?: string
    category: string
    url: string
    cover_image?: string
    coverImage?: string
    duration_seconds?: number
    created_at?: string
    updated_at?: string
}

export interface VideoDetail extends VideoItem {
    transcript?: string
    transcript_words?: TranscriptWord[]
    transcriptWords?: TranscriptWord[]
    flashcards?: Flashcard[]
    flashcards_by_lang?: Record<string, Flashcard[]>
    flashcardsByLang?: Record<string, Flashcard[]>
}

export interface SearchResultItem {
    text: string
    start_time: number
    end_time: number
    similarity: number
}

export interface DubbedSegmentItem {
    segment_id?: number
    audio_url: string
    start: number
    end: number
    translated_text?: string
}

export interface DubbedTrack {
    video_id: string
    language: string
    voice: string
    status: string
    segments: DubbedSegmentItem[]
}

export interface AgentResponse {
    type: "search" | "qa" | "dubbing" | "chat"
    content?: string
    question?: string
    answer?: string
    sources?: SearchResultItem[]
    results?: SearchResultItem[]
    status?: string
    language?: string
    voice_gender?: string
    dub_track?: DubbedTrack
    session_id?: string
    timestamp?: string
}

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const FALLBACK_VIDEOS: VideoDetail[] = [
    {
        id: "video-0",
        slug: "science-gravity-explained",
        title: "La Gravité Expliquée aux Enfants",
        category: "Science",
        url: "https://youtu.be/suQDwZcnJdg?si=Sci2Buj-E5ZDn94G",
        cover_image: "/science/img-1.png",
        coverImage: "/science/img-1.png",
        description: "Une leçon interactive et passionnante pour comprendre la gravité terrestre, la chute des corps et les lois de Newton.",
        duration_seconds: 240
    },
    {
        id: "video-2",
        slug: "engineering-pyramid-of-cheops",
        title: "Les chiffres affolants de la pyramide de Khéops",
        category: "Engineering",
        url: "https://youtu.be/ITYFvAP98qs?si=SumofslEc4X48MSx",
        cover_image: "/engineering/img-1.png",
        coverImage: "/engineering/img-1.png",
        description: "Explorez les prouesses architecturales, les dimensions colossales et les secrets d'ingénierie de la grande pyramide.",
        duration_seconds: 420
    },
    {
        id: "video-3",
        slug: "mathematics-pythagorean-theorem",
        title: "À quoi sert le théorème de Pythagore ?",
        category: "Mathematics",
        url: "https://youtu.be/eYQPZgMTzkY?si=5UWldu8ZcR4Kg5R9",
        cover_image: "/mathematics/img-1.png",
        coverImage: "/mathematics/img-1.png",
        description: "Comprenez l'utilité pratique du théorème de Pythagore dans la construction, la navigation et la vie quotidienne.",
        duration_seconds: 280
    }
]

export async function getVideos(params?: { category?: string; search?: string }): Promise<VideoItem[]> {
    try {
        const query = new URLSearchParams()
        if (params?.category && params.category !== "All") {
            query.append("category", params.category)
        }
        if (params?.search) {
            query.append("search", params.search)
        }

        const url = `${API_BASE_URL}/videos${query.toString() ? `?${query.toString()}` : ''}`
        const res = await fetch(url, {
            cache: 'no-store',
            headers: { 'Accept': 'application/json' }
        })

        if (!res.ok) throw new Error(`Failed to fetch videos: ${res.statusText}`)

        const data: VideoItem[] = await res.json()
        return data.map(v => ({
            ...v,
            coverImage: v.cover_image || v.coverImage
        }))
    } catch (e) {
        console.warn("Backend API unavailable, using fallback seed videos:", e)
        let filtered = FALLBACK_VIDEOS
        if (params?.category && params.category !== "All") {
            filtered = filtered.filter(v => v.category.toLowerCase() === params.category!.toLowerCase())
        }
        if (params?.search) {
            const s = params.search.toLowerCase()
            filtered = filtered.filter(v => 
                v.title.toLowerCase().includes(s) || 
                (v.description && v.description.toLowerCase().includes(s))
            )
        }
        return filtered
    }
}

export async function getVideoById(videoId: string, lang: string = "en"): Promise<VideoDetail | null> {
    try {
        const res = await fetch(`${API_BASE_URL}/videos/${videoId}?lang=${lang}`, {
            cache: 'no-store',
            headers: { 'Accept': 'application/json' }
        })

        if (!res.ok) throw new Error(`Failed to fetch video ${videoId}: ${res.statusText}`)

        const data = await res.json()
        return {
            ...data,
            coverImage: data.cover_image || data.coverImage,
            transcriptWords: data.transcript_words || data.transcriptWords,
            flashcardsByLang: data.flashcards_by_lang || data.flashcardsByLang
        }
    } catch (e) {
        console.warn(`Backend API unavailable for video ${videoId}, checking fallback:`, e)
        return FALLBACK_VIDEOS.find(v => v.id === videoId) || null
    }
}

// Mistral Semantic Search
export async function searchVideoSemantically(videoId: string, query: string, topK: number = 5): Promise<SearchResultItem[]> {
    try {
        const res = await fetch(`${API_BASE_URL}/videos/${videoId}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, top_k: topK })
        })
        if (!res.ok) throw new Error(`Semantic search error: ${res.statusText}`)
        const data = await res.json()
        return data.results || []
    } catch (e) {
        console.warn("Semantic search failed:", e)
        return []
    }
}

// Mistral RAG Q&A
export async function askVideoQuestionRAG(videoId: string, question: string, sessionId: string = "default-session"): Promise<{ answer: string; sources: SearchResultItem[] }> {
    try {
        const res = await fetch(`${API_BASE_URL}/videos/${videoId}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, session_id: sessionId })
        })
        if (!res.ok) throw new Error(`RAG QA error: ${res.statusText}`)
        return await res.json()
    } catch (e) {
        console.warn("RAG QA failed:", e)
        return {
            answer: "Coumba: I am currently unable to reach the AI backend. Please verify your backend server is active.",
            sources: []
        }
    }
}

// Mistral Voxtral Dubbing
export async function requestDubbedTrack(videoId: string, language: string, voiceGender: string = "female"): Promise<DubbedTrack | null> {
    try {
        const res = await fetch(`${API_BASE_URL}/videos/${videoId}/dub`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language, voice_gender: voiceGender })
        })
        if (!res.ok) throw new Error("Dubbing request failed")
        return await res.json()
    } catch (e) {
        console.warn("Dubbing request failed:", e)
        throw e
    }
}

export async function getDubbedAudioTrack(videoId: string, language: string): Promise<DubbedTrack | null> {
    try {
        const res = await fetch(`${API_BASE_URL}/videos/${videoId}/dub/${language}`, {
            cache: 'no-store'
        })
        if (!res.ok) return null
        return await res.json()
    } catch (e) {
        return null
    }
}

// Multistep Agent Router
export async function sendAgentMessage(videoId: string, message: string, sessionId: string = "default-session"): Promise<AgentResponse> {
    try {
        const res = await fetch(`${API_BASE_URL}/videos/${videoId}/agent-chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId })
        })
        if (!res.ok) throw new Error(`Agent chat error: ${res.statusText}`)
        return await res.json()
    } catch (e) {
        console.warn("Agent chat error, falling back to simulated response:", e)
        return {
            type: "chat",
            content: "Coumba: I'm here to help you study this video! You can ask questions, search moments, or take a quiz.",
            session_id: sessionId
        }
    }
}

export async function generateQuizFromAI(
    videoId: string,
    language: string = "en",
    count: number = 5
): Promise<Flashcard[]> {
    try {
        const res = await fetch(`${API_BASE_URL}/flashcards/video/${videoId}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language, count })
        })

        if (!res.ok) throw new Error(`Quiz generate error: ${res.statusText}`)

        const data = await res.json()
        return data.map((fc: any) => ({
            question: fc.question,
            options: fc.options,
            correctOption: fc.correct_option ?? fc.correctOption,
            source: fc.source
        }))
    } catch (e) {
        console.warn("Generate quiz API error:", e)
        return []
    }
}
