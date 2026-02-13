import os
import shutil
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import the new core logic
from core_processor import process_video

app = FastAPI()

# Mount static files (to serve index.html)
app.mount("/static", StaticFiles(directory=".", html=True), name="static")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

@app.post("/process_video/")
async def process_video_endpoint(
    video_file: UploadFile = File(...),
    target_language: str = Form("Portuguese"), 
    use_correction: bool = Form(True),
    background_tasks: BackgroundTasks = None
):
    video_filename = f"temp_{video_file.filename}"
    print(f"\n📥 RECEIVING UPLOAD: {video_filename} -> {target_language}")
    
    try:
        # 1. Save Uploaded File to Disk
        with open(video_filename, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)

        # 2. Call Core Processor
        # This runs the logic synchronously.
        result = process_video(video_filename, target_language, use_correction)
        
        zip_path = result["zip_path"]
        cleanup_list = result["cleanup_files"]
        
        # Add the original uploaded video to cleanup list
        cleanup_list.append(video_filename)

        # 3. Define Cleanup Background Task
        def cleanup_files():
            print("🧹 Cleaning up temp files...")
            for f in cleanup_list:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception as e:
                        print(f"⚠️ Could not delete {f}: {e}")

        if background_tasks:
            background_tasks.add_task(cleanup_files)

        print(f"✅ Sending response: {zip_path}")
        return FileResponse(zip_path, media_type="application/zip", filename=zip_path)

    except Exception as e:
        print(f"❌ API ERROR: {e}")
        # Emergency cleanup of the uploaded file if processing crashed
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