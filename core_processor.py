import os
import time
import shutil
import threading
import zipfile
import re

# Import existing modules
from grouper import read_vtt, parse_vtt_time
from transcriber import extract_audio, transcribe_audio
from text_translator import translate_full_text, verify_translation_quality
from engine import run_alignment_engine
from utils import reset_session_cost, get_session_cost, log_whisper_cost
from translation_evaluator import evaluate_translations
from video_processor import burn_subtitles
from validator import validate_vtt_structure

def process_video(video_path: str, target_language: str, use_correction: bool = True):
    """
    Core video processing logic.
    Refactored from main.py to be environment-agnostic.
    
    Args:
        video_path (str): Absolute or relative path to the input video file.
        target_language (str): Target language for translation.
        use_correction (bool): Whether to use the correction step in transcription.
        
    Returns:
        dict: Contains paths to generated files and execution metadata.
              {
                  "zip_path": str,
                  "output_video_path": str,
                  "output_vtt_path": str,
                  "metadata": {
                      "duration_seconds": float,
                      "total_cost": float,
                      "processing_time": float,
                      "audio_path": str
                  }
              }
    """
    
    # Initialize Tracking
    # Note: In a stateless cloud function, global reset might be risky if handling concurrent reqs in same process,
    # but for Cloud Run Jobs (one execution per container usually) or single-threaded local, it's fine.
    # ideally utils.cost_session should be a class or context manager, but keeping as is for minimal refactor.
    reset_session_cost() 
    job_start_time = time.time()
    
    video_filename = os.path.basename(video_path)
    print(f"\n🎬 CORE: Processing {video_filename} -> {target_language}")

    cleanup_files_list = []

    try:
        # --- 2. EXTRACT AUDIO ---
        audio_filename = f"temp_audio_{video_filename}.mp3"
        audio_path = extract_audio(video_path, audio_filename)
        if not audio_path:
            raise Exception("Audio extraction failed.")
        cleanup_files_list.append(audio_path)

        # --- 3. TRANSCRIBE ---
        vtt_content, full_english_text = transcribe_audio(audio_path, use_correction=use_correction)

        # CALCULATE Speech2Text COST
        audio_duration = 0
        try:
            timestamps = re.findall(r"--> (\d{2}:\d{2}:\d{2}\.\d{3})", vtt_content)
            if timestamps:
                last_timestamp = timestamps[-1]
                seconds = parse_vtt_time(last_timestamp)
                audio_duration = seconds
                log_whisper_cost(seconds)
        except Exception as e:
            print(f"⚠️ Could not calculate Whisper cost: {e}")

        # Save VTT to a temp file
        temp_vtt_path = "temp_generated.vtt"
        with open(temp_vtt_path, "w", encoding="utf-8") as f:
            f.write(vtt_content)
        cleanup_files_list.append(temp_vtt_path)

        # --- 4. TRANSLATE TEXT (GPT) ---
        full_target_text1, source_chunks, translated_chunks = translate_full_text(full_english_text, target_language)
        if not full_target_text1:
            raise Exception("Translation failed.")

        # --- 5. VERIFY & REFINE TRANSLATION ---
        full_target_text = verify_translation_quality(source_chunks, translated_chunks, target_language)

        # START BACKGROUND EVALUATION
        # We start it here. It relies on files or data. 
        # Note: In a Cloud Run Job, we might want to wait for this? 
        # But for now, we keep the detached thread behavior if it just logs.
        eval_thread = threading.Thread(
            target=evaluate_translations,
            args=(full_english_text, full_target_text1, full_target_text, target_language)
        )
        eval_thread.start()

        # --- 6. SAVE TRANSCRIPTS ---
        # These are saved to CWD. In Cloud Run job, CWD is writable.
        with open("full_english_text.txt", "w", encoding="utf-8") as f:
            f.write(full_english_text)
        with open("full_target_text.txt", "w", encoding="utf-8") as f:
            f.write(full_target_text)

        # --- 7. ALIGNMENT ENGINE ---
        blocks = read_vtt(temp_vtt_path)
        final_segments = run_alignment_engine(blocks, full_target_text)

        # --- 8. OUTPUT GENERATION (VTT) ---
        output_vtt = "WEBVTT\n\n"
        for seg in final_segments:
            output_vtt += f"{seg['start']} --> {seg['end']}\n{seg['text']}\n\n"

        temp_vtt_path2 = "temp_generated_target.vtt"
        with open(temp_vtt_path2, "w", encoding="utf-8") as f:
            f.write(output_vtt)
        cleanup_files_list.append(temp_vtt_path2)

        # --- 9. VALIDATION ---
        validation_report = validate_vtt_structure(temp_vtt_path, temp_vtt_path2)
        
        # Log Validation Results
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Video: {video_filename} -> {target_language}\n"
        if validation_report["valid"]:
            log_entry += "✅ VALIDATION PASSED\n"
        else:
            log_entry += f"❌ VALIDATION FAILED ({len(validation_report['errors'])} errors)\n"
            for err in validation_report['errors']:
                log_entry += f"   - ERROR: {err}\n"
        
        if validation_report["warnings"]:
             log_entry += f"⚠️ WARNINGS ({len(validation_report['warnings'])}):\n"
             for warn in validation_report['warnings']:
                 log_entry += f"   - {warn}\n"
        log_entry += "-"*40 + "\n"
        
        with open("validation_log.txt", "a", encoding="utf-8") as vf:
            vf.write(log_entry)

        # --- 10. BURN SUBTITLES ---
        output_video_path = f"final_output_{video_filename}"
        print(f"🔥 Burning subtitles into video: {output_video_path}")
        
        final_video = burn_subtitles(video_path, temp_vtt_path2, output_video_path)
        
        if not final_video:
             print("⚠️ Subtitle burning failed.")
        else:
             cleanup_files_list.append(final_video)

        # --- 11. STATS ---
        job_end_time = time.time()
        total_time = job_end_time - job_start_time
        total_spent = get_session_cost()
        
        print(f"\n💰 JOB COMPLETE. TOTAL ESTIMATED COST: ${total_spent:.5f}")
        print(f"⏰ TOTAL JOB TIME: {total_time/60:.2f} minutes")

        # --- 12. BUNDLE (ZIP) ---
        # Create the zip file
        zip_filename = f"output_{video_filename}.zip"
        
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            # Add VTT
            zipf.write(temp_vtt_path2, arcname=f"subtitles_{target_language}.vtt")
            # Add Video if it exists
            if final_video and os.path.exists(final_video):
                zipf.write(final_video, arcname=f"subbed_{video_filename}")
        
        cleanup_files_list.append(zip_filename)

        return {
            "status": "success",
            "zip_path": zip_filename,           # Caller responsible for this file
            "output_video_path": final_video,   # Caller responsible for this file (if exists)
            "output_vtt_path": temp_vtt_path2,  # Caller responsible for this file
            "cleanup_files": cleanup_files_list, # List of produced files to potentially clean
            "metadata": {
                "duration_seconds": audio_duration,
                "total_cost": total_spent,
                "processing_time": total_time
            }
        }

    except Exception as e:
        print(f"❌ CORE ERROR: {e}")
        raise e
