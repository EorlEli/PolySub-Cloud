import * as admin from "firebase-admin";

if (!admin.apps.length) {
    admin.initializeApp({
        credential: admin.credential.cert({
            projectId: process.env.GCP_PROJECT_ID,
            clientEmail: process.env.GCP_CLIENT_EMAIL,
            privateKey: process.env.GCP_PRIVATE_KEY?.replace(/\\n/g, "\n"),
        }),
    });
}

export const adminDb = admin.firestore();
export const adminAuth = admin.auth();
