"use server"

export interface AnswerResponse {
    answer: string
    isOutOfContext: boolean
    timestamps?: string[] // Array of timestamps like ["[02:15]", "[03:30]"]
}

export async function answerQuestionAction(
    question: string,
    transcript: string
): Promise<AnswerResponse> {
    const apiKey = process.env.ANTHROPIC_API_KEY

    if (!apiKey) {
        return {
            answer: "I'm currently unable to answer questions. Please check the API configuration.",
            isOutOfContext: false
        }
    }

    try {
        const prompt = `You are an intelligent educational assistant helping users understand video content.

Given the following video transcript and a user's question, provide a helpful answer.

IMPORTANT INSTRUCTIONS:
1. If the question is RELEVANT to the transcript content, answer it and include specific timestamps from the transcript where the answer can be found.
2. If the question is OUT OF CONTEXT (not related to the video content), clearly state that and suggest looking at external sources.
3. Format timestamps as [MM:SS] in your response where relevant.
4. Be concise and helpful.

VIDEO TRANSCRIPT:
${transcript ? transcript.slice(0, 15000) : "No transcript available"}

USER QUESTION:
${question}

Respond in JSON format with:
{
    "answer": "Your detailed answer here with timestamps like [02:15] where relevant",
    "isOutOfContext": false or true
}

If out of context, set isOutOfContext to true and suggest external resources.`

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
                answer: "I encountered an error processing your question. Please try again.",
                isOutOfContext: false
            }
        }

        const data = await response.json()
        const content = data.content[0].text

        // Extract JSON from content
        const jsonMatch = content.match(/\{[\s\S]*\}/)
        if (!jsonMatch) {
            return {
                answer: content,
                isOutOfContext: false
            }
        }

        const parsed = JSON.parse(jsonMatch[0])
        
        // Extract timestamps from the answer
        const timestampRegex = /\[(\d{1,2}:\d{2})\]/g
        const timestamps = parsed.answer.match(timestampRegex) || []

        return {
            answer: parsed.answer,
            isOutOfContext: parsed.isOutOfContext || false,
            timestamps
        }

    } catch (error) {
        console.error("Error answering question:", error)
        return {
            answer: "I encountered an error processing your question. Please try again.",
            isOutOfContext: false
        }
    }
}
