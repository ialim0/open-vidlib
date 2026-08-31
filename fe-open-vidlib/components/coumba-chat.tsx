"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import {
    Send, Sparkles, Loader2, Play, Search, Volume2, HelpCircle,
    ChevronDown, ChevronUp, History, Info, CheckCircle2, AlertCircle
} from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar"
import { FlashcardQuiz, Flashcard } from "@/components/flashcard-quiz"
import { sendAgentMessage, generateQuizFromAI, SearchResultItem, DubbedTrack, AgentResponse } from "@/lib/api/videos"
import { useLanguage } from "@/lib/i18n/language-context"

interface Message {
    id: string
    role: "user" | "assistant"
    content?: string
    timestamp: string
    type: "text" | "search" | "qa" | "dubbing"
    searchResults?: SearchResultItem[]
    answer?: string
    sources?: SearchResultItem[]
    dubTrack?: DubbedTrack
    hasMemoryContext?: boolean
    isInsufficientEvidence?: boolean
    verified?: boolean
    toolCallCount?: number
    modelUsed?: string
}

interface TranscriptWord {
    word: string
    start: number
    end: number
}

interface CoumbaChatProps {
    videoId?: string
    resourceTitle: string
    transcript?: string
    transcriptWords?: TranscriptWord[]
    flashcards?: Flashcard[]
    onSeekVideo?: (timeInSeconds: number) => void
    onSelectDubLanguage?: (language: string) => void
}

const MULTISTEP_STATUSES = [
    "Analyzing your question...",
    "Searching the transcript & video timestamps...",
    "Checking the answer against the source...",
    "Verifying evidence and finalizing explanation..."
]

export function CoumbaChat({
    videoId,
    resourceTitle,
    transcript,
    transcriptWords,
    flashcards,
    onSeekVideo,
    onSelectDubLanguage
}: CoumbaChatProps) {
    const { t, language } = useLanguage()
    const [messages, setMessages] = useState<Message[]>([])
    const [inputValue, setInputValue] = useState("")
    const [quizCards, setQuizCards] = useState<Flashcard[]>([])
    const [isQuizActive, setIsQuizActive] = useState(false)
    const [isGeneratingQuiz, setIsGeneratingQuiz] = useState(false)
    const [isSendingMessage, setIsSendingMessage] = useState(false)
    const [loadingStepIndex, setLoadingStepIndex] = useState(0)
    const [activeModel, setActiveModel] = useState<string>("Mistral AI")
    const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({})
    const [sessionId] = useState(() => `session-${Math.random().toString(36).substring(2, 9)}`)
    const scrollRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        if (messages.length > 0 && scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" })
        }
    }, [messages, isSendingMessage])

    // Cycle through multi-step progress messages while waiting
    useEffect(() => {
        if (!isSendingMessage) {
            setLoadingStepIndex(0)
            return
        }

        const interval = setInterval(() => {
            setLoadingStepIndex(prev => (prev < MULTISTEP_STATUSES.length - 1 ? prev + 1 : prev))
        }, 2200)

        return () => clearInterval(interval)
    }, [isSendingMessage])

    const parseTimestamp = (timestamp: string): number => {
        const match = timestamp.match(/\[(\d{1,3}):(\d{2})/)
        if (match) {
            const minutes = parseInt(match[1], 10)
            const seconds = parseInt(match[2], 10)
            return minutes * 60 + seconds
        }
        return 0
    }

    const formatSeconds = (seconds: number) => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    const renderTextWithTimestamps = (text: string) => {
        const timestampRegex = /\[(\d{1,3}:\d{2})(?:\s*[-–—]\s*\d{1,3}:\d{2})?\]/g
        const parts = []
        let lastIndex = 0
        let match

        while ((match = timestampRegex.exec(text)) !== null) {
            if (match.index > lastIndex) {
                parts.push(text.substring(lastIndex, match.index))
            }
            const timestamp = match[0]
            const timeInSeconds = parseTimestamp(timestamp)
            parts.push(
                <button
                    key={`ts-${match.index}`}
                    type="button"
                    onClick={() => onSeekVideo?.(timeInSeconds)}
                    className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 bg-primary/10 hover:bg-primary/20 text-primary rounded font-mono text-xs font-semibold transition-colors cursor-pointer border border-primary/20 hover:border-primary/40"
                    title={`Jump to ${timestamp} in video`}
                >
                    <Play className="h-2.5 w-2.5 fill-current" />
                    {timestamp}
                </button>
            )
            lastIndex = match.index + match[0].length
        }

        if (lastIndex < text.length) {
            parts.push(text.substring(lastIndex))
        }

        return parts.length > 0 ? parts : text
    }

    const selectPrompt = (prompt: string) => {
        setInputValue(prompt)
        inputRef.current?.focus()
    }

    const isInsufficient = (text?: string): boolean => {
        if (!text) return false
        const lower = text.toLowerCase()
        return (
            lower.includes("does not provide enough information") ||
            lower.includes("not enough information") ||
            lower.includes("cannot be answered from the video")
        )
    }

    const handleSendMessage = async (text: string = inputValue) => {
        if (!text.trim() || isSendingMessage) return

        const userTurnCount = messages.filter(m => m.role === "user").length
        const isFollowUpQuestion = userTurnCount > 0

        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: text,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            type: "text"
        }

        setMessages(prev => [...prev, userMsg])
        setInputValue("")

        if (text.toLowerCase().includes("quiz")) {
            handleStartQuiz()
            return
        }

        setIsSendingMessage(true)
        setLoadingStepIndex(0)

        try {
            if (videoId) {
                const res: AgentResponse = await sendAgentMessage(videoId, text, sessionId)
                const botMsgId = (Date.now() + 1).toString()

                if (res.model_used) {
                    setActiveModel(res.model_used.includes("small") ? "Mistral Small" : (res.model_used.includes("large") ? "Mistral Large" : res.model_used))
                }

                const answerText = res.answer || res.content || ""
                const insufficient = isInsufficient(answerText)

                if (res.type === "search") {
                    setMessages(prev => [...prev, {
                        id: botMsgId,
                        role: "assistant",
                        type: "search",
                        content: res.content || `Found ${res.results?.length || 0} moments in this video:`,
                        searchResults: res.results || [],
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        hasMemoryContext: isFollowUpQuestion,
                        verified: res.verified,
                        toolCallCount: res.tool_call_count,
                        modelUsed: res.model_used
                    }])
                } else if (res.type === "qa") {
                    setMessages(prev => [...prev, {
                        id: botMsgId,
                        role: "assistant",
                        type: "qa",
                        answer: answerText,
                        sources: res.sources || [],
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        hasMemoryContext: isFollowUpQuestion,
                        isInsufficientEvidence: insufficient,
                        verified: res.verified,
                        toolCallCount: res.tool_call_count,
                        modelUsed: res.model_used
                    }])
                } else if (res.type === "dubbing") {
                    setMessages(prev => [...prev, {
                        id: botMsgId,
                        role: "assistant",
                        type: "dubbing",
                        content: res.content || `Dubbed audio track ready in ${res.language?.toUpperCase()}.`,
                        dubTrack: res.dub_track,
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        hasMemoryContext: isFollowUpQuestion,
                        toolCallCount: res.tool_call_count,
                        modelUsed: res.model_used
                    }])
                } else {
                    setMessages(prev => [...prev, {
                        id: botMsgId,
                        role: "assistant",
                        type: "text",
                        content: answerText || "I am Coumba, your video study companion. Ask me anything!",
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        hasMemoryContext: isFollowUpQuestion,
                        isInsufficientEvidence: insufficient,
                        verified: res.verified,
                        toolCallCount: res.tool_call_count,
                        modelUsed: res.model_used
                    }])
                }
            } else {
                setTimeout(() => {
                    setMessages(prev => [...prev, {
                        id: (Date.now() + 1).toString(),
                        role: "assistant",
                        type: "text",
                        content: `Coumba: Here are insights on "${resourceTitle}". Ask me questions, search keywords, or take a quiz!`,
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        hasMemoryContext: isFollowUpQuestion
                    }])
                }, 600)
            }
        } catch (error) {
            console.error("Failed to process message:", error)
            setMessages(prev => [...prev, {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                type: "text",
                content: "I apologize, but I encountered an issue connecting to the Mistral AI backend. Please verify your backend server is running.",
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }])
        } finally {
            setIsSendingMessage(false)
        }
    }

    const handleStartQuiz = async () => {
        setIsGeneratingQuiz(true)
        setQuizCards([])
        setIsQuizActive(false)

        if (flashcards && flashcards.length > 0) {
            setTimeout(() => {
                setQuizCards(flashcards)
                setIsQuizActive(true)
                setIsGeneratingQuiz(false)
            }, 600)
            return
        }

        if (videoId) {
            try {
                const generated = await generateQuizFromAI(videoId, language, 5)
                if (generated && generated.length > 0) {
                    setQuizCards(generated)
                    setIsQuizActive(true)
                }
            } catch (error) {
                console.error("Quiz generation failed:", error)
            } finally {
                setIsGeneratingQuiz(false)
            }
        } else {
            setIsGeneratingQuiz(false)
        }
    }

    const toggleSources = (msgId: string) => {
        setExpandedSources(prev => ({ ...prev, [msgId]: !prev[msgId] }))
    }

    return (
        <div className="flex flex-col h-full bg-background">
            {/* Header */}
            <div className="p-4 border-b bg-card flex items-center justify-between shrink-0">
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                            <Sparkles className="h-5 w-5 text-primary" />
                        </div>
                        <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-background rounded-full"></div>
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-sm">Coumba</h3>
                            <Badge variant="outline" className="text-[10px] py-0 px-1.5 bg-primary/5 text-primary border-primary/20 font-mono">
                                {activeModel}
                            </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{t.library?.yourLibrarian || "AI Video Tutor"}</p>
                    </div>
                </div>

                <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs border-primary/20 hover:bg-primary/10"
                    onClick={handleStartQuiz}
                    disabled={isGeneratingQuiz || isQuizActive}
                >
                    <Sparkles className="mr-1.5 h-3 w-3 text-primary" />
                    {t.library?.takeQuiz || "Quiz"}
                </Button>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden relative">
                {isQuizActive ? (
                    <div className="h-full p-4 overflow-y-auto">
                        <FlashcardQuiz
                            flashcards={quizCards}
                            onClose={() => setIsQuizActive(false)}
                            onSeekVideo={onSeekVideo}
                            translations={t.library?.quiz}
                        />
                    </div>
                ) : (
                    <ScrollArea className="h-full">
                        <div className="p-4 space-y-4">
                            {messages.length === 0 && (
                                <div className="flex flex-col items-center justify-center h-[260px] text-center p-6 text-muted-foreground">
                                    <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-3">
                                        <Sparkles className="h-6 w-6" />
                                    </div>
                                    <p className="text-sm font-medium text-foreground">{t.library?.videoChatWelcome || "Ask Coumba anything about this lesson!"}</p>
                                    <p className="text-xs text-muted-foreground mt-1 max-w-xs leading-relaxed">
                                        Powered by Mistral AI: Search moments, ask conceptual questions, request voice dubbing, or take a quiz.
                                    </p>
                                </div>
                            )}

                            {messages.map((message) => (
                                <div key={message.id} className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                    {message.role === 'assistant' && (
                                        <Avatar className="h-8 w-8 mt-1 border">
                                            <AvatarImage src="/open-vidlib-logo.png" />
                                            <AvatarFallback className="bg-primary/10 text-primary text-xs">AI</AvatarFallback>
                                        </Avatar>
                                    )}
                                    <div className={`flex flex-col max-w-[88%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
                                        
                                        {/* Insufficient Evidence Empty State */}
                                        {message.isInsufficientEvidence ? (
                                            <div className="w-full bg-card border border-border/80 rounded-2xl p-4 shadow-xs space-y-3">
                                                <div className="flex items-center gap-2">
                                                    <Badge variant="outline" className="text-[10px] py-0.5 px-2 bg-muted/60 text-muted-foreground border-border flex items-center gap-1 font-medium">
                                                        <Info className="h-3 w-3 text-primary" />
                                                        Insufficient Lesson Evidence
                                                    </Badge>
                                                    {message.hasMemoryContext && (
                                                        <Badge variant="outline" className="text-[10px] py-0.5 px-1.5 bg-primary/5 text-primary border-primary/20 flex items-center gap-1">
                                                            <History className="h-2.5 w-2.5" />
                                                            Session Context
                                                        </Badge>
                                                    )}
                                                </div>
                                                <p className="text-xs text-foreground/90 leading-relaxed">
                                                    {message.answer || message.content || "The video does not provide enough information to answer that."}
                                                </p>
                                                <div className="pt-2 border-t border-border/60 text-[11px] text-muted-foreground flex items-center gap-1.5">
                                                    <CheckCircle2 className="h-3 w-3 text-primary/70 shrink-0" />
                                                    <span>Coumba only makes claims backed by verified timestamps in this video.</span>
                                                </div>
                                            </div>
                                        ) : (
                                            <>
                                                {/* Standard Text Message */}
                                                {message.type === "text" && (
                                                    <div className={`rounded-2xl px-4 py-3 text-sm shadow-xs leading-relaxed ${message.role === 'user'
                                                        ? 'bg-primary text-primary-foreground rounded-tr-none'
                                                        : 'bg-muted/50 border text-foreground rounded-tl-none space-y-1.5'
                                                    }`}>
                                                        {message.role === 'assistant' && message.hasMemoryContext && (
                                                            <div className="mb-1">
                                                                <Badge variant="outline" className="text-[10px] py-0 px-1.5 bg-primary/10 text-primary border-primary/20 flex items-center gap-1 w-fit">
                                                                    <History className="h-2.5 w-2.5" />
                                                                    Session Context
                                                                </Badge>
                                                            </div>
                                                        )}
                                                        <div>{renderTextWithTimestamps(message.content || "")}</div>
                                                    </div>
                                                )}

                                                {/* Semantic Search Result Card */}
                                                {message.type === "search" && (
                                                    <div className="w-full bg-card border rounded-2xl p-4 shadow-xs space-y-3">
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-2 text-xs font-semibold text-primary">
                                                                <Search className="h-3.5 w-3.5" />
                                                                <span>Semantic Moments Found</span>
                                                            </div>
                                                            {message.hasMemoryContext && (
                                                                <Badge variant="outline" className="text-[10px] py-0 px-1.5 bg-primary/5 text-primary border-primary/20 flex items-center gap-1">
                                                                    <History className="h-2.5 w-2.5" />
                                                                    Session Context
                                                                </Badge>
                                                            )}
                                                        </div>
                                                        <div className="space-y-2">
                                                            {message.searchResults && message.searchResults.length > 0 ? (
                                                                message.searchResults.map((res, idx) => (
                                                                    <div
                                                                        key={idx}
                                                                        onClick={() => onSeekVideo?.(res.start_time)}
                                                                        className="p-2.5 rounded-xl bg-muted/40 hover:bg-primary/10 border cursor-pointer transition-all flex items-start justify-between gap-3 group"
                                                                    >
                                                                        <div className="flex-1">
                                                                            <p className="text-xs text-foreground line-clamp-2 leading-relaxed">
                                                                                "{res.text}"
                                                                            </p>
                                                                            <div className="flex items-center gap-2 mt-1.5">
                                                                                <span className="inline-flex items-center gap-1 font-mono text-[11px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-md">
                                                                                    <Play className="h-2.5 w-2.5 fill-current" />
                                                                                    {formatSeconds(res.start_time)}
                                                                                </span>
                                                                                <span className="text-[10px] text-muted-foreground">
                                                                                    {Math.round(res.similarity * 100)}% match
                                                                                </span>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                ))
                                                            ) : (
                                                                <p className="text-xs text-muted-foreground">No moments found matching this query.</p>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* RAG Q&A Grounded Response */}
                                                {message.type === "qa" && (
                                                    <div className="w-full bg-card border rounded-2xl p-4 shadow-xs space-y-3">
                                                        <div className="flex items-center gap-1.5 flex-wrap">
                                                            {message.hasMemoryContext && (
                                                                <Badge variant="outline" className="text-[10px] py-0.5 px-2 bg-primary/5 text-primary border-primary/20 flex items-center gap-1">
                                                                    <History className="h-2.5 w-2.5" />
                                                                    Session Context
                                                                </Badge>
                                                            )}
                                                            {message.verified && (
                                                                <Badge variant="outline" className="text-[10px] py-0.5 px-2 bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20 flex items-center gap-1">
                                                                    <CheckCircle2 className="h-2.5 w-2.5" />
                                                                    Verified Evidence
                                                                </Badge>
                                                            )}
                                                            {message.toolCallCount && message.toolCallCount > 1 && (
                                                                <Badge variant="outline" className="text-[10px] py-0.5 px-2 bg-muted/60 text-muted-foreground border-border flex items-center gap-1">
                                                                    <Sparkles className="h-2.5 w-2.5 text-primary" />
                                                                    Multi-Step ({message.toolCallCount} calls)
                                                                </Badge>
                                                            )}
                                                        </div>
                                                        <div className="text-sm leading-relaxed text-foreground">
                                                            {renderTextWithTimestamps(message.answer || "")}
                                                        </div>

                                                        {message.sources && message.sources.length > 0 && (
                                                            <div className="pt-2 border-t text-xs">
                                                                <button
                                                                    onClick={() => toggleSources(message.id)}
                                                                    className="flex items-center justify-between w-full text-muted-foreground hover:text-foreground py-1 cursor-pointer"
                                                                >
                                                                    <span className="font-medium flex items-center gap-1.5">
                                                                        <CheckCircle2 className="h-3 w-3 text-primary" />
                                                                        Transcript Sources ({message.sources.length})
                                                                    </span>
                                                                    {expandedSources[message.id] ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                                                                </button>

                                                                {expandedSources[message.id] && (
                                                                    <div className="space-y-1.5 mt-2">
                                                                        {message.sources.map((src, sIdx) => (
                                                                            <div
                                                                                key={sIdx}
                                                                                onClick={() => onSeekVideo?.(src.start_time)}
                                                                                className="p-2 rounded-lg bg-muted/40 hover:bg-muted text-[11px] cursor-pointer flex items-center justify-between border border-transparent hover:border-border transition-colors"
                                                                            >
                                                                                <span className="line-clamp-1 flex-1">"{src.text}"</span>
                                                                                <Badge variant="outline" className="ml-2 font-mono text-[10px]">
                                                                                    {formatSeconds(src.start_time)}
                                                                                </Badge>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                )}

                                                {/* Dubbing Response */}
                                                {message.type === "dubbing" && (
                                                    <div className="w-full bg-card border rounded-2xl p-4 shadow-xs space-y-3">
                                                        <div className="flex items-center gap-2 text-xs font-semibold text-green-600 dark:text-green-400">
                                                            <Volume2 className="h-3.5 w-3.5" />
                                                            <span>AI Voice Dubbing Ready</span>
                                                        </div>
                                                        <p className="text-xs text-foreground">{message.content}</p>
                                                        {message.dubTrack && (
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                className="w-full text-xs h-8"
                                                                onClick={() => onSelectDubLanguage?.(message.dubTrack!.language)}
                                                            >
                                                                <Volume2 className="mr-1.5 h-3.5 w-3.5" />
                                                                Listen to {message.dubTrack.language.toUpperCase()} Track
                                                            </Button>
                                                        )}
                                                    </div>
                                                )}
                                            </>
                                        )}

                                        <span className="text-[11px] text-muted-foreground mt-1 px-1">{message.timestamp}</span>
                                    </div>
                                </div>
                            ))}

                            {(isSendingMessage || isGeneratingQuiz) && (
                                <div className="flex gap-3">
                                    <Avatar className="h-8 w-8 mt-1 border">
                                        <AvatarImage src="/open-vidlib-logo.png" />
                                        <AvatarFallback className="bg-primary/10 text-primary text-xs">AI</AvatarFallback>
                                    </Avatar>
                                    <div className="bg-card border rounded-2xl rounded-tl-none p-3.5 shadow-xs space-y-2 max-w-[85%]">
                                        <div className="flex items-center gap-2 text-xs text-foreground font-medium">
                                            <Loader2 className="h-4 w-4 animate-spin text-primary shrink-0" />
                                            <span>
                                                {isGeneratingQuiz
                                                    ? (t.library?.creatingQuiz || "Generating quiz questions...")
                                                    : MULTISTEP_STATUSES[loadingStepIndex]
                                                }
                                            </span>
                                        </div>
                                        {!isGeneratingQuiz && (
                                            <div className="flex items-center gap-1.5 pl-6">
                                                {MULTISTEP_STATUSES.map((_, idx) => (
                                                    <div
                                                        key={idx}
                                                        className={`h-1.5 rounded-full transition-all duration-300 ${
                                                            idx === loadingStepIndex
                                                                ? "w-4 bg-primary"
                                                                : idx < loadingStepIndex
                                                                ? "w-2 bg-primary/40"
                                                                : "w-2 bg-muted"
                                                        }`}
                                                    />
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            <div ref={scrollRef} />
                        </div>
                    </ScrollArea>
                )}
            </div>

            {/* Quick Action Suggestion Pills */}
            {!isQuizActive && (
                <div className="px-3 pt-2 pb-1 border-t bg-card/50 flex items-center gap-1.5 overflow-x-auto text-xs">
                    <button
                        onClick={() => selectPrompt("Where in the video is this concept explained?")}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground text-[11px] font-medium transition-colors shrink-0 cursor-pointer"
                    >
                        <Search className="h-3 w-3" />
                        Search Moments
                    </button>
                    <button
                        onClick={() => selectPrompt("Explain the key intuition and analogy of this lesson")}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground text-[11px] font-medium transition-colors shrink-0 cursor-pointer"
                    >
                        <HelpCircle className="h-3 w-3" />
                        Explain Concept
                    </button>
                    <button
                        onClick={() => handleSendMessage("Please generate French audio dub for this video")}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground text-[11px] font-medium transition-colors shrink-0 cursor-pointer"
                    >
                        <Volume2 className="h-3 w-3" />
                        Dub in French
                    </button>
                </div>
            )}

            {/* Input Area */}
            <div className="p-3 border-t bg-card space-y-2 shrink-0">
                <div className="flex gap-2">
                    <Input
                        ref={inputRef}
                        placeholder="Ask Coumba, search timestamps, or request dubbing..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                        className="flex-1 h-10 text-sm rounded-xl"
                        disabled={isQuizActive || isSendingMessage}
                    />
                    <Button
                        size="icon"
                        onClick={() => handleSendMessage()}
                        disabled={!inputValue.trim() || isQuizActive || isSendingMessage}
                        className="h-10 w-10 shrink-0 rounded-xl"
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    )
}
