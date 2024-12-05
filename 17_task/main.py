import json

def read_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip().split(',') for line in file if line.strip()]

def create_jsonl(incorrect_path, correct_path, output_path, test_data_path):
    incorrect_data = read_file(incorrect_path)
    correct_data = read_file(correct_path)
    
    # Convert strings to integers
    incorrect_data = [[int(num) for num in row] for row in incorrect_data]
    correct_data = [[int(num) for num in row] for row in correct_data]
    
    with open(output_path, 'w') as outfile:
        for correct in correct_data[0:int((len(correct_data)/3 * 2))]:
            json_line = create_json_line(",".join(map(str, correct)), True)
            outfile.write(json_line + '\n')

        for incorrect in incorrect_data[0:int(len(incorrect_data)/3 * 2)]:
            json_line = create_json_line(",".join(map(str, incorrect)), False)
            outfile.write(json_line + '\n')

    with open(test_data_path, 'w') as outfile:
        for correct in correct_data[int(len(correct_data)/3 * 2):]:
            json_line = create_json_line(",".join(map(str, correct)), True)
            outfile.write(json_line + '\n')

        for incorrect in incorrect_data[int(len(incorrect_data)/3 * 2):]:
            json_line = create_json_line(",".join(map(str, incorrect)), False)
            outfile.write(json_line + '\n')


def create_json_line(sample:str, answer:bool) -> str:
    conversation = {
    "messages": [
            {
                "role": "system",
                "content": "Decide if sample is correct or incorrect. Type 'CORRECT' or 'INCORRECT'. there is a pattern in the numbers."
            },
            {
                "role": "user",
                "content": sample
            },
            {
                "role": "assistant",
                "content": f"{answer}"
            }
        ]
    }
        
    # Write the JSON line
    json_line = json.dumps(conversation, ensure_ascii=False)
    return json_line

if __name__ == "__main__":
    base_path = "17_task/lab_data"
    incorrect_path = f"{base_path}/incorrect.txt"
    correct_path = f"{base_path}/correct.txt"
    output_path = f"{base_path}/training_data.jsonl"
    test_data_path = f"{base_path}/test_data.jsonl"
    
    create_jsonl(incorrect_path, correct_path, output_path, test_data_path)
