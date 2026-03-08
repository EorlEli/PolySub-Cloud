import os
import sys
from google.cloud import storage
from google.cloud import firestore
from core_processor import process_video

# Configurations from Environment Variables
INPUT_BUCKET_NAME = os.environ.get("INPUT_BUCKET")
OUTPUT_BUCKET_NAME = os.environ.get("OUTPUT_BUCKET")
VIDEO_FILENAME = os.environ.get("VIDEO_FILENAME") # The file within the bucket
FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION", "jobs")
FIRESTORE_DOC_ID = os.environ.get("FIRESTORE_DOC_ID")
TARGET_LANGUAGE = os.environ.get("TARGET_LANGUAGE", "Portuguese")
SOURCE_LANGUAGE = os.environ.get("SOURCE_LANGUAGE")
SUBTITLE_COLOR = os.environ.get("SUBTITLE_COLOR") # E.g., &H00FFFFFF&
BURN_VIDEO = os.environ.get("BURN_VIDEO", "true").lower() == "true"

def main():
    print(f"🚀 CLOUD WORKER STARTED for {VIDEO_FILENAME}")
    
    # Initialize Clients
    try:
        storage_client = storage.Client()
        firestore_client = firestore.Client()
    except Exception as e:
        print(f"❌ Failed to initialize Cloud Clients: {e}")
        # If we can't even connect to Firestore, we probably can't report failure easily.
        # But we should try to exit non-zero.
        sys.exit(1)

    doc_ref = firestore_client.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOC_ID)

    try:
        # 1. Update Status to Processing
        # Use set(merge=True) so it creates the document if it doesn't exist (e.g. manual testing)
        doc_ref.set({"status": "processing", "worker_id": os.environ.get("HOSTNAME")}, merge=True)

        # 2. Download Video
        print(f"📥 Downloading {VIDEO_FILENAME} from {INPUT_BUCKET_NAME}...")
        bucket = storage_client.bucket(INPUT_BUCKET_NAME)
        blob = bucket.blob(VIDEO_FILENAME)
        
        local_video_path = f"temp_{VIDEO_FILENAME}"
        blob.download_to_filename(local_video_path)

        # 3. Process Video (Core Logic)
        print("⚙️ Running Core Processor...")
        result = process_video(
            local_video_path,
            TARGET_LANGUAGE,
            source_language=SOURCE_LANGUAGE,
            subtitle_color=SUBTITLE_COLOR,
            burn_video=BURN_VIDEO,
            create_zip=False
        )
        
        # 4. Upload Results
        print("📤 Uploading Results...")
        output_bucket = storage_client.bucket(OUTPUT_BUCKET_NAME)
        
        uploaded_files = {}
        
        # Helper to upload
        def upload_file(local_path, destination_blob_name):
            if local_path and os.path.exists(local_path):
                b = output_bucket.blob(destination_blob_name)
                b.upload_from_filename(local_path)
                return f"gs://{OUTPUT_BUCKET_NAME}/{destination_blob_name}"
            return None

        # Upload VTT
        if result.get("output_vtt_path"):
            vtt_name = f"{VIDEO_FILENAME}_{TARGET_LANGUAGE}.vtt"
            vtt_gs_path = upload_file(result["output_vtt_path"], f"output/{vtt_name}")
            uploaded_files["vtt_url"] = vtt_gs_path

        # Upload Video
        if result.get("output_video_path"):
             vid_name = os.path.basename(result["output_video_path"])
             vid_gs_path = upload_file(result["output_video_path"], f"output/{vid_name}")
             uploaded_files["video_url"] = vid_gs_path

        # 5. Update Firestore Success
        doc_ref.update({
            "status": "done",
            "metadata": result["metadata"],
            "outputs": uploaded_files
        })
        
        print("✅ Job Completed Successfully.")

        # 6. Cleanup Input File (Privacy/Cost)
        try:
            print(f"🗑️ Deleting input file {VIDEO_FILENAME} from {INPUT_BUCKET_NAME}...")
            bucket.blob(VIDEO_FILENAME).delete()
            print("✅ Input file deleted.")
        except Exception as e:
            print(f"⚠️ Failed to delete input file: {e}")

    except Exception as e:
        print(f"❌ Job Failed: {e}")
        doc_ref.update({
            "status": "error",
            "error_message": str(e)
        })
        sys.exit(1)

if __name__ == "__main__":
    # Check if necessary env vars are present (Removed FIRESTORE_DOC_ID from check)
    if not all([INPUT_BUCKET_NAME, OUTPUT_BUCKET_NAME, VIDEO_FILENAME]):
        print(f"❌ Missing required environment variables.")
        print(f"Input: {INPUT_BUCKET_NAME}, Output: {OUTPUT_BUCKET_NAME}, File: {VIDEO_FILENAME}")
        sys.exit(1)
    
    main()
