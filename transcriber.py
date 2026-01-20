import os
import ffmpeg
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def transcribe_audio(audio_path):
    """
    Step 3: Sends audio to OpenAI Whisper API to get the source VTT.
    """
    print("   🎙️ Sending audio to Whisper API (Transcribing)...")
    
    audio_file = open(audio_path, "rb")
    
    # We ask for TWO things:
    # 1. The VTT file (for timestamps)
    # 2. The Raw Text (for translation context)
    
    # First, get the VTT
    transcript_vtt = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file, 
        response_format="vtt"
    )
    
    # Reset file pointer to read again for raw text
    audio_file.seek(0)
    
    # Second, get the plain text (optional, but helpful for the Translator Step)
    transcript_text = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file, 
        response_format="text"
    )
    
    print("   ✅ Transcription complete.")
    return transcript_vtt, transcript_text

# --- Quick Test Block ---
if __name__ == "__main__":
    # Test this file independently
    # Put a dummy 'test.mp4' in your folder to test this.
    test_video = "test.mp4" 
    if os.path.exists(test_video):
        audio = extract_audio(test_video)
        if audio:
            vtt, text = transcribe_audio(audio)
            print("\n--- VTT PREVIEW ---\n", vtt)
            print("\n--- TEXT PREVIEW ---\n", text)
    else:
        print("⚠️ No 'test.mp4' found. Please add a video file to test.")