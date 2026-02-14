import os
import subprocess
import shlex

def burn_subtitles(video_path, vtt_path, output_path):
    """
    Burns VTT subtitles into a video file using ffmpeg.
    
    Args:
        video_path (str): Path to the input video file.
        vtt_path (str): Path to the VTT subtitle file.
        output_path (str): Path to save the output video file.
        
    Returns:
        str: Path to the output video file if successful, None otherwise.
    """
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found: {video_path}")
        return None
    if not os.path.exists(vtt_path):
        print(f"❌ Error: Subtitle file not found: {vtt_path}")
        return None

    # Use absolute paths to avoid issues with CWD or filters
    video_path = os.path.abspath(video_path)
    vtt_path = os.path.abspath(vtt_path)
    output_path = os.path.abspath(output_path)

    # Escape paths for ffmpeg filter
    # On Windows, we need to handle backslashes carefully for the filter string
    # Replace backslashes with forward slashes is usually safer for ffmpeg filters on Windows
    vtt_path_filter = vtt_path.replace("\\", "/").replace(":", "\\:")

    # Construct the ffmpeg command
    # -i input_video -vf "subtitles=filename" -c:a copy output_video
    # we prefer libx264 for compatibility, but user didn't specify. 
    # Let's try to just act on the video stream and copy audio to be fast.
    command = [
        "ffmpeg",
        "-y", # Overwrite output file
        "-i", video_path,
        "-vf", f"subtitles='{vtt_path_filter}'",
        "-c:a", "copy",
        output_path
    ]

    print(f"🎬 Running ffmpeg command: {' '.join(command)}")

    try:
        # Run ffmpeg
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✅ Subtitles burned successfully.")
        return output_path
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8')
        print(f"❌ Error burning subtitles: {error_msg}")
        return None
