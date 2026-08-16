import { useState } from 'react';
import { getYoutubeTranscript, TranscriptResponse } from '@/lib/api/youtube';

export function useYoutubeTranscript() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [transcript, setTranscript] = useState<TranscriptResponse | null>(null);

    const fetchTranscript = async (youtubeUrl: string) => {
        setLoading(true);
        setError(null);

        try {
            const data = await getYoutubeTranscript(youtubeUrl);
            setTranscript(data);
            return data;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'An error occurred';
            setError(errorMessage);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const reset = () => {
        setTranscript(null);
        setError(null);
        setLoading(false);
    };

    return {
        transcript,
        loading,
        error,
        fetchTranscript,
        reset,
    };
}
