/**
 * Firebase Admin replacement using REST APIs + jose for JWT signing.
 * No native dependencies required (no grpc, no firebase-admin).
 */
import { SignJWT, importPKCS8, jwtVerify, createRemoteJWKSet } from "jose"

// ── Access Token ───────────────────────────────────────────────
let _cachedToken: { token: string; expiresAt: number } | null = null

async function getAccessToken(): Promise<string> {
  if (_cachedToken && Date.now() < _cachedToken.expiresAt - 60_000) {
    return _cachedToken.token
  }

  const clientEmail = process.env.GCP_CLIENT_EMAIL!
  const privateKey = process.env.GCP_PRIVATE_KEY!.replace(/\\n/g, "\n")
  const key = await importPKCS8(privateKey, "RS256")

  const jwt = await new SignJWT({
    iss: clientEmail,
    sub: clientEmail,
    aud: "https://oauth2.googleapis.com/token",
    scope: [
      "https://www.googleapis.com/auth/datastore",
      "https://www.googleapis.com/auth/firebase",
      "https://www.googleapis.com/auth/identitytoolkit",
      "https://www.googleapis.com/auth/cloud-platform",
    ].join(" "),
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

  _cachedToken = {
    token: data.access_token,
    expiresAt: Date.now() + (data.expires_in ?? 3600) * 1000,
  }

  return data.access_token
}

// ── Auth (session cookie replacement using custom JWT) ─────────

const JWKS = createRemoteJWKSet(
  new URL(
    "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"
  )
)

/**
 * Verify a Firebase ID token.
 * Returns the decoded payload (with uid, email, etc).
 */
export async function verifyIdToken(
  idToken: string
): Promise<{ uid: string; email?: string; name?: string }> {
  const projectId = process.env.GCP_PROJECT_ID!

  const { payload } = await jwtVerify(idToken, JWKS, {
    issuer: `https://securetoken.google.com/${projectId}`,
    audience: projectId,
  })

  return {
    uid: payload.sub!,
    email: payload.email as string | undefined,
    name: payload.name as string | undefined,
  }
}

/**
 * Create a custom session token (signed JWT) for cookie-based auth.
 */
export async function createSessionCookie(
  idToken: string,
  expiresInDays: number
): Promise<string> {
  // First verify the ID token
  const user = await verifyIdToken(idToken)

  const clientEmail = process.env.GCP_CLIENT_EMAIL!
  const privateKey = process.env.GCP_PRIVATE_KEY!.replace(/\\n/g, "\n")
  const key = await importPKCS8(privateKey, "RS256")

  const sessionToken = await new SignJWT({
    uid: user.uid,
    email: user.email,
    name: user.name,
  })
    .setProtectedHeader({ alg: "RS256", typ: "JWT" })
    .setIssuedAt()
    .setExpirationTime(`${expiresInDays}d`)
    .setIssuer("polysub")
    .sign(key)

  return sessionToken
}

/**
 * Verify a session cookie (our custom JWT).
 */
export async function verifySessionToken(
  sessionToken: string
): Promise<{ uid: string; email?: string; name?: string }> {
  const privateKey = process.env.GCP_PRIVATE_KEY!.replace(/\\n/g, "\n")
  const key = await importPKCS8(privateKey, "RS256")

  // For verification we need the public key, but since we signed it ourselves
  // we can derive the public key from the private key
  const { payload } = await jwtVerify(sessionToken, key, {
    issuer: "polysub",
  })

  return {
    uid: payload.uid as string,
    email: payload.email as string | undefined,
    name: payload.name as string | undefined,
  }
}

// ── Firestore REST API ─────────────────────────────────────────

const firestoreBaseUrl = () =>
  `https://firestore.googleapis.com/v1/projects/${process.env.GCP_PROJECT_ID}/databases/(default)/documents`

interface FirestoreDocument {
  name?: string
  fields?: Record<string, FirestoreValue>
  createTime?: string
  updateTime?: string
}

type FirestoreValue =
  | { stringValue: string }
  | { integerValue: string }
  | { doubleValue: number }
  | { booleanValue: boolean }
  | { timestampValue: string }
  | { nullValue: null }
  | { mapValue: { fields: Record<string, FirestoreValue> } }
  | { arrayValue: { values: FirestoreValue[] } }

// Helper to convert JS values to Firestore format
function toFirestoreValue(val: unknown): FirestoreValue {
  if (val === null || val === undefined) return { nullValue: null }
  if (typeof val === "string") return { stringValue: val }
  if (typeof val === "number") {
    return Number.isInteger(val)
      ? { integerValue: String(val) }
      : { doubleValue: val }
  }
  if (typeof val === "boolean") return { booleanValue: val }
  if (val instanceof Date) return { timestampValue: val.toISOString() }
  if (Array.isArray(val))
    return { arrayValue: { values: val.map(toFirestoreValue) } }
  if (typeof val === "object")
    return {
      mapValue: {
        fields: Object.fromEntries(
          Object.entries(val as Record<string, unknown>).map(([k, v]) => [
            k,
            toFirestoreValue(v),
          ])
        ),
      },
    }
  return { stringValue: String(val) }
}

// Helper to convert Firestore values to JS
function fromFirestoreValue(val: FirestoreValue): unknown {
  if ("stringValue" in val) return val.stringValue
  if ("integerValue" in val) return parseInt(val.integerValue, 10)
  if ("doubleValue" in val) return val.doubleValue
  if ("booleanValue" in val) return val.booleanValue
  if ("timestampValue" in val) return val.timestampValue
  if ("nullValue" in val) return null
  if ("mapValue" in val) return fromFirestoreDoc({ fields: val.mapValue.fields })
  if ("arrayValue" in val)
    return (val.arrayValue.values || []).map(fromFirestoreValue)
  return null
}

function fromFirestoreDoc(
  doc: { fields?: Record<string, FirestoreValue> } | null
): Record<string, unknown> | null {
  if (!doc?.fields) return null
  const result: Record<string, unknown> = {}
  for (const [key, val] of Object.entries(doc.fields)) {
    result[key] = fromFirestoreValue(val)
  }
  return result
}

export const firestore = {
  /**
   * Get a single document.
   */
  async getDoc(
    collection: string,
    docId: string
  ): Promise<{ exists: boolean; data: Record<string, unknown> | null; id: string }> {
    const token = await getAccessToken()
    const res = await fetch(
      `${firestoreBaseUrl()}/${collection}/${docId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    )

    if (res.status === 404) return { exists: false, data: null, id: docId }
    if (!res.ok) throw new Error(`Firestore GET failed: ${res.status}`)

    const doc: FirestoreDocument = await res.json()
    return { exists: true, data: fromFirestoreDoc(doc), id: docId }
  },

  /**
   * Create or overwrite a document.
   */
  async setDoc(
    collection: string,
    docId: string,
    data: Record<string, unknown>
  ): Promise<void> {
    const token = await getAccessToken()
    const fields: Record<string, FirestoreValue> = {}
    for (const [key, val] of Object.entries(data)) {
      fields[key] = toFirestoreValue(val)
    }

    const res = await fetch(
      `${firestoreBaseUrl()}/${collection}/${docId}`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ fields }),
      }
    )

    if (!res.ok) {
      const text = await res.text()
      throw new Error(`Firestore SET failed: ${res.status} ${text}`)
    }
  },

  /**
   * Update specific fields on a document.
   */
  async updateDoc(
    collection: string,
    docId: string,
    data: Record<string, unknown>
  ): Promise<void> {
    const token = await getAccessToken()
    const fields: Record<string, FirestoreValue> = {}
    for (const [key, val] of Object.entries(data)) {
      fields[key] = toFirestoreValue(val)
    }

    const fieldMask = Object.keys(data)
      .map((k) => `updateMask.fieldPaths=${k}`)
      .join("&")

    const res = await fetch(
      `${firestoreBaseUrl()}/${collection}/${docId}?${fieldMask}`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ fields }),
      }
    )

    if (!res.ok) {
      const text = await res.text()
      throw new Error(`Firestore UPDATE failed: ${res.status} ${text}`)
    }
  },

  /**
   * Query documents in a collection with ordering and filtering by field.
   */
  async query(
    collection: string,
    filters: Array<{
      field: string
      op: "EQUAL" | "LESS_THAN" | "GREATER_THAN"
      value: unknown
    }>,
    orderBy?: { field: string; direction?: "ASCENDING" | "DESCENDING" },
    limit?: number
  ): Promise<Array<{ id: string; data: Record<string, unknown> }>> {
    const token = await getAccessToken()
    const projectId = process.env.GCP_PROJECT_ID!

    const structuredQuery: Record<string, unknown> = {
      from: [{ collectionId: collection }],
    }

    if (filters.length > 0) {
      structuredQuery.where = {
        compositeFilter: {
          op: "AND",
          filters: filters.map((f) => ({
            fieldFilter: {
              field: { fieldPath: f.field },
              op: f.op,
              value: toFirestoreValue(f.value),
            },
          })),
        },
      }
    }

    if (orderBy) {
      structuredQuery.orderBy = [
        {
          field: { fieldPath: orderBy.field },
          direction: orderBy.direction || "DESCENDING",
        },
      ]
    }

    if (limit) {
      structuredQuery.limit = limit
    }

    const res = await fetch(
      `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents:runQuery`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ structuredQuery }),
      }
    )

    if (!res.ok) {
      const text = await res.text()
      throw new Error(`Firestore QUERY failed: ${res.status} ${text}`)
    }

    const results = await res.json()

    return (results as Array<{ document?: FirestoreDocument }>)
      .filter((r) => r.document)
      .map((r) => {
        const docName = r.document!.name!
        const id = docName.split("/").pop()!
        return { id, data: fromFirestoreDoc(r.document!) || {} }
      })
  },

  /**
   * Increment a numeric field atomically using Firestore commit with transform.
   */
  async incrementField(
    collection: string,
    docId: string,
    field: string,
    amount: number
  ): Promise<void> {
    const token = await getAccessToken()
    const projectId = process.env.GCP_PROJECT_ID!
    const docPath = `projects/${projectId}/databases/(default)/documents/${collection}/${docId}`

    const res = await fetch(
      `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents:commit`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          writes: [
            {
              transform: {
                document: docPath,
                fieldTransforms: [
                  {
                    fieldPath: field,
                    increment: { integerValue: String(amount) },
                  },
                ],
              },
            },
          ],
        }),
      }
    )

    if (!res.ok) {
      const text = await res.text()
      throw new Error(`Firestore INCREMENT failed: ${res.status} ${text}`)
    }
  },
}
