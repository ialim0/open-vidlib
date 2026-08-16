"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ArrowLeft, Sparkles, NotebookPen, Mic, Bold, Italic, Underline, List, Link as LinkIcon, AlignCenter, AlignJustify, ListOrdered, Volume2, Loader2 } from "lucide-react"
import { getYouTubeEmbedUrl } from "@/lib/utils"
import { VideoPlayerWithTranscript } from "@/components/video-player-with-transcript"
import { CoumbaChat } from "@/components/coumba-chat"
import { useLanguage } from "@/lib/i18n/language-context"
import { requestDubbedTrack, DubbedTrack } from "@/lib/api/videos"
import { Flashcard } from "@/components/flashcard-quiz"
import Link from "next/link"

interface TranscriptWord {
    word: string
    start: number
    end: number
}

interface ResourcePageClientProps {
    resource: {
        id: string
        title: string
        type: "video"
        url: string
        category?: string
        transcript?: string
        transcriptWords?: TranscriptWord[]
        flashcards?: Flashcard[]
        flashcardsByLang?: Record<string, Flashcard[]>
    }
}

export function ResourcePageClient({ resource }: ResourcePageClientProps) {
    const { t, language } = useLanguage()
    const [isNoteModalOpen, setIsNoteModalOpen] = useState(false)
    const [noteContent, setNoteContent] = useState("")
    const [activeDubTrack, setActiveDubTrack] = useState<DubbedTrack | null>(null)
    const [dubbingLoadingLang, setDubbingLoadingLang] = useState<string | null>(null)
    const editorRef = useRef<HTMLDivElement>(null)
    const videoPlayerRef = useRef<any>(null)

    useEffect(() => {
        if (isNoteModalOpen) {
            setTimeout(() => {
                const savedNote = localStorage.getItem(`note-${resource.id}`)
                if (editorRef.current) {
                    editorRef.current.innerHTML = savedNote || ""
                    setNoteContent(savedNote || "")
                }
            }, 0)
        }
    }, [resource.id, isNoteModalOpen])

    const handleSeekVideo = (timeInSeconds: number) => {
        if (videoPlayerRef.current && videoPlayerRef.current.seekTo) {
            videoPlayerRef.current.seekTo(timeInSeconds)
        }
    }

    const handleTriggerDubbing = async (targetLang: string) => {
        setDubbingLoadingLang(targetLang)
        try {
            const track = await requestDubbedTrack(resource.id, targetLang, "female")
            if (track) {
                setActiveDubTrack(track)
            }
        } catch (err) {
            console.error("Dubbing failed:", err)
        } finally {
            setDubbingLoadingLang(null)
        }
    }

    const handleSaveNote = () => {
        if (editorRef.current) {
            const content = editorRef.current.innerHTML
            localStorage.setItem(`note-${resource.id}`, content)
            setNoteContent(content)
            setIsNoteModalOpen(false)
        }
    }

    const handleCloseModal = () => {
        setIsNoteModalOpen(false)
    }

    const applyFormat = (command: string, value?: string) => {
        document.execCommand(command, false, value)
        if (editorRef.current) {
            editorRef.current.focus()
        }
    }

    return (
        <div className="min-h-screen flex flex-col bg-background relative">
            {/* Back Button */}
            <Link
                href="/"
                className="absolute top-4 left-4 z-50 bg-background/95 backdrop-blur-sm hover:bg-background p-2 rounded-full transition-all shadow-lg border hover:scale-110"
                title={t.library?.backToLibrary || "Back to Library"}
            >
                <ArrowLeft className="h-5 w-5" />
            </Link>

            {/* Main Content Area */}
            <div className="flex flex-col lg:flex-row flex-1 px-4 lg:px-6 gap-4 lg:gap-6 py-4 justify-center">
                {/* Left Column: Video Viewer + Toolbar */}
                <div className="flex flex-col gap-4 lg:flex-1 min-w-0 max-w-5xl">
                    <div className="flex-none h-[65vh] lg:h-auto bg-muted/30 overflow-hidden rounded-xl border shadow-sm">
                        <VideoPlayerWithTranscript
                            ref={videoPlayerRef}
                            videoId={resource.id}
                            videoUrl={resource.url}
                            transcriptWords={resource.transcriptWords}
                            liveCaptionsLabel={t.library?.liveCaptions || "Live Captions"}
                            activeDubTrack={activeDubTrack}
                        />
                    </div>

                    {/* Toolbar with AI Voiceover & Notes */}
                    <div className="bg-card rounded-xl border shadow-sm p-3">
                        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                            <div className="flex items-center gap-1.5 bg-muted/30 p-1.5 rounded-lg border w-full sm:w-auto justify-center sm:justify-start overflow-x-auto">
                                <div className="flex items-center gap-1.5 px-2 text-xs font-medium text-muted-foreground shrink-0">
                                    <Mic className="h-3.5 w-3.5" />
                                    <span className="hidden sm:inline">AI Voiceover (Voxtral):</span>
                                </div>
                                
                                {["fr", "es", "en", "wo", "ff", "bm"].map((langCode) => {
                                    const labels: Record<string, string> = {
                                        fr: "French",
                                        es: "Spanish",
                                        en: "English",
                                        wo: "Wolof",
                                        ff: "Pulaar",
                                        bm: "Bambara"
                                    }
                                    const isLoading = dubbingLoadingLang === langCode
                                    const isActive = activeDubTrack?.language === langCode

                                    return (
                                        <Button
                                            key={langCode}
                                            variant={isActive ? "default" : "ghost"}
                                            size="sm"
                                            onClick={() => handleTriggerDubbing(langCode)}
                                            disabled={isLoading}
                                            className="h-7 text-xs px-2.5 rounded-md hover:bg-background hover:shadow-xs transition-all"
                                        >
                                            {isLoading && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                                            {labels[langCode] || langCode.toUpperCase()}
                                        </Button>
                                    )
                                })}
                            </div>

                            <div className="flex items-center gap-3 w-full sm:w-auto">
                                <Button
                                    variant="outline"
                                    className="border-primary/20 hover:bg-primary/5 hover:border-primary/40 w-full sm:w-auto h-9"
                                    onClick={() => setIsNoteModalOpen(true)}
                                >
                                    <NotebookPen className="mr-2 h-4 w-4" />
                                    {t.library?.takeNote || "Take Note"}
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: Coumba AI Chat Interface */}
                <div className="w-full lg:w-[420px] h-[85vh] lg:h-auto lg:flex-none shrink-0 bg-background rounded-xl border shadow-sm overflow-hidden">
                    <CoumbaChat
                        videoId={resource.id}
                        resourceTitle={resource.title}
                        transcript={resource.transcript}
                        transcriptWords={resource.transcriptWords}
                        flashcards={resource.flashcardsByLang?.[language] || resource.flashcards}
                        onSeekVideo={handleSeekVideo}
                        onSelectDubLanguage={handleTriggerDubbing}
                    />
                </div>
            </div>

            {/* Note Taking Modal */}
            <Dialog open={isNoteModalOpen} onOpenChange={setIsNoteModalOpen}>
                <DialogContent className="sm:max-w-[600px]">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-semibold">{t.library?.takeNote || "Take Note"}</DialogTitle>
                        <DialogDescription>
                            {t.library?.personalNotes || "Personal study notes for"} "{resource.title}"
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-0 py-4">
                        <div className="flex items-center gap-1 border border-b-0 rounded-t-md bg-muted/30 p-2 flex-wrap">
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-background" onClick={() => applyFormat('bold')}>
                                <Bold className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-background" onClick={() => applyFormat('italic')}>
                                <Italic className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-background" onClick={() => applyFormat('underline')}>
                                <Underline className="h-4 w-4" />
                            </Button>
                            <div className="w-px h-4 bg-border mx-1" />
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-background" onClick={() => applyFormat('justifyCenter')}>
                                <AlignCenter className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-background" onClick={() => applyFormat('justifyFull')}>
                                <AlignJustify className="h-4 w-4" />
                            </Button>
                            <div className="w-px h-4 bg-border mx-1" />
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-background" onClick={() => applyFormat('insertUnorderedList')}>
                                <List className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-background" onClick={() => applyFormat('insertOrderedList')}>
                                <ListOrdered className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-background" onClick={() => {
                                const url = prompt(t.library?.enterUrl || "Enter URL:")
                                if (url) applyFormat('createLink', url)
                            }}>
                                <LinkIcon className="h-4 w-4" />
                            </Button>
                        </div>
                        <div
                            ref={editorRef}
                            contentEditable
                            className="min-h-[300px] w-full rounded-md rounded-t-none border border-t-0 border-input bg-background px-3 py-2 text-base ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 overflow-auto [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5"
                            onInput={(e) => {
                                const content = e.currentTarget.innerHTML
                                setNoteContent(content)
                                localStorage.setItem(`note-${resource.id}`, content)
                            }}
                        />
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={handleCloseModal}>
                            {t.common?.close || "Close"}
                        </Button>
                        <Button onClick={handleSaveNote} className="bg-primary hover:bg-primary/90">
                            <NotebookPen className="mr-2 h-4 w-4" />
                            {t.library?.saveNote || "Save Note"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}
