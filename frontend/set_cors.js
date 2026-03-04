const { Storage } = require('@google-cloud/storage');

const storage = new Storage({
    projectId: 'polysub',
    keyFilename: 'C:\\Users\\46760\\Downloads\\polysub-f9aa64b5d040.json'
});

async function setCors() {
    // CORS configuration to allow PUT requests from browsers
    const corsConfiguration = [
        {
            maxAgeSeconds: 3600,
            method: ['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS'],
            origin: ['*'], // Allowing all origins for ease of development; can restrict to actual domain later
            responseHeader: ['Content-Type', 'Access-Control-Allow-Origin', 'x-goog-resumable']
        }
    ];

    const buckets = ['polysub_input', 'polysub_output'];

    for (const bucketName of buckets) {
        try {
            const bucket = storage.bucket(bucketName);
            console.log(`Setting CORS config for ${bucketName} bucket...`);
            await bucket.setCorsConfiguration(corsConfiguration);
            console.log(`CORS for ${bucketName} bucket updated successfully!`);
        } catch (e) {
            console.error(`Failed to set CORS for ${bucketName}:`, e.message);
        }
    }
}

setCors().catch(console.error);
