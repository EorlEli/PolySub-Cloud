import os
import ffmpeg
from openai import OpenAI
from dotenv import load_dotenv
from deepgram import DeepgramClient
# REMOVE deepgram_captions logic
# from deepgram_captions import DeepgramConverter, webvtt

from corrector import apply_corrections

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
deepgram_client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

def extract_audio(video_path, output_audio_path="temp_audio.mp3"):
    """
    Step 2: Extracts audio track from video file using FFmpeg.
    Compresses to MP3 to save bandwidth/cost.
    """
    # If no specific name provided, make a unique one based on the video name
    if output_audio_path is None:
        base_name = os.path.splitext(video_path)[0]
        output_audio_path = f"{base_name}_audio.mp3"
    
    print(f"   🎥 Extracting audio from {os.path.basename(video_path)}...")
    
    try:
        # Run ffmpeg command: input video -> map audio (0:a) -> output mp3
        # -y means 'overwrite output file if exists'
        (
            ffmpeg
            .input(video_path)
            .output(output_audio_path, ab='64k', ac=1, loglevel="quiet") # 64k bitrate is enough for speech
            .overwrite_output()
            .run()
        )
        print(f"   ✅ Audio saved to {output_audio_path}")
        return output_audio_path
    
    except ffmpeg.Error as e:
        print(f"   ❌ FFmpeg Error: {e}")
        return None

def format_timestamp(seconds):
    """
    Converts float seconds to WebVTT timestamp format: HH:MM:SS.mmm
    """
    if seconds is None:
        return "00:00:00.000"
    
    milliseconds = int((seconds % 1) * 1000)
    int_seconds = int(seconds)
    hours = int_seconds // 3600
    minutes = (int_seconds % 3600) // 60
    seconds_rem = int_seconds % 60
    
    return f"{hours:02}:{minutes:02}:{seconds_rem:02}.{milliseconds:03}"

def generate_vtt_from_utterances(utterances):
    """
    Generates a WebVTT string from the list of utterances.
    """
    vtt_output = "WEBVTT\n\n"
    
    for u in utterances:
        start_time = format_timestamp(u.get("start", 0))
        end_time = format_timestamp(u.get("end", 0))
        text = u.get("transcript", "").strip()
        
        # Output block
        vtt_output += f"{start_time} --> {end_time}\n{text}\n\n"
        
    return vtt_output

def transcribe_audio(audio_path, use_correction=True):
    """
    Step 3: Sends audio to Deepgram (Nova-2) to get VTT and Text.
    """
    print("   🎙️ Sending audio to Deepgram Nova-2 API...")
    
    try:
        # 1. Read Audio File
        with open(audio_path, "rb") as file:
            buffer_data = file.read()
        
        # 2. Configure Deepgram Options
        # smart_format=True: Adds punctuation and capitalization
        # model="nova-2": Fastest and most accurate model
        options = {
            "model": "nova-3",
            "smart_format": True,
            "utterances": True,      # Required for VTT conversion
            "detect_language": True, # Auto-detects language
        }
        
        # 3. Call API (Once)
        # Using deepgram-sdk v3+ structure: listen.v1.media.transcribe_file
        response = deepgram_client.listen.v1.media.transcribe_file(
            request=buffer_data,
            **options
        )
        
        # 4. LLM Correction
        if use_correction:
            print("   🧠 Analyzing and correcting transcription...")
            # This updates response['results']['utterances'] transcript text
            response, transcript_text = apply_corrections(response, openai_client)
        else:
            print("   ⏩ Skipping LLM correction (User disabled it).")
            transcript_text = response.results.channels[0].alternatives[0].transcript
        
        # 5. Generate VTT (Custom Logic)
        
        # Normalize to dict if not already (for the VTT generator & normalization)
        import json
        if not isinstance(response, dict):
             if hasattr(response, "to_dict"): response = response.to_dict()
             elif hasattr(response, "model_dump"): response = response.model_dump()
             else: response = json.loads(response.to_json())

        # 5b. Normalize Text (Fix "U. S." -> "U.S.")
        transcript_text = normalize_spaced_acronyms(transcript_text)

        try:
            utterances = response["results"]["utterances"]
        except KeyError:
            print("   ⚠️ No utterances found. Returning empty VTT.")
            utterances = []
            
        # Clean utterance transcripts
        for u in utterances:
             if 'transcript' in u:
                 u['transcript'] = normalize_spaced_acronyms(u['transcript'])

        transcript_vtt = generate_vtt_from_utterances(utterances)
        
        print("   ✅ Transcription complete.")
        return transcript_vtt, transcript_text

    except Exception as e:
        print(f"   ❌ Deepgram Error: {e}")
        raise e

def normalize_spaced_acronyms(text):
    """
    Fixes "U. S. A." -> "U.S.A."
    """
    if not text: return ""
    import re
    pattern = r'(?<=\b[A-Z]\.)\s+(?=[A-Z]\.)'
    for _ in range(3):
        new_text = re.sub(pattern, '', text)
        if new_text == text: break
        text = new_text
    return text
