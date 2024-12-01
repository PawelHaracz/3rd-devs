import { v4 as uuidv4 } from "uuid";
import { Neo4jService } from "./Neo4jService";
import { OpenAIService } from "./OpenAIService";
import type { UserConnection } from "./types";

export const LABEL = "UserConnections1";

export const initialize = async (neo4jService: Neo4jService, openAIService: OpenAIService) => {
  const existingRecords = await neo4jService.executeQuery(`
    MATCH (d:${LABEL})
    RETURN count(d) AS count
  `);

  if (existingRecords.records[0].get("count").toNumber() > 0) {
    console.log("Records already exist. Skipping initialization.");
    return;
  }

  const fs = require('fs');
  const data = fs.readFileSync('15_task/data/query_result.json', 'utf8');
  const userConnections: UserConnection[] = JSON.parse(data);
  console.log(userConnections.length);
  const groupedConnections = userConnections.reduce((acc, connection) => {
    if (!acc.some(item => item.id === connection.user1_id)) {
      acc.push({ id: connection.user1_id, username: connection.username });
    }
    return acc;
  }, [] as { id: string, username: string }[]);
  console.log(Object.keys(groupedConnections) .length);

  for (const user of groupedConnections) {
    const newUc = await neo4jService.addNode(LABEL, {
      id: Number(user.id),
      name: user.username
    });
    console.log(`Added document: ${newUc.properties.name}`);
  }

  for (const uc of userConnections) {
    const user2Name = userConnections.find(uc1 => uc1.user1_id === uc.user2_id)?.username
    if (!user2Name) {
      console.log(`User not found: ${uc.user2_id}`);
      continue;
    }
    const user1 = await neo4jService.findNodeByProperty(LABEL, "name", uc.username);
    const user2 = await neo4jService.findNodeByProperty(LABEL, "name", user2Name);
    if (user1 && user2) {
      await neo4jService.connectNodes(user1.id, user2.id, "HAS_RELATIONSHIP");
      console.log(`Connected ${uc.user1_id} to ${uc.user2_id}`);
    }
    else {
      console.log(`User not found: ${uc.username} or ${user2Name}`);
    }
  }

  console.log("Initialization completed.");
};