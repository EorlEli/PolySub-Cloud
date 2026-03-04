const admin = require('firebase-admin');
const serviceAccount = require('C:\\Users\\46760\\Downloads\\polysub-f9aa64b5d040.json');

admin.initializeApp({
    credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function checkDb() {
    console.log("Checking users collection...");
    const usersSnapshot = await db.collection('users').get();
    if (usersSnapshot.empty) {
        console.log("No documents found in the 'users' collection.");
    } else {
        usersSnapshot.forEach(doc => {
            console.log(`User Document ID: ${doc.id}`);
            console.log(`Data:`, doc.data());
        });
    }

    console.log("\nChecking jobs collection...");
    const jobsSnapshot = await db.collection('jobs').get();
    if (jobsSnapshot.empty) {
        console.log("No documents found in the 'jobs' collection.");
    } else {
        console.log(`Found ${jobsSnapshot.size} jobs.`);
        const uids = new Set();
        jobsSnapshot.forEach(doc => {
            uids.add(doc.data().uid);
        });
        console.log("Unique UIDs in jobs collection:", Array.from(uids));
    }
}

checkDb().catch(console.error);
