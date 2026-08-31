'use client';

import { useState } from 'react';
import { useYoutubeTranscript } from '@/hooks/useYoutubeTranscript';

export default function YoutubeTranscriptViewer() {
    const [url, setUrl] = useState('');
    const { transcript, loading, error, fetchTranscript } = useYoutubeTranscript();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!url.trim()) return;

        try {
            await fetchTranscript(url);
        } catch (err) {
            // Error is already handled in the hook
            console.error('Failed to fetch transcript:', err);
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-6">
            <h1 className="text-2xl font-bold mb-6">YouTube Transcript Viewer</h1>

            <form onSubmit={handleSubmit} className="mb-8">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="Enter YouTube URL..."
                        className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={loading || !url.trim()}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Loading...' : 'Get Transcript'}
                    </button>
                </div>
            </form>

            {error && (
                <div className="p-4 mb-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    <p className="font-semibold">Error:</p>
                    <p>{error}</p>
                </div>
            )}

            {transcript && (
                <div className="space-y-6">
                    {/* Word-level transcript */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-semibold mb-4">Word-Level Transcript</h2>
                        <div className="flex flex-wrap gap-2">
                            {transcript.words.map((word, idx) => (
                                <span
                                    key={idx}
                                    className="px-2 py-1 bg-gray-100 rounded hover:bg-blue-100 cursor-pointer transition-colors"
                                    title={`${word.start.toFixed(2)}s - ${word.end.toFixed(2)}s`}
                                >
                                    {word.word}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Segment-level transcript */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-semibold mb-4">Segments</h2>
                        <div className="space-y-3">
                            {transcript.segments.map((segment) => (
                                <div
                                    key={segment.id}
                                    className="p-3 bg-gray-50 rounded border-l-4 border-blue-500"
                                >
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-sm text-gray-600">
                                            {segment.start.toFixed(2)}s - {segment.end.toFixed(2)}s
                                        </span>
                                        <span className="text-xs text-gray-500">
                                            Confidence: {(1 - segment.no_speech_prob).toFixed(2)}
                                        </span>
                                    </div>
                                    <p className="text-gray-800">{segment.text}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
