"use client"

import Link from "next/link"
import Image from "next/image"
import { useLanguage } from "@/lib/i18n/language-context"
import { LanguageSwitcher } from "@/components/language-switcher"

export function SiteHeader() {
    const { t } = useLanguage()

    return (
        <header className="border-b bg-card">
            <div className="container mx-auto px-4 py-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Link href="/" className="flex items-center gap-3">
                            <Image
                                src="/gandalab-logo.png"
                                alt="GandaLab Logo"
                                width={40}
                                height={40}
                                className="rounded-lg"
                            />
                            <h1 className="text-2xl font-bold text-balance">{t.home.title}</h1>
                        </Link>
                    </div>
                    <nav className="flex items-center gap-4">
                        <LanguageSwitcher />
                        <div className="hidden md:flex items-center gap-6">
                            <Link
                                href="/#features"
                                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                            >
                                {t.common.features}
                            </Link>
                            <Link
                                href="/about"
                                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                            >
                                {t.common.about}
                            </Link>
                        </div>
                    </nav>
                </div>
            </div>
        </header>
    )
}
