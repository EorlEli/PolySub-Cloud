import os
import sys
import shutil
import uvicorn
import builtins
from functools import partial
from dotenv import load_dotenv
import uuid
from google.cloud import storage
from google.cloud import firestore
from google.cloud import run_v2
import datetime

load_dotenv()

# GCP CONFIG
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
INPUT_BUCKET = os.getenv("INPUT_BUCKET")
OUTPUT_BUCKET = os.getenv("OUTPUT_BUCKET")
REGION = os.getenv("GCP_REGION", "europe-north1")
JOB_NAME = os.getenv("CLOUD_RUN_JOB_NAME", "polysub-processor-job")
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "jobs")


# 1. Force Unbuffered Output (Environment)
os.environ["PYTHONUNBUFFERED"] = "1"

# 2. Patch print to always flush (Application Level)
builtins.print = partial(builtins.print, flush=True)

# 3. Reconfigure stdout (System Level)
sys.stdout.reconfigure(line_buffering=True)
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import the new core logic
from core_processor import process_video

app = FastAPI()

# Initialize GCP Clients (Reuse connections)
storage_client = storage.Client()
firestore_client = firestore.Client()


# Mount static files (to serve index.html)
app.mount("/static", StaticFiles(directory=".", html=True), name="static")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

@app.post("/process_video/")
def process_video_endpoint(
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

@app.post("/trigger_cloud_job/")
async def trigger_cloud_job(
    video_file: UploadFile = File(...),
    target_language: str = Form("Portuguese")
):
    try:
        # 1. Generate Unique Job ID
        job_id = str(uuid.uuid4())
        short_id = job_id[:8]
        print(f"\n🚀 NEW CLOUD JOB: {short_id} -> {target_language}")

        print(f"DTO: {video_file.filename} Size: {video_file.size}")

        # 2. Upload to GCS
        # Name format: {job_id}_{original_filename} to prevent collisions
        safe_filename = f"{job_id}_{video_file.filename}"
        bucket = storage_client.bucket(INPUT_BUCKET)
        if not bucket.exists():
            print(f"❌ CRITICAL ERROR: Bucket {INPUT_BUCKET} does not exist!")
            raise Exception(f"Bucket {INPUT_BUCKET} not found.")

        blob = bucket.blob(safe_filename)
        print(blob)
        
        # Rewind file just in case
        await video_file.seek(0)
        
        print(f"📤 Uploading to {INPUT_BUCKET}...")
        blob.upload_from_file(video_file.file, content_type=video_file.content_type)
        print("✅ Upload complete.")

        # VERIFICATION
        # Force a reload to check against the server
        try:
            blob.reload()
            print(f"✅ GCS Verification: Object {blob.name} exists in {blob.bucket.name}.")
        except Exception as e:
             print(f"❌ CRITICAL: File was NOT found in GCS immediately after upload! Error: {e}")
             raise Exception(f"Upload Verification Failed: {e}")

        # 3. Create Firestore Entry
        doc_ref = firestore_client.collection(FIRESTORE_COLLECTION).document(job_id)
        doc_ref.set({
            "job_id": job_id,
            "status": "queued",
            "created_at": firestore.SERVER_TIMESTAMP,
            "filename": video_file.filename,
            "target_language": target_language
        })

        # 4. Trigger Cloud Run Job
        # We override env vars for THIS specific execution
        client = run_v2.JobsClient()
        job_path = client.job_path(PROJECT_ID, REGION, JOB_NAME)
        
        request = run_v2.RunJobRequest(
            name=job_path,
            overrides=run_v2.RunJobRequest.Overrides(
                container_overrides=[
                    run_v2.RunJobRequest.Overrides.ContainerOverride(
                        env=[
                            {"name": "VIDEO_FILENAME", "value": safe_filename},
                            {"name": "TARGET_LANGUAGE", "value": target_language},
                            {"name": "FIRESTORE_DOC_ID", "value": job_id},
                            {"name": "OUTPUT_BUCKET", "value": OUTPUT_BUCKET}
                        ]
                    )
                ]
            )
        )
        
        operation = client.run_job(request=request)
        print(f"✅ Cloud Run Job Triggered: {operation.operation.name}")

        return {"job_id": job_id, "status": "queued"}

    except Exception as e:
        print(f"❌ CLOUD TRIGGER FAILED: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/check_status/{job_id}")
def check_status(job_id: str):
    try:
        doc_ref = firestore_client.collection(FIRESTORE_COLLECTION).document(job_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Job not found")

        data = doc.to_dict()
        status = data.get("status", "unknown")
        
        response = {"status": status}

        if status == "done":
            # Generate Signed URLs for secure download
            outputs = data.get("outputs", {})
            signed_urls = {}
            
            expiration = datetime.timedelta(hours=1)
            bucket = storage_client.bucket(OUTPUT_BUCKET)

            for key, gs_path in outputs.items():
                # gs_path is like gs://bucket/path/to/file
                if gs_path:
                    blob_name = "/".join(gs_path.split("/")[3:]) # remove gs://bucket/
                    blob = bucket.blob(blob_name)
                    url = blob.generate_signed_url(expiration=expiration, method="GET")
                    signed_urls[key] = url
            
            response["download_links"] = signed_urls

        elif status == "error":
            response["error"] = data.get("error_message")

        return response

    except Exception as e:
        print(f"❌ STATUS CHECK FAILED: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🚀 Starting PolySub Server...")
    print("👉 Open your browser at: http://127.0.0.1:8081")
    # RELOAD DISABLED to fix Windows sub-process output buffering issues
    uvicorn.run("main:app", host="127.0.0.1", port=8081, reload=False)