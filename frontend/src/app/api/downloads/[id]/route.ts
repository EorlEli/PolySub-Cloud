import { NextResponse } from "next/server";
import { storage, OUTPUT_BUCKET } from "@/lib/gcp";
import { adminDb } from "@/lib/firebase-admin";

export async function GET(request: Request, { params }: { params: { id: string } }) {
    try {
        const jobRef = await adminDb.collection("jobs").doc(params.id).get();

        if (!jobRef.exists) {
            return NextResponse.json({ error: "Job not found" }, { status: 404 });
        }

        const jobData = jobRef.data();
        if (jobData?.status !== "succeeded" && jobData?.status !== "done") {
            return NextResponse.json({ error: "Job not finished" }, { status: 400 });
        }

        const outputs = jobData?.outputs || {};
        console.log("Raw Outputs Dictionary:", outputs);
        const urls: { [key: string]: string | null } = {};

        const bucket = storage.bucket(OUTPUT_BUCKET);
        for (const [key, gsPath] of Object.entries(outputs)) {
            if (typeof gsPath === "string" && gsPath.startsWith("gs://")) {
                const parts = gsPath.split("/");
                const fileName = parts.slice(3).join("/"); // everything after bucket name

                try {
                    const [url] = await bucket.file(fileName).getSignedUrl({
                        version: "v4",
                        action: "read",
                        expires: Date.now() + 60 * 60 * 1000, // 1 hour
                    });
                    urls[key] = url;
                } catch (err) {
                    console.error("Error signing URL for", fileName, err);
                }
            }
        }

        return NextResponse.json({
            videoUrl: urls.video_url || urls.videoUrl || urls.video,
            vttUrl: urls.vtt_url || urls.vttUrl || urls.vtt
        });
    } catch (error: any) {
        console.error("Downloads Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
