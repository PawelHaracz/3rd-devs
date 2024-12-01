import { initialize, LABEL } from "./init-neo4j";
import { Neo4jService } from "./Neo4jService";
import { OpenAIService } from "./OpenAIService";

if (
  !process.env.NEO4J_URI ||
  !process.env.NEO4J_USER ||
  !process.env.NEO4J_PASSWORD
) {
  throw new Error("NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set");
}

const openAIService = new OpenAIService();
const neo4jService = new Neo4jService(
  process.env.NEO4J_URI,
  process.env.NEO4J_USER,
  process.env.NEO4J_PASSWORD + "#",
  openAIService
);


const main = async () => {
  await neo4jService.createVectorIndex( "user_connections_index1", LABEL, "embedding", 3072 );
  await neo4jService.waitForIndexToBeOnline("user_connections_index1");
  await initialize(neo4jService, openAIService);
  

  const result1 = await neo4jService.findNodeByProperty(
    LABEL, 
    "name", 
    "Rafał" )

  const result2 = await neo4jService.findNodeByProperty(
    LABEL, 
    "name", 
    "Barbara" )
 
  const CypherQuery = `
    MATCH (startNode:UserConnections1 {id: ${result1?.properties.id} }), (endNode:UserConnections1 {id: ${result2?.properties.id}})
    MATCH p = shortestPath((startNode)-[:HAS_RELATIONSHIP*]-(endNode))
    RETURN [node IN nodes(p) | node.name] AS names
  `;

  const resultQuery = await neo4jService.executeQuery(CypherQuery);
  const resultNames = resultQuery.records[0].get("names");

  console.log(resultNames);
  console.log(`final result: ${resultNames.join(", ")}`);
} 

main().catch(console.error).finally(async () => {
  await neo4jService.close();
});

