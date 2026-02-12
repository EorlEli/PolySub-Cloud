import os
import shutil
import uvicorn
import time
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import threading

# Import our new modules
from grouper import read_vtt, parse_vtt_time
from transcriber import extract_audio, transcribe_audio
from text_translator import translate_full_text, verify_translation_quality
from engine import run_alignment_engine
from utils import reset_session_cost, get_session_cost, log_whisper_cost # Import these!
from translation_evaluator import evaluate_translations
from video_processor import burn_subtitles
from validator import validate_vtt_structure


app = FastAPI()

# Mount static files (to serve index.html)
app.mount("/static", StaticFiles(directory=".", html=True), name="static")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

@app.post("/process_video/")
async def process_video_endpoint(
    video_file: UploadFile = File(...),
    target_language: str = Form("Portuguese"), # Default if not chosen
    use_correction: bool = Form(True), # Default to True
    background_tasks: BackgroundTasks = None
):
    try:
        # --- 0. RESET COST COUNTER & START TIMER ---
        reset_session_cost()
        job_start_time = time.time()
        
        # --- 1. SETUP ---
        video_filename = f"temp_{video_file.filename}"
        print(f"\n🎬 NEW JOB: {video_filename} -> {target_language}")
        
        # Save uploaded video to disk
        with open(video_filename, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)

        # --- 2. EXTRACT AUDIO ---
        # Create a unique audio filename
        audio_filename = f"temp_audio_{video_file.filename}.mp3"
        audio_path = extract_audio(video_filename, audio_filename)
        if not audio_path:
            raise HTTPException(status_code=500, detail="Audio extraction failed.")

        # --- 3. TRANSCRIBE ---
        # Returns: (VTT String, English Text String)
        vtt_content, full_english_text = transcribe_audio(audio_path, use_correction=use_correction)
        
        # CALCULATE Speech2Text COST
        audio_duration = 0
        try:
            import re
            # Find the very last timestamp in the file
            timestamps = re.findall(r"--> (\d{2}:\d{2}:\d{2}\.\d{3})", vtt_content)
            
            if timestamps:
                last_timestamp = timestamps[-1]
                
                # REUSE THE ROBUST FUNCTION FROM GROUPER.
                # It handles 00:00:00.000 correctly without crashing
                seconds = parse_vtt_time(last_timestamp)
                audio_duration = seconds
                
                log_whisper_cost(seconds)

        except Exception as e:
            print(f"⚠️ Could not calculate Whisper cost: {e}")
        
        # Save VTT to a temp file because 'read_vtt' expects a file path
        temp_vtt_path = "temp_generated.vtt"
        with open(temp_vtt_path, "w", encoding="utf-8") as f:
            f.write(vtt_content)

        # --- 4. TRANSLATE TEXT (GPT) ---
        # Now returns a tuple: (full_text, source_chunks, translated_chunks)
        full_target_text1, source_chunks, translated_chunks = translate_full_text(full_english_text, target_language)
        
        if not full_target_text1:
            raise HTTPException(status_code=500, detail="Translation failed.")

        # --- 4.5. VERIFY & REFINE TRANSLATION (LLM Check) ---
        # Pass the chunks directly to verification for better context handling
        full_target_text = verify_translation_quality(source_chunks, translated_chunks, target_language)

        # START BACKGROUND EVALUATION (True Parallel - Starts Immediately)
        # We use threading so it runs alongside the Alignment Engine, 
        # instead of waiting for the file to be sent (which BackgroundTasks does).
        eval_thread = threading.Thread(
            target=evaluate_translations,
            args=(full_english_text, full_target_text1, full_target_text, target_language)
        )
        eval_thread.start()

        # --- 5. ALIGNMENT ENGINE (The Core) ---
        # Parse the English VTT we just made
        blocks = read_vtt(temp_vtt_path)
        
        # Run your logic loop
        final_segments = run_alignment_engine(blocks, full_target_text)

        # --- 6. OUTPUT GENERATION ---
        output_vtt = "WEBVTT\n\n"
        for seg in final_segments:
            output_vtt += f"{seg['start']} --> {seg['end']}\n{seg['text']}\n\n"

        temp_vtt_path2 = "temp_generated_target.vtt"
        with open(temp_vtt_path2, "w", encoding="utf-8") as f:
            f.write(output_vtt)

        # --- 6.5. VALIDATION ---
        validation_report = validate_vtt_structure(temp_vtt_path, temp_vtt_path2)
        
        # Log Validation Results
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Video: {video_file.filename} -> {target_language}\n"
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

        # --- 7. BURN SUBTITLES INTO VIDEO ---
        output_video_path = f"final_output_{video_file.filename}"
        print(f"🔥 Burning subtitles into video: {output_video_path}")
        
        final_video = burn_subtitles(video_filename, temp_vtt_path2, output_video_path)
        
        if not final_video:
             # Fallback to returning VTT if burning fails? 
             # Or raise error? Let's print error and still return VTT for now, or raise.
             # But user wants video. Let's assume it works or raise.
             print("⚠️ Subtitle burning failed, returning simple VTT instead.")
        
        # --- 8. TIME, COST & CLEANUP ---
        job_end_time = time.time()
        total_time = job_end_time - job_start_time
        total_spent = get_session_cost()
        print(f"\n💰 JOB COMPLETE. TOTAL ESTIMATED COST: ${total_spent:.5f}\n")
        print(f"⏰ TOTAL JOB TIME: {total_time/60:.2f} minutes\n")
        print(f"🎵 AUDIO DURATION: {audio_duration:.2f} seconds ({audio_duration/60:.2f} minutes)\n")

        # --- 9. Save transcripts for debugging
        with open("full_english_text.txt", "w", encoding="utf-8") as f:
            f.write(full_english_text)
        with open("full_target_text.txt", "w", encoding="utf-8") as f:
            f.write(full_target_text)

        # --- 10. BUNDLE OUTPUT ---
        import zipfile
        zip_filename = f"output_{video_file.filename}.zip"
        
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            # Add VTT
            zipf.write(temp_vtt_path2, arcname=f"subtitles_{target_language}.vtt")
            
            # Add Video if it exists
            if final_video and os.path.exists(final_video):
                zipf.write(final_video, arcname=f"subbed_{video_file.filename}")
            else:
                 print("⚠️ Video generation failed, only zipping VTT.")

        # Cleanup function to be run after response
        def cleanup_files():
            files_to_remove = [video_filename, audio_path, temp_vtt_path, temp_vtt_path2, final_video, zip_filename]
            for f in files_to_remove:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception as e:
                        print(f"⚠️ Could not delete {f}: {e}")

        # Add cleanup to background tasks
        if background_tasks:
            background_tasks.add_task(cleanup_files)

        print("✅ Job Complete. Sending zip file to user.")
        
        return FileResponse(zip_filename, media_type="application/zip", filename=zip_filename)

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        # Clean up video if it exists even on error
        if os.path.exists(video_filename):
            try:
                os.remove(video_filename)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting PolySub Server...")
    print("👉 Open your browser at: http://127.0.0.1:8080")
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)