import os
os.environ["PATH"] += os.pathsep + r"C:\Users\Arni\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin"
import shutil
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import whisper
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Audio to Text Generator with Summarization")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

# Load Whisper STT Model (using 'base' for decent speed/accuracy tradeoff)
print("Loading Whisper model...")
try:
    # Ensure this runs without error. Might take some time on first load.
    whisper_model = whisper.load_model("base")
except Exception as e:
    print(f"Error loading whisper model: {e}")
    whisper_model = None

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    if not file.filename.endswith(('.mp3', '.wav', '.mp4')):
        raise HTTPException(status_code=400, detail="Only .mp3, .wav, and .mp4 files are supported")
    
    if whisper_model is None:
        raise HTTPException(status_code=500, detail="Whisper model failed to load on the server.")
        
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create a safe, unique filename to avoid unicode/emoji errors on Windows
    import uuid
    _, ext = os.path.splitext(file.filename)
    safe_filename = f"upload_{uuid.uuid4().hex}{ext}"
    temp_file_path = os.path.join(temp_dir, safe_filename)
    
    try:
        # 1. Save uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Transcribe Audio using Whisper
        safe_print_name = file.filename.encode('ascii', 'ignore').decode('ascii')
        print(f"Transcribing {safe_print_name}...")
        result = whisper_model.transcribe(temp_file_path)
        transcript = result["text"]
        
        # 3. Summarize using Gemini
        summary = ""
        key_points = []
        
        if GEMINI_API_KEY and transcript.strip():
            print("Generating summary with Gemini...")
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            Summarize the following transcript clearly and extract important key points.
            Format the response exactly as a JSON object with two keys:
            1. "summary": A short paragraph summarizing the text.
            2. "key_points": A list of strings, each being a key point.
            
            Transcript:
            {transcript}
            """
            
            response = model.generate_content(prompt)
            
            try:
                # Attempt to parse the JSON from Gemini's response
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:-3]
                elif response_text.startswith("```"):
                    response_text = response_text[3:-3]
                    
                gemini_data = json.loads(response_text)
                summary = gemini_data.get("summary", "Summary could not be generated.")
                key_points = gemini_data.get("key_points", [])
            except json.JSONDecodeError:
                print("Failed to parse Gemini response as JSON:", response.text)
                summary = "Error parsing summary from LLM."
                key_points = [response.text]
        else:
            summary = "Gemini API key not configured or empty transcript."
            key_points = ["Please set GEMINI_API_KEY in backend."]
            
        return {
            "transcript": transcript,
            "summary": summary,
            "key_points": key_points
        }
        
    except Exception as e:
        print(f"Error during processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
