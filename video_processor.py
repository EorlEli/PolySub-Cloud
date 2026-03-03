import os
import subprocess
import shlex

import platform

def burn_subtitles(video_path, vtt_path, output_path, target_language=None):
    """
    Burns VTT subtitles into a video file using ffmpeg.
    
    Args:
        video_path (str): Path to the input video file.
        vtt_path (str): Path to the VTT subtitle file.
        output_path (str): Path to save the output video file.
        target_language (str): Optional. Target language of the subtitles.

        
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

    # Determine fallback font style for CJK languages to avoid white squares
    font_style = ""
    if target_language:
        lang_lower = target_language.lower()
        if any(cjk in lang_lower for cjk in ["chinese", "japanese", "korean"]):
            os_name = platform.system()
            if os_name == "Windows":
                cjk_font = "Microsoft YaHei"
            elif os_name == "Darwin":
                cjk_font = "PingFang SC"
            else:
                cjk_font = "Noto Sans CJK SC"
            font_style = f":force_style='Fontname={cjk_font}'"

    # Construct the ffmpeg command
    # -i input_video -vf "subtitles=filename:force_style='Fontname=Fallback'" -c:a copy output_video
    # we prefer libx264 for compatibility, but user didn't specify. 
    # Let's try to just act on the video stream and copy audio to be fast.
    command = [
        "ffmpeg",
        "-y", # Overwrite output file
        "-i", video_path,
        "-vf", f"subtitles='{vtt_path_filter}'{font_style}",
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
