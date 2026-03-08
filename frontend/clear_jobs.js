const admin = require('firebase-admin');
const serviceAccount = require('C:\\Users\\46760\\Downloads\\polysub-f9aa64b5d040.json');

admin.initializeApp({
    credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function clearJobs() {
    console.log("Checking jobs collection for pending/processing jobs...");
    const jobsSnapshot = await db.collection('jobs').get();

    if (jobsSnapshot.empty) {
        console.log("No documents found in the 'jobs' collection.");
        return;
    }

    let updatedCount = 0;
    const batch = db.batch();

    jobsSnapshot.forEach(doc => {
        const data = doc.data();
        if (data.status === 'pending' || data.status === 'processing') {
            console.log(`Job ${doc.id} is stuck in '${data.status}'. Marking as FAILED.`);
            const docRef = db.collection('jobs').doc(doc.id);
            batch.update(docRef, {
                status: 'FAILED',
                error: 'Job manually canceled in Cloud Run.',
                errorMessage: 'Job manually canceled in Cloud Run.'
            });
            updatedCount++;
        }
    });

    if (updatedCount > 0) {
        await batch.commit();
        console.log(`Successfully updated ${updatedCount} jobs.`);
    } else {
        console.log("No pending or processing jobs found.");
    }
}

clearJobs().catch(console.error);
