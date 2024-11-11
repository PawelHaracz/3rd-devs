import OpenAI from 'openai';
import dotenv from 'dotenv';

dotenv.config();

export class OpenAIService {
    private openai: OpenAI;

    constructor() {
        this.openai = new OpenAI({
            apiKey: process.env.OPENAI_API_KEY
        });
    }

    async getCompletion({ messages }: { messages: { role: string; content: string }[] }): Promise<string> {
        try {
            const completion = await this.openai.chat.completions.create({
                model: 'gpt-3.5-turbo',
                messages: messages as any[],
                temperature: 0,
                max_tokens: 10
            });

            return completion.choices[0].message.content || '';
        } catch (error) {
            console.error('Error getting completion:', error);
            throw error;
        }
    }
}
