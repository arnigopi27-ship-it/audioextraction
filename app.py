import os
import shutil
import json
import uuid
import streamlit as st
import whisper
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables (for local dev)
load_dotenv()

# Add ffmpeg to PATH for Windows local development only
if os.name == 'nt':
    ffmpeg_path = r"C:\Users\Arni\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin"
    if ffmpeg_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + ffmpeg_path

# Configure Page
st.set_page_config(page_title="Audio Intelligence", page_icon="🎙️", layout="centered")

# Custom CSS for a clean look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #9E9E9E;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">Audio Intelligence 🎙️</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Convert speech to text and extract key insights instantly using AI.</p>', unsafe_allow_html=True)

# Load API Key (Try Streamlit secrets first, then environment variable)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.warning("⚠️ GEMINI_API_KEY is not set. Summarization will not work. Please add it to your Streamlit secrets or .env file.")

# Cache the whisper model so it doesn't reload on every interaction
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

model_load_state = st.text("Loading Whisper AI model... (this may take a moment on first run)")
try:
    whisper_model = load_whisper_model()
    model_load_state.empty()
except Exception as e:
    model_load_state.error(f"Failed to load Whisper model: {e}")
    whisper_model = None

uploaded_file = st.file_uploader("Upload Audio or Video File", type=['mp3', 'wav', 'mp4'])

if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    if st.button("Generate Insights", type="primary"):
        if whisper_model is None:
            st.error("Whisper model is not available.")
        else:
            temp_dir = "temp_audio"
            os.makedirs(temp_dir, exist_ok=True)
            
            _, ext = os.path.splitext(uploaded_file.name)
            safe_filename = f"upload_{uuid.uuid4().hex}{ext}"
            temp_file_path = os.path.join(temp_dir, safe_filename)
            
            try:
                # Save temporarily
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                with st.spinner("🎧 Transcribing audio with Whisper... This might take a minute."):
                    result = whisper_model.transcribe(temp_file_path)
                    transcript = result["text"]
                
                summary = ""
                key_points = []
                
                if GEMINI_API_KEY and transcript.strip():
                    with st.spinner("🧠 Generating insights with Gemini..."):
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
                            response_text = response.text.strip()
                            if response_text.startswith("```json"):
                                response_text = response_text[7:-3]
                            elif response_text.startswith("```"):
                                response_text = response_text[3:-3]
                                
                            gemini_data = json.loads(response_text)
                            summary = gemini_data.get("summary", "Summary could not be generated.")
                            key_points = gemini_data.get("key_points", [])
                        except json.JSONDecodeError:
                            summary = "Error parsing summary from LLM."
                            key_points = [response.text]
                
                # Display Results
                st.subheader("📝 AI Summary")
                st.info(summary if summary else "No summary available.")
                
                st.subheader("🔑 Key Points")
                if key_points:
                    for pt in key_points:
                        st.write(f"- {pt}")
                else:
                    st.write("No key points extracted.")
                    
                with st.expander("📄 Full Transcript"):
                    st.write(transcript)
                    
            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
            finally:
                # Explicit cleanup ensuring data isn't stored
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

st.markdown("---")
st.caption("🔒 **Privacy Note:** Your audio files are only stored temporarily for processing and are immediately deleted from the server after analysis is complete.")
