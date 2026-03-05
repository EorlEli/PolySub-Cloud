import { NextResponse } from "next/server";
import { runClient, GCP_REGION, CLOUD_RUN_JOB_NAME, INPUT_BUCKET, OUTPUT_BUCKET } from "@/lib/gcp";
import { adminDb } from "@/lib/firebase-admin";

const COST_PER_MINUTE = 1; // Example: 1 credit = 1 minute

export async function POST(request: Request) {
    try {
        const { gsPath, targetLanguage, originalFilename, durationSeconds, uid } = await request.json();

        if (!gsPath || !targetLanguage || !uid) {
            return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
        }

        const costCredits = Math.ceil(durationSeconds / 60) * COST_PER_MINUTE;

        // 1. Create a Firestore Document for the Job
        const jobRef = adminDb.collection("jobs").doc();
        await jobRef.set({
            uid,
            gsPath,
            targetLanguage,
            originalFilename,
            durationSeconds,
            costCredits,
            status: "pending",
            createdAt: new Date(),
        });

        // Extract filename from gsPath
        const parts = gsPath.split("/");
        const videoFilename = parts[parts.length - 1];

        // 2. Trigger Cloud Run Job via REST API (bypassing gRPC override bugs)
        const { GoogleAuth } = await import("google-auth-library");
        const auth = new GoogleAuth({
            scopes: ["https://www.googleapis.com/auth/cloud-platform"],
            projectId: process.env.GCP_PROJECT_ID,
            credentials: {
                client_email: process.env.GCP_CLIENT_EMAIL,
                private_key: process.env.GCP_PRIVATE_KEY?.replace(/\\n/g, "\n"),
            },
        });
        const client = await auth.getClient();

        const projectId = process.env.GCP_PROJECT_ID || "polysub";
        const url = `https://run.googleapis.com/v2/projects/${projectId}/locations/${GCP_REGION}/jobs/${CLOUD_RUN_JOB_NAME}:run`;

        const res = await client.request({
            url,
            method: "POST",
            data: {
                overrides: {
                    containerOverrides: [
                        {
                            env: [
                                { name: "INPUT_BUCKET", value: INPUT_BUCKET },
                                { name: "OUTPUT_BUCKET", value: OUTPUT_BUCKET },
                                { name: "VIDEO_FILENAME", value: videoFilename },
                                { name: "FIRESTORE_DOC_ID", value: jobRef.id },
                                { name: "TARGET_LANGUAGE", value: targetLanguage },
                            ]
                        }
                    ]
                }
            }
        });

        const execution = res.data as any;

        return NextResponse.json({
            jobId: jobRef.id,
            executionName: execution.name,
        });
    } catch (error: any) {
        console.error("Job Creation Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
