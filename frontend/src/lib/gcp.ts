import { Storage } from "@google-cloud/storage";
import { JobsClient } from "@google-cloud/run";

const gcpOptions = {
    projectId: process.env.GCP_PROJECT_ID,
    credentials: {
        client_email: process.env.GCP_CLIENT_EMAIL,
        private_key: process.env.GCP_PRIVATE_KEY?.replace(/\\n/g, "\n"),
    },
};

export const storage = new Storage(gcpOptions);
export const runClient = new JobsClient(gcpOptions);

export const INPUT_BUCKET = process.env.INPUT_BUCKET_NAME!;
export const OUTPUT_BUCKET = process.env.OUTPUT_BUCKET_NAME!;
export const CLOUD_RUN_JOB_NAME = process.env.CLOUD_RUN_JOB_NAME!;
export const GCP_REGION = process.env.GCP_REGION || "europe-north1";
