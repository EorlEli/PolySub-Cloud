const { Storage } = require('@google-cloud/storage');
require('dotenv').config({ path: '.env.local' });

async function configureCors() {
    try {
        const storage = new Storage({
            projectId: process.env.GCP_PROJECT_ID,
            credentials: {
                client_email: process.env.GCP_CLIENT_EMAIL,
                private_key: process.env.GCP_PRIVATE_KEY.replace(/\\n/g, '\n'),
            },
        });

        const bucketName = process.env.INPUT_BUCKET_NAME || 'polysub_input';
        console.log(`Configuring CORS for bucket: ${bucketName}...`);

        const corsConfiguration = [
            {
                maxAgeSeconds: 3600,
                method: ['GET', 'PUT', 'HEAD', 'OPTIONS', 'POST'],
                origin: ['*'], // Allow requests from any origin (including Vercel/localhost)
                responseHeader: ['Content-Type', 'Authorization', 'x-goog-resumable'],
            },
        ];

        await storage.bucket(bucketName).setCorsConfiguration(corsConfiguration);

        console.log(`Successfully configured CORS for ${bucketName}`);
    } catch (error) {
        console.error('Failed to configure CORS:', error);
    }
}

configureCors();
