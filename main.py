import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import logging
import sys
import os
from dotenv import load_dotenv

# --- SETUP LOGGING ---
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# --- IMPORT MODULES ---
try:
    from grouper import parse_vtt_lines, get_clean_blocks
    from matcher import find_matching_translation
    from distributor import distribute_translation
except ImportError as e:
    print(f"CRITICAL: Could not import modules. {e}")
    exit(1)

load_dotenv()
app = FastAPI()

def generate_vtt_string(segments):
    output = ["WEBVTT\n"]
    for i, seg in enumerate(segments, 1):
        output.append(str(i))
        output.append(f"{seg['start']} --> {seg['end']}")
        output.append(f"{seg['text']}\n")
    return "\n".join(output)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Backend is running. Upload index.html.</h1>"

@app.post("/process/")
async def process_subtitles(
    english_vtt: UploadFile = File(...),
    portuguese_txt: UploadFile = File(...)
):
    print(f"\n--- NEW JOB: {english_vtt.filename} (STRICT CURSOR MODE) ---")

    # 1. READ FILES
    try:
        vtt_content = (await english_vtt.read()).decode("utf-8")
        pt_full_text = (await portuguese_txt.read()).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading files: {e}")

    # 2. GROUPING
    print("1. Grouping English lines...")
    raw_lines = parse_vtt_lines(vtt_content)
    blocks = get_clean_blocks(raw_lines)
    
    if not blocks:
        raise HTTPException(status_code=400, detail="No blocks found.")
    print(f"   -> Found {len(blocks)} blocks.")

    final_segments = []
    
    # --- LOGIC: STRICT CURSOR ---
    pt_cursor = 0 
    
    # We use 1000 chars (approx 150 words). 
    # This is plenty for even the longest sentence, but efficient.
    WINDOW_SIZE = 1000 

    try:
        for i, block in enumerate(blocks):
            en_text = " ".join([l['text'] for l in block])
            print(f"[{i+1}/{len(blocks)}] Processing lines {block[0]['id']}-{block[-1]['id']}...")

            # --- STEP A: PREPARE WINDOW (The Fix) ---
            # We create a "Rearview Mirror" of 50 characters.
            # This prevents the "Greedy Neighbor" bug where the previous block eat the first word of this block.
            overlap = 50
            window_start = max(0, pt_cursor - overlap)
            window_end = pt_cursor + WINDOW_SIZE
            
            # Slice the text using the new, wider window
            pt_window = pt_full_text[window_start : window_end]

            # --- STEP B: FIND MATCH ---
            matched_text = find_matching_translation(en_text, pt_window)
            
            if not matched_text:
                # If we still don't find it, we log it but do NOT crash.
                print(f"   ⚠️ Block {i+1}: No match found. Cursor stuck at {pt_cursor}.")
                debug_trap = True
                matched_text = "[TRANSLATION NOT FOUND]"
                
                # OPTIONAL: You could force the cursor forward slightly to try to "skip" the bad spot
                # pt_cursor += 50 
            else:
                # --- STEP C: UPDATE CURSOR (Math Adjustment) ---
                found_index = pt_window.find(matched_text)
                
                if found_index != -1:
                    # We must calculate the absolute position in the file.
                    # Formula: (Start of Window) + (Location in Window) + (Length of Match)
                    absolute_end = window_start + found_index + len(matched_text)
                    
                    # Log the jump
                    # print(f"   -> Match found. Moving cursor to {absolute_end}")
                    
                    # Update the master cursor
                    pt_cursor = absolute_end
                else:
                    print("   ⚠️ Error: AI returned text not found in window.")

            # --- STEP D: DISTRIBUTE LINES ---
            new_segments = distribute_translation(block, matched_text)
            final_segments.extend(new_segments)

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # 4. OUTPUT
    final_vtt = generate_vtt_string(final_segments)
    output_filename = "Portuguese_Aligned.vtt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_vtt)
    
    return FileResponse(output_filename, media_type='text/vtt', filename=output_filename)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)