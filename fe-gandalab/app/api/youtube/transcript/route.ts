import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
    try {
        const formData = await request.formData();
        const youtubeUrl = formData.get('youtube_url');

        if (!youtubeUrl) {
            return NextResponse.json(
                { error: 'YouTube URL is required' },
                { status: 400 }
            );
        }

        const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
        const backendFormData = new FormData();
        backendFormData.append('youtube_url', youtubeUrl as string);

        const response = await fetch(`${backendUrl}/youtube/youtube-transcript`, {
            method: 'POST',
            body: backendFormData,
        });

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(error, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Transcript API error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
