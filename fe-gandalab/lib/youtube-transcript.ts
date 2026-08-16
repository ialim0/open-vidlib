// Utility to fetch YouTube transcripts from the backend API
export async function fetchYoutubeTranscript(youtubeUrl: string): Promise<string | null> {
    try {
        const apiUrl = 'http://0.0.0.0:8000/youtube/youtube-transcript'

        const formData = new URLSearchParams()
        formData.append('youtube_url', youtubeUrl)

        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        })

        if (!response.ok) {
            console.error(`Failed to fetch transcript for ${youtubeUrl}: ${response.statusText}`)
            return null
        }

        const data = await response.json()

        // The API response structure may vary, adjust based on actual response
        // Common patterns: data.transcript, data.text, or data itself
        return data.transcript || data.text || JSON.stringify(data)
    } catch (error) {
        console.error(`Error fetching transcript for ${youtubeUrl}:`, error)
        return null
    }
}
