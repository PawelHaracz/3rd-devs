import type { ChatCompletion } from "openai/resources/chat/completions";
import { v4 as uuidv4 } from "uuid";
import { DatabaseService } from "./DatabaseService";
import { AlgoliaService } from "./AlgoliaService";
import { VectorService } from "./VectorService";
import { OpenAIService } from "./OpenAIService";
import { ApiDBRequest, ApiDBResponse } from "./schema";
const openAIService = new OpenAIService();
const algoliaService = new AlgoliaService(
  process.env.ALGOLIA_APP_ID!,
  process.env.ALGOLIA_API_KEY!
);
const vectorService = new VectorService(openAIService);
const APIDB_ENDPOINT = "https://centrala.ag3nts.org/apidb";
const API_KEY = process.env.DEV_AI_KEY!;
console.log(API_KEY);
// const dbService = new DatabaseService(
//   "hybrid/database.db",
//   algoliaService,
//   vectorService
// );

function getPropertyValue<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}


async function getQuery(query: string): Promise<object[]>{
   const request = new ApiDBRequest(API_KEY, query);
  //  console.log(JSON.stringify(request))
   const response = await fetch(APIDB_ENDPOINT, {
    method: 'POST',
    body: JSON.stringify(request)
   });
   const data = await response.json() as ApiDBResponse;
  //  console.log(data);

   if(data.reply === null){
    throw new Error(data.error);
   }

   return data.reply;
}

async function generateRelationships(tables: object[]) {
  const completion = (await openAIService.completion({
    model: "gpt-4o-mini",
    jsonMode: true,
    messages: [
      {
        role: "user", 
        content: `
      generate relationships between tables and return in json format with keys: table1, table2, relationship.
      Table1 and Table2 are names of tables and relationship is a string describing the relationship between them.
      you got tables name and schema.

      <rules>      
      - return only json format.
      - Json should be valid.
      - return only array of objects.
      - relationship should be a string describing the relationship between them.
      - expected json format: [{"table1": "table1", "table2": "table2", "relationship": "relationship"}, {"table1": "table1", "table2": "table2", "relationship": "relationship"}]
      </rules>

      <tables>
      ${tables.map((table) => `<table> ${ getPropertyValue<any, string>(table, "tableName")}\n</table><schema>: ${ getPropertyValue<any, string>(table,"schema")}</schema>:`).join("\n")}
      </tables>
      `
    }]
  })) as ChatCompletion;

  console.log(completion.choices[0].message.content);
  const json =  JSON.parse(completion.choices[0].message.content!);


  return json.relationships as object[];
}

async function answerQuery(question: string, tables: object[], relationships: object[]){
  const completion = (await openAIService.completion({
    model: "gpt-4o-mini",
    jsonMode: true,
    messages: [
      {
        role: "user", 
        content: `
      answer the question based on the tables and relationships. you MUST generate sql query to answer the question.

      <rules>     
      - json structure MUST HAVE keys: "explanation" and "query".
      - explanation should be a string describing the query.
      - explanation should be VERY FIRST property of the object.
      - return only json format.
      - Json should be valid.
      - return only array of objects.
      - objects should have keys: query, explanation.
      - explanation should be a string describing the query.
      - explanation should be VERY FIRST property of the object.
      - query should be valid. 
      - query should be SELECT query.
      - you can use joins.
      - select only what is asked in the question.
      - question may be complex, you can use joins.
      - question cane be in Polish or English.
      - return only query, nothing else.
      - query must be fit the tables and relationships.
      </rules>

      <tables>
      ${tables.map((table) => `<table> ${ getPropertyValue<any, string>(table, "tableName")}\n</table><schema>: ${ getPropertyValue<any, string>(table,"schema")}</schema>:`).join("\n")}
      </tables>

      <relationships>
      ${relationships.map((relationship) => `<table1> ${ getPropertyValue<any, string>(relationship, "table1")}\n</table1><table2>: ${ getPropertyValue<any, string>(relationship,"table2")}</table2><relationship>: ${ getPropertyValue<any, string>(relationship,"relationship")}</relationship>:`).join("\n")}
      </relationships>

      <question>
      ${question}
      </question>
      `
    }]
  })) as ChatCompletion;

  const query = completion.choices[0].message.content;
  console.log(query);
  const json = JSON.parse(query!);
  return json.query;
}

async function main(){
  const queryTables = await getQuery("show tables");
  // console.log(query);
  const tabels = await Promise.all(queryTables.map(async (i) => {
    const createTable = await getQuery(`show create table ${getPropertyValue<any, string>(i, "Tables_in_banan")}`);
    // console.log(createTable);

    return {
      tableName: getPropertyValue<any, string>(createTable[0], "Table"),
      schema: getPropertyValue<any, string>(createTable[0], "Create Table") 
    };
  }));
    
  const relationships = await generateRelationships(tabels) as object[];



  const query = await answerQuery("Zwróć mi liste ID datacenter które są zarządzane przez użytkowników którzy są na urlopie", tabels, relationships);
  var dc = await getQuery(query!);

  const dcIds = dc.map((item) => getPropertyValue<any, string>(item, "dc_id"));
  console.log(dcIds);
}

main().catch(console.error);

