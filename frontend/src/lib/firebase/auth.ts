import { cookies } from "next/headers"
import { verifySessionToken } from "./admin"
import { SESSION_COOKIE_NAME } from "../constants"

export async function verifySessionCookie(sessionCookie: string) {
  try {
    const claims = await verifySessionToken(sessionCookie)
    return claims
  } catch {
    return null
  }
}

export async function getCurrentUser() {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME)?.value

  if (!sessionCookie) return null

  return verifySessionCookie(sessionCookie)
}
