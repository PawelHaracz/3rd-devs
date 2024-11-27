import { OpenAIService } from "./OpenAIService";
import type { ChatCompletion } from "openai/resources/chat/completions";
import type { PlaceRelation, PersonRelation, Relation } from './types';
import _ from "lodash";

const API_KEY = process.env.DEV_AI_KEY!;
const API_ENDPOINT = "https://centrala.ag3nts.org/";
const openAIService = new OpenAIService();
const RESTRICTED = "[**RESTRICTED DATA**]";
const LookingFor = "Barbara";
async function main() {

    const note = await fetchNote();
    let [persons, places] = await Promise.all([ RecognizePerson(note), RecognizePlaces(note)]);
    let [personsRelations, placesRelations] = [[], []]

    // console.log(personsRelations);
    // console.log(placesRelations);

    let generation = 0;
    let found = false
    let relations: Relation[] = [];
    const alreadyVisitedPersons: string[] = [];
    const alreadyVisitedPlaces: string[] = [];
    while(!found) {

        generation++;
        let [personsRelations, placesRelations] = await Promise.all([BuildPersonsRelations(persons), BuildPlacesRelations(places)]);
        let relationsGeneration = inlineRelations(personsRelations, placesRelations, generation);
        
        console.log(relationsGeneration);
        if (relationsGeneration.length === 0) {
            break;
        }

        relations.push(...relationsGeneration);
        alreadyVisitedPersons.push(...persons.filter(p => !alreadyVisitedPersons.includes(p)));
        alreadyVisitedPlaces.push(...places.filter(p => !alreadyVisitedPlaces.includes(p)));
        persons = relationsGeneration.filter(r => r.generation > generation-1).filter(r => !alreadyVisitedPersons.includes(r.person) ).map(r => r.person);
        places = relationsGeneration.filter(r => r.generation > generation-1).filter(r => !alreadyVisitedPlaces.includes(r.place)).map(r => r.place);

        if (persons.length === 0 && places.length === 0) {
            break;
        }
    }
    console.dir(relations, {depth: 3});
    
    let cities = await FindPeson(LookingFor, relations);
    console.log(cities);

}

async function FindPeson(person: string, relations: Relation[]): Promise<string> {
    const completion = (await openAIService.completion({
        model: "gpt-4o",
        jsonMode: true,
        messages: [
          {
            role: "system", 
            content: `
            you are a person finder system.
            you got a person name and relations.
            you MUST analyze the and relations to find the place where the looking for person is.
            you need to find all places related to this person.
            you must match teh personal relationships.
            return list of places related to this person.

            <rules>
            - return a place name as a string.
            - JSON property name: "place" is property wher you must provide the place name.
            - JSON property name: "thoughts" is property where you must provide your thoughts about the person.
            - _thoughts property is required.
            - _thoughts property MUST be a string.
            - _thoughts property MUST be a thoughts about the person based on relationships.
            - _thoughts property MUST BE FIRST.
            - _thoughts property MUST be analyzed step by step. The first action focues on the relationships between people, then mapping peaople to cities and conduct where looking for persone is.
            - _thoughts property contains bullet points of thinking proces step by step.
            - _thoughts property contains a list of thoughts about the person.
            - relationhips are the graph of connections between people and places.
            - the first generation is a first meeting with the person.
            - in _thoughts please build the path of relationships how and where meet the looking for person.
            - the last place of meet is the looking for person place. 
            - place property MUST BE SECOUND.
            - expected json format: {"_thoughts: 'YOUR THOUGHTS', " "place": 'place']}
            - place name should be a string.
            - place should be takes from relations.
            - IF person is not in relations, return place as empty string.
            - generation is a number of steps from the person.
            - generation is a number.
            - treat generations as waights of relationships. 
            - the very low generation means that the person is on the begginig of the relationship chain.
            - the very high generation means that the person is on the end of the relationship chain.
        

            </rules>

            <relations>
                ${
                    relations.map(r => `
                        <relation>
                        <person>${r.person}</person>
                        <place>${r.place}</place>
                        <generation>${r.generation}</generation>
                        </relation>
                        `).join('\n')
                }
            </relations>

            REMEMBER: you must analyze relations to find the place where the looking for person is.        
            `
            },
            {
                role: "user",
                content: person
            }
     ]
    })) as ChatCompletion;

    const content = completion.choices[0].message.content;
    debugger;
    if (content === null) {
        throw new Error("Received null content from completion.");
    }
    const _thoughts = JSON.parse(content)["_thoughts"] as string || "";
    console.log(_thoughts);
    return JSON.parse(content).place as string || "";
}


async function BuildPersonsRelations(persons: string[]): Promise<PersonRelation[]> {
    var relations: PersonRelation[] = [];
    for (const p of persons) {
        const people = await fetch(`${API_ENDPOINT}/people/${p}`, {
            method: "POST",
            body: JSON.stringify({
                "apikey": API_KEY,
                "query": p
            })
        });
        
        var peopleData = await people.json();
        if (peopleData.message.includes(RESTRICTED)) {
            continue;
        }
        if(peopleData.code !== 0){
            continue
        }
        relations.push({
            "person": p.toUpperCase(),
            "cities": peopleData.message.split(" ")
        });
    }
    return relations;
}

async function BuildPlacesRelations(places: string[]): Promise<PlaceRelation[]> {
    var relations: PlaceRelation[] = [];
    for (const p of places) {
        const places = await fetch(`${API_ENDPOINT}/places`, {
            method: "POST",
            body: JSON.stringify({
                "apikey": API_KEY,
                "query": p
            })
        });
        var placesData = await places.json();
        if (placesData.message.includes(RESTRICTED || placesData.message.includes("no data found"))) {
            continue;
        }
        if(placesData.code !== 0){
            continue
        }
        relations.push({
            "place": p.toUpperCase(),
            "persons": placesData.message.split(" ")
        });
    }

    return relations;
}

async function RecognizePerson(note: string): Promise<string[]> {
    const completion = (await openAIService.completion({
        model: "gpt-4o-mini",
        jsonMode: true,
        messages: [
          {
            role: "system", 
            content: `
            you are a person recognition system.
            you got a note and you need to recognize persons in the note.
            return list of persons in the note.

            <rules>
            - return only array of strings.
            - expected json format: ["person1", "person2", "person3"]
            - person name should be a string.
            - person should be a first name.
            - the names must be without any additional characters like: ".", ",", "!", "?", etc.
            - names MUST NOT contains any Polish letters.
            - IF name has polish letters, then use english letter instead. example: "Barbara" -> "Barbara", "Łukasz" -> "Lukasz", "Paweł" -> "Pawel"
            </rules>
        `
        },
        {
            role: "user",
            content: note
        }
    ]
    })) as ChatCompletion;
      const content = completion.choices[0].message.content;
      if (content === null) {
          throw new Error("Received null content from completion.");
      }
      return JSON.parse(content).persons as string[];
    }
    
async function RecognizePlaces(note: string): Promise<string[]> {
    const completion = (await openAIService.completion({
        model: "gpt-4o-mini",
        jsonMode: true,
        messages: [
            {
                role: "system",
                content: `
                you are a place recognition system.
                you got a note and you need to recognize places in the note.
                return list of places in the note.

                <rules>
                - return only array of strings.
                - expected json format: ["place1", "place2", "place3"]
                - place name should be a string.
                - place should be a name of a city.
                - the names must be without any additional characters like: ".", ",", "!", "?", etc.
                - names MUST NOT contains any Polish letters.
                - IF name has polish letters, then use english letter instead. example: "Warszawa" -> "Warszawa", "Łódź" -> "Lodz", "Kraków" -> "Krakow"
                - avoid using Polish colloquial or informal variations of place names, such as 'Warszawki' instead of 'Warszawa'. Krakowie instead of Krakow.
                - Return only names of cities.
                - All cities MUST be written in UPPERCASE.
                </rules>
                `
            },
            {
                role: "user",
                content: note
            }
        ]
    })) as ChatCompletion;

    const content = completion.choices[0].message.content;
    if (content === null) {
        throw new Error("Received null content from completion.");
    }

    return JSON.parse(content).places as string[];
 }

async function fetchNote(): Promise<string> {
    const note = await fetch(`${API_ENDPOINT}/dane/barbara.txt`)
    const text = await note.text(); 

    return text;
}
function inlineRelations(personsRelations: PersonRelation[], placesRelations: PlaceRelation[], generation: number): Relation[] {
    const seen = new Set<string>();
    const relations: Relation[] = [];

    // Process person relations
    for (const personRelation of personsRelations) {
        for (const city of personRelation.cities) {
            const key = `${personRelation.person}-${city}-${generation}`;
        if (!seen.has(key)) {
            seen.add(key);
                relations.push({
                    person: personRelation.person,
                    place: city,
                    generation: generation
                });
            }
        }
    }

    // Process place relations
    for (const placeRelation of placesRelations) {
        for (const person of placeRelation.persons) {
            const key = `${person}-${placeRelation.place}-${generation}`;
            if (!seen.has(key)) {
                seen.add(key);
                relations.push({
                    person: person,
                    place: placeRelation.place,
                    generation: generation
                });
            }
        }
    }

    return relations;
}

main().catch(console.error);

