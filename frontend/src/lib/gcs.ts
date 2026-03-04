import { SignJWT, importPKCS8 } from "jose"

/**
 * GCS V4 Signed URL generation using jose for JWT signing.
 * No native dependencies required.
 */

async function createSignedUrl(
  bucket: string,
  objectName: string,
  method: "GET" | "PUT",
  expiresInSeconds: number,
  contentType?: string
): Promise<string> {
  const clientEmail = process.env.GCP_CLIENT_EMAIL!
  const privateKey = process.env.GCP_PRIVATE_KEY!.replace(/\\n/g, "\n")

  const now = Math.floor(Date.now() / 1000)
  const expiration = now + expiresInSeconds
  const datestamp = new Date().toISOString().replace(/[-:]/g, "").split(".")[0] + "Z"
  const dateOnly = datestamp.substring(0, 8)
  const credentialScope = `${dateOnly}/auto/storage/goog4_request`
  const credential = `${clientEmail}/${credentialScope}`

  const host = `${bucket}.storage.googleapis.com`
  const canonicalUri = `/${encodeURIComponent(objectName).replace(/%2F/g, "/")}`

  const queryParams: Record<string, string> = {
    "X-Goog-Algorithm": "GOOG4-RSA-SHA256",
    "X-Goog-Credential": credential,
    "X-Goog-Date": datestamp,
    "X-Goog-Expires": String(expiresInSeconds),
    "X-Goog-SignedHeaders": contentType ? "content-type;host" : "host",
  }

  const sortedParams = Object.keys(queryParams)
    .sort()
    .map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(queryParams[k])}`)
    .join("&")

  const canonicalHeaders = contentType
    ? `content-type:${contentType}\nhost:${host}\n`
    : `host:${host}\n`

  const signedHeaders = contentType ? "content-type;host" : "host"

  const canonicalRequest = [
    method,
    canonicalUri,
    sortedParams,
    canonicalHeaders,
    signedHeaders,
    "UNSIGNED-PAYLOAD",
  ].join("\n")

  // Hash the canonical request
  const encoder = new TextEncoder()
  const hashBuffer = await crypto.subtle.digest(
    "SHA-256",
    encoder.encode(canonicalRequest)
  )
  const hashedRequest = Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")

  const stringToSign = [
    "GOOG4-RSA-SHA256",
    datestamp,
    credentialScope,
    hashedRequest,
  ].join("\n")

  // Sign with jose
  const key = await importPKCS8(privateKey, "RS256")
  const signatureBuffer = await crypto.subtle.sign(
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    key as unknown as CryptoKey,
    encoder.encode(stringToSign)
  )

  // jose importPKCS8 returns a KeyLike, but we need the raw CryptoKey for subtle.sign
  // Use a different approach - sign via jose JWT then extract, or use the key directly
  // Actually, let's use a simpler approach with jose's SignJWT equivalent for raw signing
  // For GCS signed URLs, it's easiest to use the JSON API with an access token instead

  // Simpler approach: Use the JSON API with OAuth2 access token for signed URL generation
  const jwtToken = await new SignJWT({
    iss: clientEmail,
    sub: clientEmail,
    aud: "https://oauth2.googleapis.com/token",
    scope: "https://www.googleapis.com/auth/devstorage.full_control",
  })
    .setProtectedHeader({ alg: "RS256" })
    .setIssuedAt()
    .setExpirationTime("1h")
    .sign(key)

  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: jwtToken,
    }),
  })

  const tokenData = await tokenRes.json()
  if (!tokenRes.ok) throw new Error(`Token error: ${JSON.stringify(tokenData)}`)

  // Use the signBlob API to create the V4 signature
  const signRes = await fetch(
    `https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${clientEmail}:signBlob`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${tokenData.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        payload: Buffer.from(stringToSign).toString("base64"),
      }),
    }
  )

  const signData = await signRes.json()
  if (!signRes.ok) throw new Error(`Sign error: ${JSON.stringify(signData)}`)

  const signature = Buffer.from(signData.signedBlob, "base64")
    .toString("hex")

  return `https://${host}${canonicalUri}?${sortedParams}&X-Goog-Signature=${signature}`
}

/**
 * Generate a signed PUT URL for uploading a file to the input bucket.
 */
export async function generateUploadSignedUrl(
  fileName: string,
  contentType: string
): Promise<string> {
  const inputBucket = process.env.INPUT_BUCKET_NAME!
  return createSignedUrl(inputBucket, fileName, "PUT", 15 * 60, contentType)
}

/**
 * Generate a signed GET URL for downloading a file from a bucket.
 */
export async function generateDownloadSignedUrl(
  bucketName: string,
  filePath: string
): Promise<string> {
  return createSignedUrl(bucketName, filePath, "GET", 60 * 60)
}
