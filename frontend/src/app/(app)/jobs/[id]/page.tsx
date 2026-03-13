"use client"

import { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { JobStatusBadge } from "@/components/app/job-status-badge"
import {
  ArrowLeft,
  Download,
  FileVideo,
  FileText,
  Clock,
  Globe,
  Coins,
  AlertCircle,
  Loader2,
} from "lucide-react"
import { SUPPORTED_LANGUAGES } from "@/lib/constants"
import { toast } from "sonner"
import { doc, onSnapshot } from "firebase/firestore"
import { db } from "@/lib/firebase"

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, "0")}`
}

export default function JobDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const { id } = params
  const [isDownloading, setIsDownloading] = useState(false)
  const [job, setJob] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const docRef = doc(db, "jobs", id);
    const unsubscribe = onSnapshot(docRef, (snap) => {
      if (snap.exists()) {
        setJob({ id: snap.id, ...snap.data() });
      } else {
        setJob(null);
      }
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, [id])

  const handleDownload = async (type: 'video' | 'vtt') => {
    setIsDownloading(true)
    try {
      const res = await fetch(`/api/downloads/${id}`)
      if (!res.ok) throw new Error("Failed to get download URLs")
      const { videoUrl, vttUrl } = await res.json()

      if (type === 'video' && videoUrl) {
        window.open(videoUrl, "_blank")
      } else if (type === 'vtt' && vttUrl) {
        window.open(vttUrl, "_blank")
      } else {
        toast.error(`The requested ${type} file is not available for this job yet.`)
      }
    } catch {
      toast.error("Failed to generate download links. Please try again.")
    } finally {
      setIsDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl">
        <Skeleton className="mb-8 h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    )
  }

  if (!job) {
    return (
      <div className="mx-auto max-w-2xl">
        <Card>
          <CardContent className="flex flex-col items-center py-16">
            <AlertCircle className="h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-semibold text-foreground">
              Job not found
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              This job does not exist or you do not have access.
            </p>
            <Button className="mt-6" variant="outline" asChild>
              <Link href="/jobs">Back to Jobs</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const languageName =
    SUPPORTED_LANGUAGES.find((l) => l.code === job.targetLanguage)?.name ||
    job.targetLanguage

  return (
    <div className="mx-auto max-w-2xl">
      <Button variant="ghost" size="sm" className="mb-6" asChild>
        <Link href="/jobs">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Jobs
        </Link>
      </Button>

      <div className="flex flex-col gap-6">
        {/* Job info card */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex flex-col gap-1">
                <CardTitle className="text-xl">
                  {job.originalFilename || job.originalFileName}
                </CardTitle>
                <CardDescription>
                  Created{" "}
                  {new Date(job.createdAt).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </CardDescription>
              </div>
              <JobStatusBadge status={job.status} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex items-center gap-3">
                <Globe className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Language</p>
                  <p className="text-sm font-medium text-foreground">
                    {languageName}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Duration</p>
                  <p className="text-sm font-medium text-foreground">
                    {job.durationSeconds ? formatDuration(job.durationSeconds) : "N/A"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Coins className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">
                    Credits Used
                  </p>
                  <p className="text-sm font-medium text-foreground">
                    {job.costCredits || 0} minute
                    {job.costCredits !== 1 ? "s" : ""}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <FileVideo className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Job ID</p>
                  <p className="text-sm font-mono font-medium text-foreground truncate max-w-[200px]">
                    {job.id}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Processing status */}
        {job.status !== "done" && job.status !== "succeeded" && job.status !== "error" && job.status !== "FAILED" && (
          <Card className="border-primary/30">
            <CardContent className="flex items-center gap-4 py-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
              </div>
              <div>
                <p className="font-medium text-foreground">
                  {job.status === "pending"
                    ? "Job is queued for processing"
                    : "Processing your video..."}
                </p>
                <div className="mt-2 w-full max-w-md">
                  <StageProgress
                    status={job.status}
                    progress={job.progress}
                    burnVideo={job.burnVideo}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Success - Download */}
        {(job.status === "succeeded" || job.status === "done") && (
          <Card className="border-emerald-500/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Download className="h-5 w-5 text-emerald-500" />
                Download Results
              </CardTitle>
              <CardDescription>
                Your video has been processed successfully. Download your
                files below.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 sm:flex-row">
              {job.burnVideo !== false && (
                <Button
                  onClick={() => handleDownload('video')}
                  disabled={isDownloading}
                  className="flex-1"
                >
                  {isDownloading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <FileVideo className="mr-2 h-4 w-4" />
                  )}
                  Download Video
                </Button>
              )}
              <Button
                variant="outline"
                onClick={() => handleDownload('vtt')}
                disabled={isDownloading}
                className="flex-1"
              >
                {isDownloading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="mr-2 h-4 w-4" />
                )}
                Download WebVTT
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Failed */}
        {(job.status === "FAILED" || job.status === "error") && (
          <Card className="border-destructive/30">
            <CardContent className="flex items-start gap-4 py-6">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
              <div>
                <p className="font-medium text-foreground">Processing Failed</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {job.errorMessage || job.error ||
                    "An unexpected error occurred during processing. Your credits have been refunded."}
                </p>
                <Button className="mt-4" size="sm" asChild>
                  <Link href="/upload">Try Again</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

const PROCESSING_STAGES = [
  { key: "downloading", label: "Downloading" },
  { key: "transcribing", label: "Transcribing" },
  { key: "translating", label: "Translating" },
  { key: "matching", label: "Matching" },
  { key: "burning", label: "Burning subtitles" },
  { key: "uploading", label: "Uploading" },
] as const

type StageKey = typeof PROCESSING_STAGES[number]["key"]

function StageProgress({
  status,
  progress,
  burnVideo,
}: {
  status: string
  progress?: {
    stage?: StageKey
    stageCurrent?: number
    stageTotal?: number
  }
  burnVideo?: boolean
}) {
  if (status !== "pending" && status !== "processing") {
    return null
  }

  // Filter out burning stage if burnVideo is false
  const stages = burnVideo === false 
    ? PROCESSING_STAGES.filter(s => s.key !== "burning")
    : PROCESSING_STAGES

  const currentStage = progress?.stage
  const currentStageIndex = currentStage 
    ? stages.findIndex(s => s.key === currentStage)
    : -1

  // Get the display label for the current stage
  const currentStageInfo = currentStage 
    ? stages.find(s => s.key === currentStage)
    : null

  // Build the progress text
  let progressText = "Waiting to start..."
  if (status === "processing" && currentStageInfo) {
    progressText = currentStageInfo.label
    // Add block progress for matching stage
    if (currentStage === "matching" && progress?.stageCurrent && progress?.stageTotal) {
      progressText += ` (${progress.stageCurrent}/${progress.stageTotal})`
    }
    progressText += "..."
  }

  return (
    <div className="w-full space-y-3">
      {/* Stage indicator pills */}
      <div className="flex flex-wrap gap-1.5">
        {stages.map((stage, index) => {
          const isCompleted = currentStageIndex > index
          const isCurrent = currentStageIndex === index
          const isPending = currentStageIndex < index

          return (
            <div
              key={stage.key}
              className={`
                flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-colors
                ${isCompleted ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400" : ""}
                ${isCurrent ? "bg-primary/15 text-primary" : ""}
                ${isPending ? "bg-muted text-muted-foreground/60" : ""}
              `}
            >
              {isCompleted && (
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              )}
              {isCurrent && (
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
                </span>
              )}
              <span>{stage.label}</span>
              {/* Show block count for matching */}
              {isCurrent && stage.key === "matching" && progress?.stageCurrent && progress?.stageTotal && (
                <span className="text-[10px] opacity-70">
                  {progress.stageCurrent}/{progress.stageTotal}
                </span>
              )}
            </div>
          )
        })}
      </div>

      {/* Current stage description */}
      <p className="text-xs text-muted-foreground">{progressText}</p>
    </div>
  )
}
