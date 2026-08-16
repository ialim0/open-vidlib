"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { Search, Video, ArrowRight, Sparkles, Play, BookOpen, Database, Globe, CheckCircle2 } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useLanguage } from "@/lib/i18n/language-context"
import { LanguageSwitcher } from "@/components/language-switcher"
import { SiteFooter } from "@/components/site-footer"
import { getVideos, VideoItem } from "@/lib/api/videos"

export default function HomePage() {
  const { t } = useLanguage()
  const [videos, setVideos] = useState<VideoItem[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [activeCategory, setActiveCategory] = useState<string>("All")
  const [loading, setLoading] = useState(true)

  const categories = ["All", "Science", "Technology", "Engineering", "Mathematics"]

  useEffect(() => {
    async function loadVideos() {
      setLoading(true)
      try {
        const data = await getVideos({ category: activeCategory, search: searchQuery })
        setVideos(data)
      } catch (err) {
        console.error("Failed to load videos:", err)
      } finally {
        setLoading(false)
      }
    }
    loadVideos()
  }, [activeCategory, searchQuery])

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case "All": return t.library?.types?.all || "All"
      case "Science": return t.library?.categories?.science || "Science"
      case "Technology": return t.library?.categories?.technology || "Technology"
      case "Engineering": return t.library?.categories?.engineering || "Engineering"
      case "Mathematics": return t.library?.categories?.math || "Mathematics"
      default: return category
    }
  }

  const getVideoTitle = (originalTitle: string) => {
    const titleMap: Record<string, string> = {
      "La Gravité Expliquée aux Enfants": t.library?.videoTitles?.gravity || originalTitle,
      "Qu'est-ce que le Test de Turing ?": t.library?.videoTitles?.turing || originalTitle,
      "Les chiffres affolants de la pyramide de Khéops": t.library?.videoTitles?.pyramid || originalTitle,
      "À quoi sert le théorème de Pythagore ?": t.library?.videoTitles?.pythagoras || originalTitle,
    }
    return titleMap[originalTitle] || originalTitle
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return "Lesson"
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-primary/20">
      {/* Top Navigation */}
      <header className="border-b bg-card/80 backdrop-blur sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image
              src="/gandalab-logo.png"
              alt="GandaLab Logo"
              width={38}
              height={38}
              className="rounded-lg shadow-sm"
            />
            <div>
              <span className="text-xl font-bold tracking-tight text-foreground">GandaLab</span>
              <span className="hidden sm:inline-block ml-2 text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium border border-primary/20">
                Open Source
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden md:inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <Globe className="h-4 w-4" />
              <span>GitHub</span>
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-8 md:pt-20 md:pb-12 border-b bg-gradient-to-b from-muted/30 to-background">
        <div className="container mx-auto px-4 text-center max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold uppercase tracking-wider mb-6 border border-primary/20">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Interactive STEM Video Library</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-foreground text-balance mb-6">
            {t.home?.subtitle || "Democratizing STEM Learning Through AI"}
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground text-balance max-w-2xl mx-auto mb-10 leading-relaxed">
            {t.library?.subtitle || "Explore curated educational videos with real-time synchronized transcripts, interactive Coumba AI assistant, and multi-language flashcards."}
          </p>

          {/* Search & Filter Bar directly in Hero */}
          <div className="max-w-2xl mx-auto space-y-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                placeholder={t.library?.searchPlaceholder || "Search videos, STEM lessons, topics..."}
                className="pl-12 h-14 text-base rounded-2xl shadow-sm border-2 focus-visible:ring-primary/20 bg-background"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Category Pills */}
            <div className="flex flex-wrap gap-2 justify-center items-center pt-2">
              {categories.map((cat) => (
                <Badge
                  key={cat}
                  variant={activeCategory === cat ? "default" : "outline"}
                  className="cursor-pointer text-sm py-1.5 px-4 rounded-full transition-all shadow-sm hover:scale-105"
                  onClick={() => setActiveCategory(cat)}
                >
                  {getCategoryLabel(cat)}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Main Video Library Section */}
      <main className="flex-1 container mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              {activeCategory === "All" ? "Featured STEM Lessons" : `${getCategoryLabel(activeCategory)} Lessons`}
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              {videos.length} {videos.length === 1 ? 'lesson' : 'lessons'} available with AI transcripts & quizzes
            </p>
          </div>

          {(searchQuery || activeCategory !== "All") && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearchQuery("")
                setActiveCategory("All")
              }}
              className="text-xs"
            >
              Reset Filters
            </Button>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-72 rounded-xl bg-muted/40 animate-pulse border" />
            ))}
          </div>
        ) : videos.length === 0 ? (
          <div className="text-center py-20 bg-card rounded-2xl border">
            <Video className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium text-foreground">No videos found</p>
            <p className="text-sm text-muted-foreground mt-1">Try adjusting your search terms or category filter</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchQuery("")
                setActiveCategory("All")
              }}
              className="mt-4"
            >
              View All Videos
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {videos.map((video) => (
              <Card
                key={video.id}
                className="group overflow-hidden rounded-2xl border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-xl flex flex-col bg-card"
              >
                {/* Cover Image / Thumbnail */}
                <div className="relative aspect-[16/10] overflow-hidden bg-muted">
                  {video.coverImage || video.cover_image ? (
                    <img
                      src={video.coverImage || video.cover_image}
                      alt={video.title}
                      className="object-cover w-full h-full transition-transform duration-500 group-hover:scale-105"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-secondary/20">
                      <Video className="h-8 w-8 text-primary" />
                    </div>
                  )}

                  {/* Play Overlay */}
                  <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[2px]">
                    <div className="p-3 rounded-full bg-primary text-primary-foreground shadow-lg transform scale-75 group-hover:scale-100 transition-transform">
                      <Play className="h-5 w-5 fill-current" />
                    </div>
                  </div>

                  {/* Badges */}
                  <div className="absolute top-2.5 left-2.5">
                    <Badge className="bg-background/90 text-foreground backdrop-blur-md shadow-sm text-xs font-semibold hover:bg-background">
                      {getCategoryLabel(video.category)}
                    </Badge>
                  </div>
                  {video.duration_seconds && (
                    <div className="absolute bottom-2.5 right-2.5 px-2 py-0.5 rounded bg-black/80 text-white text-[11px] font-mono font-medium">
                      {formatDuration(video.duration_seconds)}
                    </div>
                  )}
                </div>

                <CardHeader className="flex-grow p-4 pb-2">
                  <CardTitle className="line-clamp-2 text-lg font-bold group-hover:text-primary transition-colors leading-snug">
                    {getVideoTitle(video.title)}
                  </CardTitle>
                  {video.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1.5 leading-relaxed">
                      {video.description}
                    </p>
                  )}
                </CardHeader>

                <CardFooter className="p-4 pt-2">
                  <Button asChild className="w-full h-10 rounded-xl group-hover:bg-primary group-hover:text-primary-foreground transition-all">
                    <Link href={`/library/${video.id}`}>
                      <span>Watch & Learn</span>
                      <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </Link>
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {/* Feature Highlights Grid */}
        <section className="mt-20 pt-12 border-t">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h3 className="text-2xl font-bold tracking-tight text-foreground">
              Designed for Accessible Open-Source Education
            </h3>
            <p className="text-muted-foreground text-sm mt-2">
              Everything in GandaLab is engineered for frictionless self-paced mastery with AI tutors and synchronized transcripts.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl border bg-card/50 flex flex-col items-start">
              <div className="p-3 rounded-xl bg-blue-500/10 text-blue-600 mb-4">
                <BookOpen className="h-6 w-6" />
              </div>
              <h4 className="font-semibold text-base mb-2">Live Synchronized Captions</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Word-by-word timestamped subtitles let students click any phrase to instantly jump to that exact second in the video.
              </p>
            </div>

            <div className="p-6 rounded-2xl border bg-card/50 flex flex-col items-start">
              <div className="p-3 rounded-xl bg-purple-500/10 text-purple-600 mb-4">
                <Sparkles className="h-6 w-6" />
              </div>
              <h4 className="font-semibold text-base mb-2">Coumba AI Learning Assistant</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Ask Coumba any question about the video and get intuitive analogies, timestamp citations, and personalized guidance.
              </p>
            </div>

            <div className="p-6 rounded-2xl border bg-card/50 flex flex-col items-start">
              <div className="p-3 rounded-xl bg-green-500/10 text-green-600 mb-4">
                <Database className="h-6 w-6" />
              </div>
              <h4 className="font-semibold text-base mb-2">PostgreSQL & PGVector Ready</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                All video transcripts, quizzes, and multilingual data are stored in a clean PostgreSQL database ready for vector semantic search.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <SiteFooter />
    </div>
  )
}
