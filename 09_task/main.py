# Note: DALL-E 3 requires version 1.0.0 of the openai-python library or later
import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI
import json
import requests
from dotenv import load_dotenv
import base64

load_dotenv()

taskId = "kategorie"
dev_ai_api_key = os.getenv("DEV_AI_KEY")

client = OpenAI()

def process_text_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate a concise summary of the following text:"},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message.content

def process_audio_file(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate a concise summary of the following audio transcript:"},
                {"role": "user", "content": transcript.text}
            ]
        )
        return response.choices[0].message.content

def process_image_file(file_path):
    with open(file_path, "rb") as image_file:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe what you see in this image and provide a summary."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
                            }
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content

def generate_summaries():
    base_dir = "09_task/pliki_z_fabryki"
    output_file = "09_task/summaries.jsonl"
    
    with open(output_file, 'w') as jsonl_file:
        # Process all files in the main directory
        for file in os.listdir(base_dir):
            # Skip the facts folder
            if file == "facts":
                continue
                
            file_path = os.path.join(base_dir, file)
            if os.path.isfile(file_path):
                summary = None
                if file.endswith('.txt'):
                    summary = process_text_file(file_path)
                elif file.endswith('.mp3'):
                    summary = process_audio_file(file_path)
                elif file.endswith('.png'):
                    summary = process_image_file(file_path)
                
                if summary:
                    json_line = json.dumps({"file": file, "summary": summary})
                    jsonl_file.write(json_line + '\n')
    
    return output_file

def classify_summary(summary):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """Analyze if the text contains information about:
                1. People - Include if there's evidence of:
                   - Detected unauthorized individuals
                   - People transferred to control/investigation
                   - Physical evidence of intrusion (fingerprints)
                   - Found hidden devices (transmitters)
                   - Captured or detained individuals
                   DO NOT include:
                   - Unsuccessful searches
                   - Regular staff activities
                   - False alarms about wildlife

                2. Hardware - Include ONLY if there's evidence of:
                   - Physical equipment repairs (like fixing antennas, sensors)
                   - Component replacements (like cells, relays)
                   - Fixed hardware malfunctions
                   DO NOT include:
                   - Software updates
                   - Communication system updates
                   - Protocol implementations
                   - Regular monitoring
                   - System configurations

                Return exactly one of these values (without quotes):
                - people (if unauthorized people were detected/captured or evidence found)
                - hardware (if physical repairs were made)
                - both (if both criteria are met)
                - skip (for everything else)"""
            },
            {"role": "user", "content": summary}
        ]
    )
    return response.choices[0].message.content.lower().strip().replace("'", "").replace('"', '')

def filter_summaries(input_file):
    output_file = "09_task/summaries_2.jsonl"
    
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            entry = json.loads(line)
            classification = classify_summary(entry['summary'])
            
            if classification not in ['skip']:
                # If classification is 'both', create two entries
                if classification == 'both':
                    # Create people entry
                    people_entry = {
                        "file": entry['file'],
                        "summary": entry['summary'],
                        "type": "people"
                    }
                    outfile.write(json.dumps(people_entry) + '\n')
                    
                    # Create hardware entry
                    hardware_entry = {
                        "file": entry['file'],
                        "summary": entry['summary'],
                        "type": "hardware"
                    }
                    outfile.write(json.dumps(hardware_entry) + '\n')
                else:
                    # Create single entry for people or hardware
                    filtered_entry = {
                        "file": entry['file'],
                        "summary": entry['summary'],
                        "type": classification
                    }
                    outfile.write(json.dumps(filtered_entry) + '\n')
    
    return output_file

def verify_not_staff_related(summary):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """Analyze if this text describes:

                For PEOPLE category - Include if it mentions:
                - Detected unauthorized individuals
                - People transferred to control/investigation
                - Found fingerprints or hidden devices
                - Captured or detained individuals
                Return 'false' for these cases (to include them)

                Return 'true' for:
                - Regular staff activities
                - Unsuccessful searches
                - False alarms
                - Regular monitoring

                For HARDWARE category - Include if it mentions:
                - Physical repairs (antennas, sensors)
                - Component replacements
                - Hardware fixes
                Return 'false' for these cases (to include them)

                Return 'true' for:
                - Software updates
                - System configurations
                - Communication protocols
                - Regular monitoring"""
            },
            {"role": "user", "content": summary}
        ]
    )
    result = response.choices[0].message.content.lower().strip()
    return result == 'false'  # Return True if it's NOT about staff/software

def create_final_structure(filtered_file):
    result = {
        "people": [],
        "hardware": []
    }
    
    with open(filtered_file, 'r') as file:
        for line in file:
            entry = json.loads(line)
            # First verify it's not about regular staff/software
            if verify_not_staff_related(entry['summary']):
                # Clean up type variations
                entry_type = entry['type'].lower().strip().replace('"', '').replace("'", "")
                if entry_type == 'people':
                    result['people'].append(entry['file'])
                elif entry_type == 'hardware':
                    result['hardware'].append(entry['file'])
    
    # Remove duplicates and sort
    result['people'] = sorted(list(set(result['people'])))
    result['hardware'] = sorted(list(set(result['hardware'])))
    
    return result

# Step 1: Generate summaries for all files
print("Step 1: Generating summaries...")
summaries_file = generate_summaries()
print(f"Summaries have been saved to {summaries_file}")

# Step 2: Filter and classify summaries
print("\nStep 2: Filtering and classifying summaries...")
filtered_file = filter_summaries(summaries_file)
print(f"Filtered summaries have been saved to {filtered_file}")

# Step 3: Create final structure with staff verification
print("\nStep 3: Creating final structure (with staff verification)...")
final_structure = create_final_structure(filtered_file)
print("\nFinal Structure:")
print(json.dumps(final_structure, indent=2))

# Send the result to the specified endpoint
report_url = "https://centrala.ag3nts.org/report"
payload = {
    "task": taskId,
    "apikey": dev_ai_api_key,
    "answer": final_structure
}

report_response = requests.post(report_url, json=payload)
print("\nAPI Response:")
print(report_response.json())
