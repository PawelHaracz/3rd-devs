# Note: DALL-E 3 requires version 1.0.0 of the openai-python library or later
import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI
import json
import requests
from dotenv import load_dotenv

load_dotenv()

taskId = "robotid"
dev_ai_api_key = os.getenv("DEV_AI_KEY")
# Download and read the JSON data from URL
url = f'https://centrala.ag3nts.org/data/{dev_ai_api_key}/robotid.json'
response = requests.get(url)
robot_data = response.json()

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

client = OpenAI()

result = client.images.generate(
    model="dall-e-3", # the name of your DALL-E 3 deployment
    prompt=robot_data['description'],
    n=1,
    size="1024x1024",
    quality="standard",
    response_format="url"
)

image_url = json.loads(result.model_dump_json())['data'][0]['url']

print(image_url)

# Send the result to the specified endpoint
report_url = "https://centrala.ag3nts.org/report"
payload = {
    "task": taskId,
    "apikey": dev_ai_api_key,
    "answer": image_url
}

report_response = requests.post(report_url, json=payload)
print(report_response.json())
