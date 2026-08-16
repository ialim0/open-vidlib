"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { X, Trophy, BookOpen, Play, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

export interface Flashcard {
    question: string
    options: string[]
    correctOption: number
    source: string
}

interface FlashcardQuizProps {
    flashcards: Flashcard[]
    onClose?: () => void
    onSeekVideo?: (timeInSeconds: number) => void
    translations?: {
        questionOf: string
        showSource: string
        correct: string
        incorrect: string
        correctAnswer: string
        sourceReference: string
        nextQuestion: string
        viewResults: string
        quizComplete: string
        yourScore: string
        retakeQuiz: string
        closeQuiz: string
    }
}

export function FlashcardQuiz({ flashcards, onClose, onSeekVideo, translations }: FlashcardQuizProps) {
    const [currentIndex, setCurrentIndex] = useState(0)
    const [selectedOption, setSelectedOption] = useState<number | null>(null)
    const [showSource, setShowSource] = useState(false)
    const [score, setScore] = useState(0)
    const [completed, setCompleted] = useState(false)
    const [answers, setAnswers] = useState<boolean[]>(new Array(flashcards.length).fill(false))

    // Default translations
    const t = translations || {
        questionOf: "Question {current} of {total}",
        showSource: "Show Source",
        correct: "Correct!",
        incorrect: "Incorrect",
        correctAnswer: "Correct Answer:",
        sourceReference: "Source Reference:",
        nextQuestion: "Next Question",
        viewResults: "View Results",
        quizComplete: "Quiz Complete!",
        yourScore: "Your Score",
        retakeQuiz: "Retake Quiz",
        closeQuiz: "Close Quiz",
    }

    const currentCard = flashcards[currentIndex]

    // Safety check - if card format is invalid, show error
    if (!currentCard || !currentCard.options || !Array.isArray(currentCard.options)) {
        return (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div className="bg-card rounded-xl border shadow-2xl p-8 max-w-md w-full text-center">
                    <p className="text-lg font-medium mb-4">Error loading quiz</p>
                    <p className="text-sm text-muted-foreground mb-6">The quiz data format is invalid. Please try again.</p>
                    <Button onClick={onClose}>Close</Button>
                </div>
            </div>
        )
    }

    const handleSelectOption = (optionIndex: number) => {
        if (!showSource) {
            setSelectedOption(optionIndex)
        }
    }

    const handleFlipToSource = () => {
        if (selectedOption !== null) {
            setShowSource(true)

            // Record whether the answer was correct
            const isCorrect = selectedOption === currentCard.correctOption
            const newAnswers = [...answers]
            newAnswers[currentIndex] = isCorrect
            setAnswers(newAnswers)

            if (isCorrect) {
                setScore(prev => prev + 1)
            }
        }
    }

    const handleNext = () => {
        if (currentIndex < flashcards.length - 1) {
            setSelectedOption(null)
            setShowSource(false)
            setCurrentIndex(prev => prev + 1)
        } else {
            setCompleted(true)
        }
    }

    // Parse timestamp from source text (e.g., "[02:15]" -> 135 seconds)
    const parseTimestamp = (timestamp: string): number => {
        const match = timestamp.match(/\[(\d{1,2}):(\d{2})\]/)
        if (match) {
            const minutes = parseInt(match[1], 10)
            const seconds = parseInt(match[2], 10)
            return minutes * 60 + seconds
        }
        return 0
    }

    // Render source with clickable timestamps
    const renderSource = (source: string) => {
        const timestampRegex = /\[(\d{1,2}:\d{2})\]/g
        const parts = []
        let lastIndex = 0
        let match

        while ((match = timestampRegex.exec(source)) !== null) {
            // Add text before timestamp
            if (match.index > lastIndex) {
                parts.push(
                    <span key={`text-${lastIndex}`}>
                        {source.substring(lastIndex, match.index)}
                    </span>
                )
            }

            // Add clickable timestamp
            const timestamp = match[0]
            const timeInSeconds = parseTimestamp(timestamp)
            parts.push(
                <button
                    key={`timestamp-${match.index}`}
                    onClick={(e) => {
                        e.stopPropagation()
                        if (onSeekVideo) {
                            onSeekVideo(timeInSeconds)
                        }
                        // Close modal so user can watch the video
                        if (onClose) {
                            setTimeout(() => onClose(), 300)
                        }
                    }}
                    className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors font-mono text-xs font-semibold"
                >
                    <Play className="h-2.5 w-2.5" />
                    {timestamp}
                </button>
            )

            lastIndex = match.index + match[0].length
        }

        // Add remaining text
        if (lastIndex < source.length) {
            parts.push(
                <span key={`text-${lastIndex}`}>
                    {source.substring(lastIndex)}
                </span>
            )
        }

        return parts.length > 0 ? parts : source
    }

    if (completed) {
        const percentage = Math.round((score / flashcards.length) * 100)
        let gradeMessage = ""
        if (percentage >= 80) gradeMessage = "Excellent Work!"
        else if (percentage >= 60) gradeMessage = "Good Job!"
        else gradeMessage = "Keep Practicing!"

        return (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div className="bg-card rounded-xl border shadow-2xl p-8 max-w-md w-full">
                    <div className="flex flex-col items-center space-y-6">
                        <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
                            <Trophy className="h-10 w-10 text-primary" />
                        </div>
                        <div className="text-center space-y-2">
                            <h3 className="text-2xl font-bold">{t.quizComplete}</h3>
                            <p className="text-muted-foreground">{t.yourScore}: {score} / {flashcards.length}</p>
                            <div className="text-4xl font-bold text-primary mt-4">{percentage}%</div>
                        </div>
                        <div className="flex gap-4 w-full pt-4">
                            <Button variant="outline" className="flex-1" onClick={onClose}>{t.closeQuiz}</Button>
                            <Button className="flex-1" onClick={() => {
                                setCurrentIndex(0)
                                setSelectedOption(null)
                                setShowSource(false)
                                setScore(0)
                                setCompleted(false)
                                setAnswers(new Array(flashcards.length).fill(false))
                            }}>{t.retakeQuiz}</Button>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-card rounded-xl border shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-card z-10">
                    <div className="flex items-center gap-3">
                        <div className="text-sm font-medium text-muted-foreground">
                            {t.questionOf.replace('{current}', String(currentIndex + 1)).replace('{total}', String(flashcards.length))}
                        </div>
                        <div className="flex gap-1">
                            {flashcards.map((_, idx) => (
                                <div
                                    key={idx}
                                    className={cn(
                                        "h-1.5 w-6 rounded-full transition-colors",
                                        idx === currentIndex ? "bg-primary" :
                                            idx < currentIndex ? "bg-primary/40" : "bg-muted"
                                    )}
                                />
                            ))}
                        </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X className="h-5 w-5" />
                    </Button>
                </div>

                {/* Question and Options */}
                {!showSource ? (
                    <div className="p-8 space-y-6">
                        <h2 className="text-2xl font-bold leading-relaxed">{currentCard.question}</h2>

                        <div className="space-y-3">
                            {currentCard.options.map((option, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSelectOption(index)}
                                    className={cn(
                                        "w-full text-left p-4 rounded-lg border-2 transition-all",
                                        selectedOption === index
                                            ? "border-primary bg-primary/10 font-medium"
                                            : "border-border hover:border-primary/50 hover:bg-muted/50"
                                    )}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={cn(
                                            "w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0",
                                            selectedOption === index ? "border-primary bg-primary" : "border-border"
                                        )}>
                                            {selectedOption === index && (
                                                <div className="w-2 h-2 bg-white rounded-full" />
                                            )}
                                        </div>
                                        <span>{option}</span>
                                    </div>
                                </button>
                            ))}
                        </div>

                        <Button
                            className="w-full"
                            size="lg"
                            onClick={handleFlipToSource}
                            disabled={selectedOption === null}
                        >
                            <BookOpen className="mr-2 h-5 w-5" />
                            {t.showSource}
                        </Button>
                    </div>
                ) : (
                    /* Source View */
                    <div className="p-8 space-y-6">
                        <div className="text-center space-y-4">
                            <div className={cn(
                                "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium",
                                selectedOption === currentCard.correctOption
                                    ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                                    : "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400"
                            )}>
                                {selectedOption === currentCard.correctOption ? `✓ ${t.correct}` : `✗ ${t.incorrect}`}
                            </div>

                            <div>
                                <p className="text-sm text-muted-foreground mb-2">{t.correctAnswer}</p>
                                <p className="font-medium text-lg">{currentCard.options[currentCard.correctOption]}</p>
                            </div>
                        </div>

                        <div className="bg-muted/50 p-4 rounded-lg border">
                            <div className="flex items-center gap-2 font-semibold text-sm text-muted-foreground mb-2">
                                <BookOpen className="h-4 w-4" />
                                {t.sourceReference}
                            </div>
                            <p className="text-sm leading-relaxed">
                                {renderSource(currentCard.source)}
                            </p>
                        </div>

                        <Button
                            className="w-full"
                            size="lg"
                            onClick={handleNext}
                        >
                            {currentIndex < flashcards.length - 1 ? (
                                <>
                                    {t.nextQuestion}
                                    <ChevronRight className="ml-2 h-5 w-5" />
                                </>
                            ) : (
                                t.viewResults
                            )}
                        </Button>
                    </div>
                )}
            </div>
        </div>
    )
}
