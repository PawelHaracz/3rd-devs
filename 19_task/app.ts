import type { Request, Response } from 'express';

import express from 'express';
import OpenAI from 'openai';
import { prompt } from './prompt';

const app = express();
const port = 3000;

app.use(express.json());

app.listen(port, () => {
    console.log(`App listening at http://localhost:${port}`);
  });

app.post('/webhook', async (req: Request, res: Response) => {
    const { instruction } = req.body || {};
    console.log(instruction);
    let result = {
    "description": ""
   };

    if (instruction !== "" || instruction !== null || instruction !== undefined) {
    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });

    const completion = await openai.chat.completions.create({
      messages: [
        { role: "system", content: prompt },
        { role: "user", content: instruction }
      ],
      model: "gpt-4o-mini",
      response_format: { type: "json_object" }
    });
    var content = completion.choices[0].message.content || "";
    console.log(content);
    result.description = JSON.parse(content).result;
   }

   res.json(result);
});

  