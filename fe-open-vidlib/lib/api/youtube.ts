export interface TranscriptWord {
    word: string;
    start: number;
    end: number;
}

export interface TranscriptSegment {
    id: number;
    seek: number;
    start: number;
    end: number;
    text: string;
    tokens: number[];
    temperature: number;
    avg_logprob: number;
    compression_ratio: number;
    no_speech_prob: number;
}

export interface TranscriptResponse {
    words: TranscriptWord[];
    segments: TranscriptSegment[];
    full_response: any;
}

export async function getYoutubeTranscript(youtubeUrl: string): Promise<TranscriptResponse> {
    const formData = new FormData();
    formData.append('youtube_url', youtubeUrl);

    const response = await fetch('/api/youtube/transcript', {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Failed to fetch transcript' }));
        throw new Error(error.error || error.detail || 'Failed to fetch transcript');
    }

    return response.json();
}
