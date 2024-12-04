import json

def read_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip().split(',') for line in file if line.strip()]

def create_jsonl(incorrect_path, correct_path, output_path):
    incorrect_data = read_file(incorrect_path)
    correct_data = read_file(correct_path)
    
    # Convert strings to integers
    incorrect_data = [[int(num) for num in row] for row in incorrect_data]
    correct_data = [[int(num) for num in row] for row in correct_data]
    
    with open(output_path, 'w') as outfile:
        for incorrect, correct in zip(incorrect_data, correct_data):
            # Create the conversation format
            json_line = create_json_line(",".join(map(str, incorrect)), "INCORRECT")
            outfile.write(json_line + '\n')
            json_line = create_json_line(",".join(map(str, correct)), "CORRECT")
            outfile.write(json_line + '\n')
            json_line = create_json_line(", ".join(map(str, incorrect)), "INCORRECT")
            outfile.write(json_line + '\n')
            json_line = create_json_line(", ".join(map(str, correct)), "CORRECT")
            outfile.write(json_line + '\n')



def create_json_line(sample:str, answer:str):
    conversation = {
    "messages": [
        {
            "role": "system",
            "content": "Decide if sample is correct or incorrect."
        },
        {
            "role": "user",
            "content": sample
        },
        {
            "role": "assistant",
            "content": answer
        }
        ]
    }
        
    # Write the JSON line
    json_line = json.dumps(conversation, ensure_ascii=False)
    return json_line

if __name__ == "__main__":
    incorrect_path = "lab_data/incorrect.txt"
    correct_path = "lab_data/correct.txt"
    output_path = "training_data.jsonl"
    
    create_jsonl(incorrect_path, correct_path, output_path)
