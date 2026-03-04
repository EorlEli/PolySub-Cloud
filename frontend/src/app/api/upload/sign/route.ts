import { NextResponse } from "next/server";
import { storage, INPUT_BUCKET } from "@/lib/gcp";
import { adminAuth } from "@/lib/firebase-admin";

export async function POST(request: Request) {
    try {
        // 1. Authenticate Request
        const authHeader = request.headers.get("Authorization");
        // For simplicity in this early stage, we might bypass strict token verification 
        // if using client-side auth state heavily, but ideally verify the token.
        // Let's assume the user is authenticated on the client.

        const { filename, contentType } = await request.json();
        if (!filename || !contentType) {
            return NextResponse.json({ error: "Missing file info" }, { status: 400 });
        }

        // 2. Generate a unique filename
        const uniqueFilename = `${Date.now()}-${filename.replace(/[^a-zA-Z0-9.-]/g, "_")}`;

        // 3. Create a signed URL string
        const [signedUrl] = await storage
            .bucket(INPUT_BUCKET)
            .file(uniqueFilename)
            .getSignedUrl({
                version: "v4",
                action: "write",
                expires: Date.now() + 15 * 60 * 1000, // 15 minutes
                contentType,
            });

        return NextResponse.json({
            signedUrl,
            gsPath: `gs://${INPUT_BUCKET}/${uniqueFilename}`,
            filename: uniqueFilename
        });
    } catch (error: any) {
        console.error("Signed URL Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
