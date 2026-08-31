"use client"

import { useState, useEffect, useRef, useMemo, forwardRef, useImperativeHandle } from "react"
import { getYouTubeEmbedUrl } from "@/lib/utils"
import { Play, Pause, Clock, Search, Sparkles, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { API_BASE_URL, searchVideoSemantically, SearchResultItem, DubbedTrack } from "@/lib/api/videos"

interface TranscriptWord {
    word: string
    start: number
    end: number
}

interface VideoPlayerWithTranscriptProps {
    videoId?: string
    videoUrl: string
    transcriptWords?: TranscriptWord[]
    liveCaptionsLabel?: string
    activeDubTrack?: DubbedTrack | null
    isDubbingLoading?: boolean
}

export const VideoPlayerWithTranscript = forwardRef<{ seekTo: (time: number) => void }, VideoPlayerWithTranscriptProps>(
    function VideoPlayerWithTranscript({
        videoId,
        videoUrl,
        transcriptWords,
        liveCaptionsLabel = "Live Captions",
        activeDubTrack,
        isDubbingLoading = false
    }, ref) {
        const [currentTime, setCurrentTime] = useState(0)
        const [maxRevealedTime, setMaxRevealedTime] = useState(0)
        const [isPlaying, setIsPlaying] = useState(false)
        const [player, setPlayer] = useState<any>(null)
        const [hoveredWordIndex, setHoveredWordIndex] = useState<number | null>(null)
        const [searchQuery, setSearchQuery] = useState("")
        const [searchResults, setSearchResults] = useState<SearchResultItem[]>([])
        const [isSearching, setIsSearching] = useState(false)
        const [activeTab, setActiveTab] = useState<"captions" | "search">("captions")

        const animationFrameRef = useRef<number | null>(null)
        const playerRef = useRef<any>(null)
        const audioRef = useRef<HTMLAudioElement | null>(null)
        const dubbedSegmentRef = useRef<number | null>(null)

        const getVideoId = (url: string) => {
            const match = url.match(/(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/watch\?.+&v=))([^&?\/]+)/)
            return match ? match[1] : null
        }

        const ytId = getVideoId(videoUrl)

        useEffect(() => {
            if (!ytId) return

            const initializePlayer = () => {
                try {
                    const newPlayer = new (window as any).YT.Player('youtube-player', {
                        videoId: ytId,
                        events: {
                            onReady: (event: any) => {
                                setPlayer(event.target)
                                playerRef.current = event.target
                            },
                            onStateChange: (event: any) => {
                                const isNowPlaying = event.data === (window as any).YT.PlayerState.PLAYING
                                setIsPlaying(isNowPlaying)
                            }
                        }
                    })
                } catch (error) {
                    console.error('Error initializing player:', error)
                }
            }

            if ((window as any).YT && (window as any).YT.Player) {
                initializePlayer()
            } else {
                if (!document.querySelector('script[src*="youtube.com/iframe_api"]')) {
                    const tag = document.createElement('script')
                    tag.src = 'https://www.youtube.com/iframe_api'
                    const firstScriptTag = document.getElementsByTagName('script')[0]
                    firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag)
                }

                (window as any).onYouTubeIframeAPIReady = () => {
                    initializePlayer()
                }
            }

            return () => {
                if (animationFrameRef.current) {
                    cancelAnimationFrame(animationFrameRef.current)
                }
                if (playerRef.current && playerRef.current.destroy) {
                    playerRef.current.destroy()
                }
            }
        }, [ytId])

        useImperativeHandle(ref, () => ({
            seekTo: (time: number) => {
                if (player && player.seekTo) {
                    player.seekTo(time, true)
                    player.playVideo()
                    setIsPlaying(true)
                    setCurrentTime(time)
                }
            }
        }), [player])

        useEffect(() => {
            const updateTime = () => {
                if (player && player.getCurrentTime) {
                    const time = player.getCurrentTime()
                    setCurrentTime(time)
                    setMaxRevealedTime(prev => Math.max(prev, time))
                    animationFrameRef.current = requestAnimationFrame(updateTime)
                }
            }

            if (isPlaying && player) {
                updateTime()
            } else {
                if (animationFrameRef.current) {
                    cancelAnimationFrame(animationFrameRef.current)
                    animationFrameRef.current = null
                }
            }

            return () => {
                if (animationFrameRef.current) {
                    cancelAnimationFrame(animationFrameRef.current)
                }
            }
        }, [isPlaying, player])

        useEffect(() => {
            const audio = audioRef.current
            if (!audio) return

            if (!activeDubTrack || activeDubTrack.segments.length === 0) {
                audio.pause()
                audio.removeAttribute("src")
                audio.load()
                dubbedSegmentRef.current = null
                playerRef.current?.unMute?.()
                return
            }

            playerRef.current?.mute?.()
            if (!isPlaying) {
                audio.pause()
                return
            }

            const segment = activeDubTrack.segments.find((item) => currentTime >= item.start && currentTime < item.end)
            if (!segment) {
                audio.pause()
                return
            }

            const apiOrigin = API_BASE_URL.substring(0, API_BASE_URL.indexOf("/api/v1"))
            const audioUrl = segment.audio_url.startsWith("http") ? segment.audio_url : `${apiOrigin}${segment.audio_url}`
            if (dubbedSegmentRef.current !== segment.segment_id || audio.src !== audioUrl) {
                audio.src = audioUrl
                audio.load()
                dubbedSegmentRef.current = segment.segment_id ?? null
            }

            const offset = Math.max(0, currentTime - segment.start)
            if (Math.abs(audio.currentTime - offset) > 0.35) audio.currentTime = offset
            audio.play().catch(() => undefined)
        }, [activeDubTrack, currentTime, isPlaying])

        const getCurrentWordIndex = () => {
            if (!transcriptWords || transcriptWords.length === 0) return -1
            for (let i = 0; i < transcriptWords.length; i++) {
                const word = transcriptWords[i]
                if (currentTime >= word.start && currentTime < word.end) {
                    return i
                }
            }
            return -1
        }

        const currentWordIndex = getCurrentWordIndex()

        const handleWordClick = (word: TranscriptWord, index: number) => {
            if (!player || !player.seekTo) return

            if (index === currentWordIndex) {
                if (isPlaying) {
                    player.pauseVideo()
                    setIsPlaying(false)
                } else {
                    player.playVideo()
                    setIsPlaying(true)
                }
                return
            }

            const seekTime = word.start + 0.001
            player.seekTo(seekTime, true)
            player.pauseVideo()
            setCurrentTime(seekTime)
            setIsPlaying(false)
        }

        const handleSemanticSearch = async () => {
            if (!searchQuery.trim() || !videoId) return
            setIsSearching(true)
            setActiveTab("search")
            try {
                const results = await searchVideoSemantically(videoId, searchQuery, 6)
                setSearchResults(results)
            } catch (err) {
                console.error("Semantic search failed:", err)
            } finally {
                setIsSearching(false)
            }
        }

        const formatTime = (seconds: number) => {
            const mins = Math.floor(seconds / 60)
            const secs = Math.floor(seconds % 60)
            return `${mins}:${secs.toString().padStart(2, '0')}`
        }

        const togglePlayPause = () => {
            if (!player) return
            if (isPlaying) {
                player.pauseVideo()
            } else {
                player.playVideo()
            }
        }

        const groupWordsIntoLines = () => {
            if (!transcriptWords || transcriptWords.length === 0) return []

            const lines: { words: TranscriptWord[], startIndex: number }[] = []
            let currentLine: TranscriptWord[] = []
            let lineStartIndex = 0

            transcriptWords.forEach((word, index) => {
                currentLine.push(word)
                const isPunctuation = word.word.match(/[.!?;,]$/)
                const isLongEnough = currentLine.length >= 8
                const isVeryLong = currentLine.length >= 12

                if ((isPunctuation && isLongEnough) || isVeryLong) {
                    lines.push({ words: [...currentLine], startIndex: lineStartIndex })
                    currentLine = []
                    lineStartIndex = index + 1
                }
            })

            if (currentLine.length > 0) {
                lines.push({ words: currentLine, startIndex: lineStartIndex })
            }

            return lines
        }

        const lines = useMemo(() => groupWordsIntoLines(), [transcriptWords])
        const translatedCaptions = useMemo(
            () => (activeDubTrack?.segments || []).filter((segment) => segment.translated_text?.trim()),
            [activeDubTrack]
        )

        return (
            <div className="h-full flex flex-col bg-background rounded-xl overflow-hidden border shadow-sm">
                {/* Video Frame */}
                <div className="w-full aspect-video relative bg-black group shrink-0">
                    <iframe
                        id="youtube-player"
                        src={`${getYouTubeEmbedUrl(videoUrl)}?enablejsapi=1`}
                        className="absolute top-0 left-0 w-full h-full"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                    />
                    <audio ref={audioRef} preload="auto" className="hidden" />

                    {isDubbingLoading && (
                        <div className="absolute inset-0 z-20 flex items-center justify-center bg-black/70 p-6 text-center text-white">
                            <div className="flex flex-col items-center gap-3">
                                <Loader2 className="h-8 w-8 animate-spin" />
                                <p className="text-sm font-medium">This video is being translated. Please wait a moment...</p>
                            </div>
                        </div>
                    )}

                    {/* Controls Overlay */}
                    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-background/95 backdrop-blur-sm rounded-full px-6 py-3 shadow-lg border opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10">
                        <div className="flex items-center gap-4">
                            <Button
                                size="sm"
                                variant="ghost"
                                onClick={togglePlayPause}
                                className="h-8 w-8 p-0 rounded-full hover:bg-primary/10"
                            >
                                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                            </Button>
                            <div className="flex items-center gap-2 text-xs font-medium">
                                <Clock className="h-3 w-3 text-muted-foreground" />
                                <span>{formatTime(currentTime)}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Subtitle / Semantic Search Container */}
                <div className="flex-1 min-h-[140px] lg:flex-none lg:h-[260px] border-t bg-gradient-to-b from-muted/30 to-background flex flex-col relative">
                    {/* Header with Search & Tabs */}
                    <div className="p-3 border-b bg-card/60 backdrop-blur-sm flex-none flex flex-col sm:flex-row items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                            <Button
                                size="sm"
                                variant={activeTab === "captions" ? "default" : "ghost"}
                                className="h-7 text-xs rounded-lg px-2.5"
                                onClick={() => setActiveTab("captions")}
                            >
                                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse mr-1.5"></span>
                                {liveCaptionsLabel}
                            </Button>
                            <Button
                                size="sm"
                                variant={activeTab === "search" ? "default" : "ghost"}
                                className="h-7 text-xs rounded-lg px-2.5"
                                onClick={() => setActiveTab("search")}
                            >
                                <Sparkles className="h-3 w-3 text-primary mr-1.5" />
                                Semantic Moments
                            </Button>
                        </div>

                        {/* Semantic Search Bar */}
                        <div className="flex items-center gap-1.5 w-full sm:w-auto">
                            <div className="relative w-full sm:w-56">
                                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                                <Input
                                    placeholder="Search in video..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSemanticSearch()}
                                    className="h-7 text-xs pl-8 pr-2 rounded-lg bg-background"
                                />
                            </div>
                            <Button
                                size="sm"
                                variant="outline"
                                className="h-7 px-2 text-xs"
                                onClick={handleSemanticSearch}
                                disabled={isSearching || !searchQuery.trim()}
                            >
                                Search
                            </Button>
                        </div>
                    </div>

                    {/* Tab 1: Live Interactive Captions */}
                    {activeTab === "captions" && (
                        translatedCaptions.length > 0 ? (
                            <div className="flex-1 overflow-y-auto p-5 scroll-smooth relative">
                                <div className="mb-3 text-[11px] font-medium uppercase tracking-wide text-primary">Translated captions</div>
                                <div className="space-y-3">
                                    {translatedCaptions.map((caption) => {
                                        const isCurrentCaption = currentTime >= caption.start && currentTime <= caption.end
                                        const isPastCaption = currentTime > caption.end
                                        return (
                                            <button
                                                type="button"
                                                key={caption.segment_id ?? `${caption.start}-${caption.end}`}
                                                onClick={() => {
                                                    player?.seekTo?.(caption.start, true)
                                                    setCurrentTime(caption.start)
                                                }}
                                                className={`block w-full rounded-lg p-2 text-left leading-relaxed transition-colors ${isCurrentCaption ? "bg-blue-600 text-white font-semibold shadow-md" : isPastCaption ? "text-muted-foreground hover:text-foreground" : "text-foreground hover:bg-primary/10"}`}
                                            >
                                                <span className="mr-2 font-mono text-[10px] opacity-70">{formatTime(caption.start)}</span>
                                                {caption.translated_text}
                                            </button>
                                        )
                                    })}
                                </div>
                            </div>
                        ) : transcriptWords && transcriptWords.length > 0 ? (
                            <div className="flex-1 overflow-y-auto p-5 scroll-smooth relative">
                                <div className="space-y-3">
                                    {lines.map((line) => {
                                        const lineStartTime = line.words[0]?.start || 0
                                        const lineEndTime = line.words[line.words.length - 1]?.end || 0
                                        const isCurrentLine = currentTime >= lineStartTime && currentTime <= lineEndTime

                                        return (
                                            <div
                                                key={line.startIndex}
                                                className={`leading-relaxed transition-opacity duration-300 ${isCurrentLine ? 'opacity-100' : 'opacity-70 hover:opacity-100'}`}
                                            >
                                                {line.words.map((word, wordIndexInLine) => {
                                                    const globalIndex = line.startIndex + wordIndexInLine
                                                    const isActive = globalIndex === currentWordIndex
                                                    const isPast = currentTime > word.end
                                                    const isHovered = hoveredWordIndex === globalIndex
                                                    const isFuture = word.start > maxRevealedTime
                                                    if (isFuture) return null

                                                    return (
                                                        <span
                                                            key={globalIndex}
                                                            onClick={() => handleWordClick(word, globalIndex)}
                                                            onMouseEnter={() => setHoveredWordIndex(globalIndex)}
                                                            onMouseLeave={() => setHoveredWordIndex(null)}
                                                            className={`
                                                                inline-block mr-1.5 px-1.5 py-0.5 rounded-md
                                                                cursor-pointer select-none
                                                                transition-all duration-200 ease-out
                                                                ${isActive
                                                                    ? 'bg-blue-600 text-white font-bold scale-110 shadow-md z-10 px-2'
                                                                    : isHovered
                                                                        ? 'bg-primary/20 text-foreground scale-105'
                                                                        : isPast
                                                                            ? 'text-muted-foreground hover:text-foreground'
                                                                            : 'text-foreground'
                                                                }
                                                            `}
                                                            title={`${word.word} (${formatTime(word.start)})`}
                                                        >
                                                            {word.word || ' '}
                                                        </span>
                                                    )
                                                })}
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 flex items-center justify-center p-6 text-center text-muted-foreground text-xs">
                                Captions will highlight word-by-word as the lesson plays.
                            </div>
                        )
                    )}

                    {/* Tab 2: Semantic Search Results */}
                    {activeTab === "search" && (
                        <div className="flex-1 overflow-y-auto p-4 space-y-2">
                            {isSearching ? (
                                <div className="flex items-center justify-center h-full text-xs text-muted-foreground gap-2">
                                    <Sparkles className="h-4 w-4 animate-spin text-primary" />
                                    <span>Searching moments using Mistral embeddings...</span>
                                </div>
                            ) : searchResults.length > 0 ? (
                                <div className="space-y-2">
                                    <p className="text-[11px] text-muted-foreground font-medium">Click any timestamp to jump to that moment:</p>
                                    {searchResults.map((res, idx) => (
                                        <div
                                            key={idx}
                                            onClick={() => {
                                                if (player && player.seekTo) {
                                                    player.seekTo(res.start_time, true)
                                                    player.playVideo()
                                                    setIsPlaying(true)
                                                    setCurrentTime(res.start_time)
                                                }
                                            }}
                                            className="p-3 rounded-xl bg-card border hover:border-primary/50 cursor-pointer transition-all flex items-start justify-between gap-3 group shadow-xs"
                                        >
                                            <div className="flex-1">
                                                <p className="text-xs text-foreground line-clamp-2 leading-relaxed">
                                                    "{res.text}"
                                                </p>
                                                <div className="flex items-center gap-2 mt-1.5">
                                                    <span className="inline-flex items-center gap-1 font-mono text-[11px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-md">
                                                        <Play className="h-2.5 w-2.5 fill-current" />
                                                        {formatTime(res.start_time)}
                                                    </span>
                                                    <Badge variant="outline" className="text-[10px]">
                                                        {Math.round(res.similarity * 100)}% match
                                                    </Badge>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground text-xs p-4">
                                    <Search className="h-6 w-6 text-muted-foreground/50 mb-2" />
                                    <p className="font-medium text-foreground">Type a concept above to search inside the video</p>
                                    <p className="text-[11px] mt-0.5">Powered by pgvector and mistral-embed</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        )
    }
)
