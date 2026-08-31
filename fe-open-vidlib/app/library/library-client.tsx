"use client"

import { useState } from "react"
import { Search, Video, ArrowRight } from "lucide-react"
import Link from "next/link"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SiteHeader } from "@/components/site-header"
import { SiteFooter } from "@/components/site-footer"
import { useLanguage } from "@/lib/i18n/language-context"

import { Resource, ResourceType } from "@/lib/resources"

interface LibraryClientProps {
    initialResources: Resource[]
}

export function LibraryClient({ initialResources }: LibraryClientProps) {
    const { t } = useLanguage()
    const [searchQuery, setSearchQuery] = useState("")
    const [activeCategory, setActiveCategory] = useState<string>("All")

    const categories = ["All", "Science", "Technology", "Engineering", "Mathematics"]

    const getCategoryLabel = (category: string) => {
        switch (category) {
            case "All": return t.library.types.all
            case "Science": return t.library.categories.science
            case "Technology": return t.library.categories.technology
            case "Engineering": return t.library.categories.engineering
            case "Mathematics": return t.library.categories.math
            case "History": return t.library.categories.history
            default: return category
        }
    }

    const getVideoTitle = (originalTitle: string) => {
        // Map French titles to translation keys
        const titleMap: Record<string, string> = {
            "La Gravité Expliquée aux Enfants": t.library.videoTitles.gravity,
            "Les chiffres affolants de la pyramide de Khéops": t.library.videoTitles.pyramid,
            "À quoi sert le théorème de Pythagore ?": t.library.videoTitles.pythagoras,
        }
        return titleMap[originalTitle] || originalTitle
    }

    const filteredResources = initialResources.filter((resource) => {
        // Search filter: check title and category
        const matchesSearch = searchQuery.trim() === "" ||
            resource.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (resource.category && resource.category.toLowerCase().includes(searchQuery.toLowerCase()))

        // Category filter: check if category matches (case-insensitive for safety)
        const matchesCategory = activeCategory === "All" ||
            (resource.category && resource.category === activeCategory)

        return matchesSearch && matchesCategory
    })

    return (
        <div className="min-h-screen bg-background flex flex-col">
            <SiteHeader />

            <main className="flex-1 container mx-auto py-12 px-4 md:px-6">
                <div className="flex flex-col items-center text-center mb-12 space-y-4">
                    <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
                        {t.library.title}
                    </h1>
                    <p className="text-lg text-muted-foreground max-w-2xl">
                        {t.library.subtitle}
                    </p>
                </div>

                <div className="flex flex-col gap-6 mb-10">
                    <div className="flex flex-col md:flex-row gap-6 items-center justify-between">
                        <div className="relative w-full md:w-96">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder={t.library.searchPlaceholder}
                                className="pl-10 h-12 text-lg"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-2 justify-center md:justify-start">
                        <span className="text-sm font-medium text-muted-foreground mr-2 self-center">{t.library.filterSubject}:</span>
                        {categories.map((category) => (
                            <Badge
                                key={category}
                                variant={activeCategory === category ? "default" : "outline"}
                                className="cursor-pointer text-sm py-1 px-3 hover:bg-primary/90 hover:text-primary-foreground transition-colors"
                                onClick={() => setActiveCategory(category)}
                            >
                                {getCategoryLabel(category)}
                            </Badge>
                        ))}
                    </div>

                    {/* Active filters indicator */}
                    {(searchQuery || activeCategory !== "All") && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>{t.library.showingResults} {filteredResources.length} {t.library.of} {initialResources.length} {t.library.resources}</span>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                    setSearchQuery("");
                                    setActiveCategory("All");
                                }}
                                className="h-7 text-xs"
                            >
                                {t.library.clearFilters}
                            </Button>
                        </div>
                    )}
                </div>

                {filteredResources.length === 0 ? (
                    <div className="text-center py-20">
                        <p className="text-xl text-muted-foreground">{t.library.noResults}</p>
                        <Button variant="link" onClick={() => {
                            setSearchQuery("");
                            setActiveCategory("All");
                        }} className="mt-4 text-lg">
                            {t.common.cancel}
                        </Button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {filteredResources.map((resource) => (
                            <Card key={resource.id} className="group overflow-hidden border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-lg flex flex-col">
                                <div className="relative aspect-[4/3] overflow-hidden bg-muted">
                                    {resource.coverImage ? (
                                        <img
                                            src={resource.coverImage}
                                            alt={resource.title}
                                            className="object-cover w-full h-full transition-transform duration-500 group-hover:scale-105"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center bg-secondary/20">
                                            <Video className="h-8 w-8 text-red-500" />
                                        </div>
                                    )}
                                    <div className="absolute top-2 right-2">
                                        <div className="p-2 rounded-full bg-background/90 backdrop-blur-md shadow-sm text-red-500">
                                            <Video className="h-4 w-4" />
                                        </div>
                                    </div>
                                </div>

                                <CardHeader className="flex-grow">
                                    {resource.category && (
                                        <div className="text-sm text-muted-foreground mb-1 font-medium">
                                            {getCategoryLabel(resource.category)}
                                        </div>
                                    )}
                                    <CardTitle className="line-clamp-2 text-xl group-hover:text-primary transition-colors">
                                        {getVideoTitle(resource.title)}
                                    </CardTitle>
                                </CardHeader>

                                <CardFooter className="pt-0">
                                    <Button asChild className="w-full text-lg h-12 group-hover:bg-primary group-hover:text-primary-foreground transition-all">
                                        <Link href={`/library/${resource.id}`}>
                                            {t.library.explore}
                                            <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                                        </Link>
                                    </Button>
                                </CardFooter>
                            </Card>
                        ))}
                    </div>
                )}
            </main>

            <SiteFooter />
        </div>
    )
}
