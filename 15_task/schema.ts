export class ApiDBRequest{
    public readonly task: string = 'database';
    public apikey: string = '';
    public query: string = '';

    constructor(apiKey: string, query: string){
        this.apikey = apiKey;
        this.query = query;
    }
}


export class ApiDBResponse {
    public reply: object[] = [];
    public error: string = '';
}

