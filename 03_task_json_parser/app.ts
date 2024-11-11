import { readFileSync, writeFileSync } from 'fs';

interface TestData {
    question: string;
    answer: number;
    test?: {
        q: string;
        a: string;
    };
}

interface JsonData {
    'test-data': TestData[];
}

function validateCalculations(data: TestData[]): { question: string; expected: number; actual: number }[] {
    const errors: { question: string; expected: number; actual: number }[] = [];
    
    for (const item of data) {
        const [num1, num2] = item.question.split('+').map(n => parseInt(n.trim()));
        const expectedSum = num1 + num2;
        
        if (expectedSum !== item.answer) {
            errors.push({
                question: item.question,
                expected: expectedSum,
                actual: item.answer
            });
        }
    }
    
    return errors;
}

function findTestQuestions(data: TestData[]): { question: string; index: number }[] {
    return data
        .map((item, index) => ({ item, index }))
        .filter(({ item }) => item.test)
        .map(({ item, index }) => ({
            question: item.test!.q,
            index
        }));
}

function fixCalculations(data: TestData[]): void {
    for (const item of data) {
        const [num1, num2] = item.question.split('+').map(n => parseInt(n.trim()));
        item.answer = num1 + num2;
    }
}

function main() {
    const filePath = '../json.txt';
    const jsonContent = readFileSync(filePath, 'utf-8');
    const data = JSON.parse(jsonContent) as JsonData;
    
    // Find calculation errors
    const errors = validateCalculations(data['test-data']);
    console.log('\nCalculation Errors:');
    errors.forEach(error => {
        console.log(`Question: ${error.question}`);
        console.log(`Expected: ${error.expected}`);
        console.log(`Actual: ${error.actual}`);
        console.log('---');
    });
    
    // Fix calculation errors
    fixCalculations(data['test-data']);
    writeFileSync(filePath, JSON.stringify(data, null, 2));
    console.log('Calculation errors have been fixed and the file has been updated.');
    
    // Find test questions that need AI responses
    const testQuestions = findTestQuestions(data['test-data']);
    console.log('\nQuestions requiring AI responses:');
    testQuestions.forEach(q => {
        console.log(`Index: ${q.index}`);
        console.log(`Question: ${q.question}`);
        console.log('---');
    });
}

main();
