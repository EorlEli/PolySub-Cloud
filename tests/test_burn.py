import os
import subprocess
from video_processor import burn_subtitles

def create_dummy_files():
    # Create dummy video using ffmpeg
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=5", 
        "-c:v", "libx264", "-t", "5", "dummy_video.mp4"
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Create dummy VTT
    with open("dummy.vtt", "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nHello World\n")

def cleanup():
    for f in ["dummy_video.mp4", "dummy.vtt", "test_output_burned.mp4"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

def test():
    cleanup() # Clean start
    create_dummy_files()
    
    video_path = os.path.abspath("dummy_video.mp4")
    vtt_path = os.path.abspath("dummy.vtt")
    output_path = os.path.abspath("test_output_burned.mp4")

    print(f"Testing burn_subtitles with {video_path} and {vtt_path}...")
    result = burn_subtitles(video_path, vtt_path, output_path)

    if result and os.path.exists(result) and os.path.getsize(result) > 0:
        print(f"✅ Test Passed: Output file created at {result}")
    else:
        print("❌ Test Failed: Output file not created or empty.")

    # uncomment to cleanup
    cleanup()

if __name__ == "__main__":
    test()
