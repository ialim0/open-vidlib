import Link from "next/link"
import { ArrowLeft, Database, Globe, Search, Sparkles } from "lucide-react"

const technologies = [
  { icon: Database, name: "Next.js + TypeScript", description: "A fast, accessible frontend for browsing lessons and interacting with transcripts." },
  { icon: Database, name: "FastAPI + PostgreSQL", description: "A maintainable API and relational data layer for videos, transcripts, quizzes, and learning sessions." },
  { icon: Search, name: "pgvector + Mistral AI", description: "Semantic transcript search, grounded answers, translation, and multilingual voice generation." },
  { icon: Globe, name: "Open educational content", description: "A foundation for STEM learning in English, French, Wolof, Pulaar, Bambara, and more languages." },
]

const roadmap = [
  "Community video submissions and moderation",
  "Self-hosted Whisper transcription for any YouTube lesson",
  "Learner accounts, saved notes, and progress tracking",
  "More West African languages and voice presets",
  "Contributor-friendly APIs, tests, and deployment guides",
]

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto max-w-5xl px-4 py-12 md:py-20">
        <Link href="/" className="mb-10 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back to the library
        </Link>

        <section className="max-w-3xl">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-primary">
            <Sparkles className="h-3.5 w-3.5" /> Open VidLib
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight md:text-6xl">About the project</h1>
          <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
            Open VidLib is an open-source educational video platform created to make STEM lessons easier to understand, search, and discuss. It was born at the AIMS Scientific Innovation Hackathon in Senegal, where the project won first prize in the EdTech category.
          </p>
          <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
            Learners can watch curated lessons, jump through word-level transcripts, search for concepts, ask Coumba questions grounded in a video, and practice with multilingual flashcards.
          </p>
        </section>

        <section className="mt-16 rounded-3xl border border-primary/20 bg-primary/5 p-8 md:p-10">
          <h2 className="text-3xl font-bold">Why this matters</h2>
          <p className="mt-4 max-w-3xl leading-relaxed text-muted-foreground">
            Imagine watching any educational video in the language that helps you learn best. Open VidLib is moving toward real-time language switching, translated voice playback, and captions that stay synchronized with the lesson. Instead of scrubbing through a long video, learners will be able to search any concept, jump directly to the relevant moment, and ask questions grounded in what was said.
          </p>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {[
              ["Learn in your language", "Switch between English, French, and future community-supported languages without losing the lesson context."],
              ["Search every moment", "Find a formula, explanation, or example inside the video and play it immediately."],
              ["Share knowledge", "Help expand the library by contributing videos, transcripts, translations, and improvements."],
            ].map(([title, description]) => (
              <article key={title} className="rounded-2xl border bg-card p-5">
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-16">
          <div className="mb-8 flex items-center gap-3">
            <Database className="h-6 w-6 text-primary" />
            <h2 className="text-3xl font-bold">Technology</h2>
          </div>
          <div className="grid gap-5 md:grid-cols-2">
            {technologies.map(({ icon: Icon, name, description }) => (
              <article key={name} className="rounded-2xl border bg-card p-6">
                <Icon className="mb-4 h-6 w-6 text-primary" />
                <h3 className="font-semibold">{name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-16 rounded-3xl border bg-card p-8 md:p-10">
          <div className="flex items-center gap-3">
            <Globe className="h-6 w-6 text-primary" />
            <h2 className="text-3xl font-bold">Open-source roadmap</h2>
          </div>
          <p className="mt-4 max-w-2xl leading-relaxed text-muted-foreground">
            The roadmap is community-shaped. Every feature below is an opportunity for contributors to improve access to high-quality learning resources.
          </p>
          <ul className="mt-6 grid gap-3 md:grid-cols-2">
            {roadmap.map((item) => (
              <li key={item} className="flex gap-3 text-sm leading-relaxed">
                <Globe className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-16 flex flex-col gap-4 rounded-2xl border border-primary/20 bg-primary/5 p-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="font-bold">Help build the next version</h2>
            <p className="mt-1 text-sm text-muted-foreground">Open an issue, propose a feature, or contribute code to Open VidLib.</p>
          </div>
          <a href="https://github.com/ialim0/open-vidlib" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90">
            <Globe className="h-4 w-4" /> View on GitHub
          </a>
        </section>
      </div>
    </main>
  )
}
