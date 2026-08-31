"use server"

import { Flashcard } from "@/components/flashcard-quiz"

export async function generateQuizAction(transcript: string): Promise<Flashcard[]> {
    const apiKey = process.env.ANTHROPIC_API_KEY

    // Mock data for fallback or if no key
    const mockData: Flashcard[] = [
        {
            question: "If a right-angled triangle were a ladder leaning against a wall, what would the hypotenuse represent?",
            options: [
                "The wall",
                "The ladder itself",
                "The ground distance"
            ],
            correctOption: 1,
            source: "[00:45] - 'Imagine a ladder leaning against a wall...'"
        },
        {
            question: "Think of the Pythagorean theorem like a shortcut across a park. Why is the diagonal path shorter than walking along the edges?",
            options: [
                "Because it's a straight line between two points",
                "Because parks are designed that way",
                "Because you walk faster diagonally"
            ],
            correctOption: 0,
            source: "[01:20] - 'The diagonal path is always shorter...'"
        },
        {
            question: "If the sides of a triangle were squares of chocolate, how does the big square relate to the two smaller ones?",
            options: [
                "The big square is always larger",
                "The big square equals the sum of the two smaller squares",
                "The big square is unrelated to the smaller ones"
            ],
            correctOption: 1,
            source: "[02:15] - 'The area of the square on the hypotenuse...'"
        },
        {
            question: "Imagine a rope with 12 knots tied at equal intervals. How can this be used to build a perfect corner?",
            options: [
                "By forming a triangle with sides 3, 4, and 5 knots",
                "By tying it to a wall",
                "By measuring right angles with a protractor"
            ],
            correctOption: 0,
            source: "[03:10] - 'Ancient builders used a rope with knots...'"
        },
        {
            question: "If a right triangle is a slice of cheese, what is the 'crust' opposite the sharpest corner?",
            options: [
                "The shortest side",
                "Any side of the triangle",
                "The hypotenuse"
            ],
            correctOption: 2,
            source: "[00:30] - 'The side opposite the right angle is the hypotenuse'"
        }
    ]

    if (!apiKey) {
        console.warn("No Anthropic API key found. Using mock data.")
        return mockData
    }

    try {
        const prompt = `You are an expert educational AI. Create a dynamic multiple-choice flashcard quiz based on the following transcript.
        Generate exactly 5 flashcards.
        
        CRITICAL INSTRUCTION: Create questions based on ANALOGIES to explain concepts. 
        For example: "If an atom were a solar system, what would the nucleus be?"
        
        Each flashcard must have:
        1. A creative question based on an analogy or real-world comparison.
        2. THREE answer options (multiple choice).
        3. The index (0, 1, or 2) of the correct option.
        4. A source citation that MUST include a specific timestamp from the transcript (e.g., "[02:15] - 'quote from text'").
        
        Return the result as a JSON object with a "flashcards" array containing objects with:
        - "question": string
        - "options": array of 3 strings
        - "correctOption": number (0, 1, or 2)
        - "source": string (with timestamp)
        
        Do not include any other text, just the JSON.
        
        Transcript:
        ${transcript ? transcript.slice(0, 15000) : "No transcript provided."}
        `

        const response = await fetch("https://api.anthropic.com/v1/messages", {
            method: "POST",
            headers: {
                "x-api-key": apiKey,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            body: JSON.stringify({
                model: "claude-3-5-sonnet-20241022",
                max_tokens: 2048,
                messages: [{ role: "user", content: prompt }],
            }),
        })

        if (!response.ok) {
            console.error("Anthropic API Error:", await response.text())
            return mockData
        }

        const data = await response.json()
        const content = data.content[0].text

        // Extract JSON from content (in case there's extra text)
        const jsonMatch = content.match(/\{[\s\S]*\}/)
        if (!jsonMatch) return mockData

        const parsed = JSON.parse(jsonMatch[0])
        return parsed.flashcards || mockData

    } catch (error) {
        console.error("Error generating quiz:", error)
        return mockData
    }
}
