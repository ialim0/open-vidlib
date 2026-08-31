import type React from "react"
import type { Metadata } from "next"
import "./globals.css"
import { LanguageProvider } from "@/lib/i18n/language-context"

export const metadata: Metadata = {
  title: "Open VidLib - Interactive Learning Platform",
  description: "Democratizing learning through AI-powered educational tools",
  icons: {
    icon: "/open-vidlib-logo.png",
    apple: "/open-vidlib-logo.png",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-sans antialiased`}>
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  )
}
