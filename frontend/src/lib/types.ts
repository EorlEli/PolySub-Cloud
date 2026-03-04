export type JobStatus = "UPLOADING" | "QUEUED" | "PROCESSING" | "SUCCEEDED" | "FAILED"

export interface Job {
  id: string
  uid: string
  status: JobStatus
  inputPath: string
  outputVideoPath?: string
  outputVttPath?: string
  targetLanguage: string
  originalFileName: string
  durationSeconds: number
  costCredits: number
  createdAt: string
  updatedAt: string
  errorMessage?: string
}

export interface UserProfile {
  email: string
  displayName?: string
  stripeCustomerId?: string
  creditBalanceMinutes: number
  createdAt: string
}

export interface CreditPack {
  id: string
  name: string
  credits: number
  priceUsd: number
  popular?: boolean
}

export interface SupportedLanguage {
  code: string
  name: string
}
