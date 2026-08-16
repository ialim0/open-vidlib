"use client"

import Link from "next/link"
import { useLanguage } from "@/lib/i18n/language-context"

export function SiteFooter() {
    const { t } = useLanguage()

    return (
        <footer className="border-t bg-card">
            <div className="container mx-auto px-4 py-8">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                    <p className="text-sm text-muted-foreground">
                        © 2025 {t.home.title}. {t.home.footerRights}
                    </p>
                    <div className="flex items-center gap-4">
                        <Link href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                            {t.home.privacy}
                        </Link>
                        <Link href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                            {t.home.terms}
                        </Link>
                        <Link href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                            {t.home.contact}
                        </Link>
                    </div>
                </div>
            </div>
        </footer>
    )
}
