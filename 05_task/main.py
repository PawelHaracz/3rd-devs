import os
from dotenv import load_dotenv
from openai import OpenAI
client = OpenAI()

def transcribe_folder():
    # Load Whisper model
    client = OpenAI()
    
    # Create output text file
    with open("/Users/pawelharacz/src/ai_devs/3rd-devs/05_task/transcriptions.txt", "w", encoding="utf-8") as outfile:
        outfile.write("<transcriptions>\n")
        # Process each WAV file in przesulanie folder
        for filename in os.listdir("/Users/pawelharacz/src/ai_devs/3rd-devs/05_task/przesluchania"):
            if filename.endswith(".m4a"):
                filepath = os.path.join("/Users/pawelharacz/src/ai_devs/3rd-devs/05_task/przesluchania", filename)
                audio_file= open(filepath, "rb")
                # Transcribe audio
                result = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                    )
                
                # Write transcription to file
                outfile.write(f"<filename>{filename}</filename>\n")
                outfile.write(f"<transcription>{result.text}</transcription>\n")
                outfile.write("-" * 80 + "\n")
                
                print(f"Transcribed {filename}")
        outfile.write("</transcriptions>\n")
if __name__ == "__main__":
    load_dotenv()
    transcribe_folder()
