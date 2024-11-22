import { OpenAIService } from "./OpenAIService";
import { TextSplitter } from "./TextService";
import { VectorService } from './VectorService';
import type { ChatCompletion } from "openai/resources/chat/completions";


const query = 'When a prototype weapon was stolen?';

const COLLECTION_NAME = "aidevs";

const openai = new OpenAIService();
const vectorService = new VectorService(openai);
const textSplitter = new TextSplitter();
import fs from 'fs/promises';

async function initializeData() {
    const dataDir = await fs.readdir('./12_task/do-not-share');
    const files = await Promise.all(dataDir.map(async (file) => {
        const text = await fs.readFile(`./12_task/do-not-share/${file}`, 'utf8');
        return {
            fileName: file,
            content: text
        }
    }));

    const points = await Promise.all(files.map(async ({ fileName, content }: { fileName: string, content: string }) => {
        const [year, month, day] = fileName.split('.')[0].split('_');
        const date = `${year}-${month}-${day}`;

        const determineStealingWeapon = await openai.completion({
            messages: [
                { role: 'system', content: `You are a helpful assistant that you determine that receive text is about stealing a weapon. 
                                           If it is, respond with "1", otherwise respond with "0".` },
                { role: 'user', content: content }
            ], model: 'gpt-4o-mini'
        }) as ChatCompletion;

        const isStealingWeapon = determineStealingWeapon.choices[0].message.content === '1';
        const doc = await textSplitter.document(content, 'gpt-4o-mini', { fileName: fileName, date: date, isStealingWeapon: isStealingWeapon });
        return doc;
    }));

    await vectorService.initializeCollectionWithData(COLLECTION_NAME, points);
}

async function main() {
    await initializeData();

    const filter = {
        should: {
          key: "isStealingWeapon",
          match: {
            value: true
          }
        }
      };

    const searchResults = await vectorService.performSearch(COLLECTION_NAME, query, filter, 15);

    console.table(searchResults.map((result, index) => ({
        'Author': result.payload?.author || '',
        'Text': typeof result.payload?.text === 'string' ? result.payload.text.slice(0, 45) + '...' : '',
        'Score': result.score
    })));


    const answer = await openai.completion({
        messages: [
            { role: 'system', content: 'You are a helpful assistant find the date based metadata from the search results. Where the text is answered for the query. You must only return the date from the metadata "date".' },
            { role: 'user', content: `
                <query> ${query} </query>
                <searchResults>
                    ${searchResults.map((result) => 
                        
                        `<searchResult>
                            <fileName>${result.payload?.fileName || ''}</fileName>
                            <text>${result.payload?.text || ''}</text>
                            <date>${result.payload?.date || ''}</date>
                        </searchResult>`
                ).join('')}
                </searchResults>
            ` }
        ]
    }) as ChatCompletion;
    console.log(`Query: ${query}`);
    console.log(`Date: ${answer.choices[0].message.content}`);
    console.table(searchResults.map((result, index) => ({
        'Author': result.payload?.author || '',
        'Text': typeof result.payload?.text === 'string' ? result.payload.text.slice(0, 45) + '...' : '',
        'Score': result.score
    })));
}

main().catch(console.error);