import { SignJWT, importPKCS8 } from "jose"

/**
 * Generate a Google OAuth2 access token using a service account JWT.
 */
async function getAccessToken(): Promise<string> {
  const clientEmail = process.env.GCP_CLIENT_EMAIL!
  const privateKey = process.env.GCP_PRIVATE_KEY!.replace(/\\n/g, "\n")
  const key = await importPKCS8(privateKey, "RS256")

  const jwt = await new SignJWT({
    iss: clientEmail,
    sub: clientEmail,
    aud: "https://oauth2.googleapis.com/token",
    scope: "https://www.googleapis.com/auth/cloud-platform",
  })
    .setProtectedHeader({ alg: "RS256" })
    .setIssuedAt()
    .setExpirationTime("1h")
    .sign(key)

  const res = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: jwt,
    }),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(`Token exchange failed: ${JSON.stringify(data)}`)
  return data.access_token
}

interface TriggerJobParams {
  jobId: string
  videoFilename: string
  targetLanguage: string
  outputBucket: string
}

/**
 * Triggers the Cloud Run Job with environment variable overrides
 * using the Cloud Run Admin REST API v2.
 */
export async function triggerProcessingJob(params: TriggerJobParams) {
  const { jobId, videoFilename, targetLanguage, outputBucket } = params

  const projectId = process.env.GCP_PROJECT_ID!
  const region = process.env.CLOUD_RUN_REGION || "us-central1"
  const jobName = process.env.CLOUD_RUN_JOB_NAME!

  const url = `https://run.googleapis.com/v2/projects/${projectId}/locations/${region}/jobs/${jobName}:run`

  const accessToken = await getAccessToken()

  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      overrides: {
        containerOverrides: [
          {
            env: [
              { name: "VIDEO_FILENAME", value: videoFilename },
              { name: "TARGET_LANGUAGE", value: targetLanguage },
              { name: "FIRESTORE_DOC_ID", value: jobId },
              { name: "OUTPUT_BUCKET", value: outputBucket },
            ],
          },
        ],
      },
    }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Cloud Run job trigger failed: ${response.status} ${error}`)
  }
}
