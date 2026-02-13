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
        doc_ref.update({"status": "processing", "worker_id": os.environ.get("HOSTNAME")})

        # 2. Download Video
        print(f"📥 Downloading {VIDEO_FILENAME} from {INPUT_BUCKET_NAME}...")
        bucket = storage_client.bucket(INPUT_BUCKET_NAME)
        blob = bucket.blob(VIDEO_FILENAME)
        
        local_video_path = f"temp_{VIDEO_FILENAME}"
        blob.download_to_filename(local_video_path)

        # 3. Process Video (Core Logic)
        print("⚙️ Running Core Processor...")
        result = process_video(local_video_path, TARGET_LANGUAGE)
        
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

        # Upload Zip
        zip_gs_path = upload_file(result["zip_path"], f"output/{result['zip_path']}")
        uploaded_files["zip_url"] = zip_gs_path
        
        # Upload Video (optional, maybe user just wants zip)
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

    except Exception as e:
        print(f"❌ Job Failed: {e}")
        doc_ref.update({
            "status": "error",
            "error_message": str(e)
        })
        sys.exit(1)

if __name__ == "__main__":
    # Check if necessary env vars are present
    if not all([INPUT_BUCKET_NAME, OUTPUT_BUCKET_NAME, VIDEO_FILENAME, FIRESTORE_DOC_ID]):
        print("❌ Missing required environment variables.")
        sys.exit(1)
    
    main()
