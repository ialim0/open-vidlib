"use server"

export interface ChatResponse {
    answer: string
    isRelevant: boolean
}

export async function chatWithVideoAction(
    transcript: string,
    question: string
): Promise<ChatResponse> {
    const apiKey = process.env.Claude_API_KEY

    console.log("Chat Action - API Key exists:", !!apiKey)
    if (apiKey) {
        console.log("Chat Action - API Key start:", apiKey.substring(0, 10) + "...")
    }

    if (!apiKey) {
        return {
            answer: "I apologize, but I'm unable to process your question at the moment. The AI service is not configured.",
            isRelevant: true
        }
    }

    try {
        const prompt = `You are an intelligent video assistant. A user is watching a video and has asked a question.

VIDEO TRANSCRIPT:
${transcript ? transcript.slice(0, 20000) : "No transcript available."}

USER QUESTION:
${question}

INSTRUCTIONS:
1. First, determine if the question is RELEVANT to the video content.
2. If RELEVANT:
   - Provide a clear, helpful answer based on the transcript
   - Include specific timestamp references in the format [MM:SS] where the information appears
   - Example: "According to the video [02:15], the main concept is..."
3. If NOT RELEVANT (question is completely unrelated to the video):
   - Politely indicate the question is out of context
   - Suggest that the user might need external sources
   - Example: "This question appears to be outside the scope of this video content. You might want to search external resources for information about [topic]."

Return your response as a JSON object with:
- "answer": string (your response with [MM:SS] timestamps if relevant)
- "isRelevant": boolean (true if question relates to video, false if out of context)

Do not include any other text, just the JSON.`

        const response = await fetch("https://api.anthropic.com/v1/messages", {
            method: "POST",
            headers: {
                "x-api-key": apiKey,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            body: JSON.stringify({
                model: "claude-3-5-sonnet-20241022",
                max_tokens: 1024,
                messages: [{ role: "user", content: prompt }],
            }),
        })

        if (!response.ok) {
            console.error("Anthropic API Error:", await response.text())
            return {
                answer: "I apologize, but I encountered an error processing your question. Please try again.",
                isRelevant: true
            }
        }

        const data = await response.json()
        const content = data.content[0].text

        // Extract JSON from content
        const jsonMatch = content.match(/\{[\s\S]*\}/)
        if (!jsonMatch) {
            return {
                answer: "I apologize, but I couldn't process your question properly. Please try rephrasing it.",
                isRelevant: true
            }
        }

        const parsed = JSON.parse(jsonMatch[0])
        return {
            answer: parsed.answer || "I couldn't find an answer to your question.",
            isRelevant: parsed.isRelevant !== false
        }

    } catch (error) {
        console.error("Error in chat:", error)
        return {
            answer: "I apologize, but I encountered an error. Please try again.",
            isRelevant: true
        }
    }
}
