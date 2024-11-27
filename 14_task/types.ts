export type PlaceRelation = {
    place: string;
    persons: string[];
}

export type PersonRelation = {
    person: string;
    cities: string[];
} 
export type Relation = {
    person: string;
    place: string;
    generation: number;
}