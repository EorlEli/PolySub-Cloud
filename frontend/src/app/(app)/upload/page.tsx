"use client"

import { useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import {
  Upload,
  FileVideo,
  X,
  Loader2,
  AlertCircle,
  Coins,
} from "lucide-react"
import { toast } from "sonner"
import {
  SUPPORTED_LANGUAGES,
  ACCEPTED_VIDEO_TYPES,
  MAX_FILE_SIZE_BYTES,
} from "@/lib/constants"
import { useAuth } from "@/contexts/AuthContext"

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, "0")}`
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [duration, setDuration] = useState<number>(0)
  const [language, setLanguage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  const { user, credits = 0 } = useAuth()
  const costCredits = duration > 0 ? Math.ceil(duration / 60) : 0
  const hasEnoughCredits =
    process.env.NODE_ENV === "development" ? true : credits >= costCredits

  const handleFileSelect = useCallback(
    (selectedFile: File) => {
      if (!ACCEPTED_VIDEO_TYPES.includes(selectedFile.type)) {
        toast.error("Unsupported file format. Please use MP4, MOV, AVI, WebM, or MKV.")
        return
      }
      if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
        toast.error("File is too large. Maximum size is 2GB.")
        return
      }

      setFile(selectedFile)

      // Extract duration via HTML5 video element
      const video = document.createElement("video")
      video.preload = "metadata"
      video.onloadedmetadata = () => {
        window.URL.revokeObjectURL(video.src)
        setDuration(video.duration)
      }
      video.onerror = () => {
        window.URL.revokeObjectURL(video.src)
        toast.error("Could not read video metadata. Please try another file.")
        setFile(null)
      }
      video.src = URL.createObjectURL(selectedFile)
    },
    []
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile) handleFileSelect(droppedFile)
    },
    [handleFileSelect]
  )

  const handleSubmit = async () => {
    if (!file || !language || !duration || !user) return

    setIsSubmitting(true)
    setUploadProgress(0)

    try {
      // 1. Get Signed URL from our backend
      const signRes = await fetch("/api/upload/sign", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename: file.name,
          contentType: file.type,
        }),
      });

      if (!signRes.ok) throw new Error("Failed to get upload URL");
      const { signedUrl, gsPath } = await signRes.json();

      // 2. Upload file directly to GCS using XMLHttpRequest for progress
      const xhr = new XMLHttpRequest()

      await new Promise<void>((resolve, reject) => {
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            setUploadProgress(Math.round((e.loaded / e.total) * 100))
          }
        })

        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve()
          } else {
            reject(new Error(`Upload failed with status ${xhr.status}`))
          }
        })

        xhr.addEventListener("error", () => {
          reject(new Error("Upload failed"))
        })

        xhr.open("PUT", signedUrl)
        xhr.setRequestHeader("Content-Type", file.type)
        xhr.send(file)
      })

      // 3. Inform Backend to start the Job
      const createRes = await fetch("/api/jobs/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          gsPath,
          targetLanguage: language,
          originalFilename: file.name,
          durationSeconds: Math.ceil(duration),
          uid: user.uid,
        }),
      });

      if (!createRes.ok) throw new Error("Failed to create job");
      const { jobId } = await createRes.json();

      toast.success("Video uploaded! Processing will begin shortly.")
      router.push(`/jobs/${jobId}`)
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : "Something went wrong"
      toast.error(message)
    } finally {
      setIsSubmitting(false)
      setUploadProgress(0)
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Upload Video</h1>
        <p className="mt-1 text-muted-foreground">
          Select a video file and choose a subtitle language.
        </p>
      </div>

      <div className="flex flex-col gap-6">
        {/* File picker */}
        <Card>
          <CardHeader>
            <CardTitle>Video File</CardTitle>
            <CardDescription>
              Supported formats: MP4, MOV, AVI, WebM, MKV. Maximum size: 2GB.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {file ? (
              <div className="flex items-center justify-between rounded-lg border border-border bg-muted/50 p-4">
                <div className="flex items-center gap-3">
                  <FileVideo className="h-8 w-8 text-primary" />
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.size)}
                      {duration > 0 && ` \u00B7 ${formatDuration(duration)}`}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    setFile(null)
                    setDuration(0)
                  }}
                  aria-label="Remove file"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div
                className="flex cursor-pointer flex-col items-center gap-3 rounded-lg border-2 border-dashed border-border p-10 transition-colors hover:border-primary/50 hover:bg-muted/30"
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    fileInputRef.current?.click()
                  }
                }}
              >
                <Upload className="h-8 w-8 text-muted-foreground" />
                <div className="text-center">
                  <p className="text-sm font-medium text-foreground">
                    Drop your video here or click to browse
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    MP4, MOV, AVI, WebM, MKV up to 2GB
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) handleFileSelect(f)
                  }}
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Language selector */}
        <Card>
          <CardHeader>
            <CardTitle>Subtitle Language</CardTitle>
            <CardDescription>
              Choose the language for your subtitles.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-2">
              <Label htmlFor="language" className="sr-only">
                Language
              </Label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger id="language">
                  <SelectValue placeholder="Select a language" />
                </SelectTrigger>
                <SelectContent>
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      {lang.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Cost estimate */}
        {file && duration > 0 && language && (
          <Card
            className={
              hasEnoughCredits
                ? "border-primary/30"
                : "border-destructive/30"
            }
          >
            <CardContent className="flex items-center justify-between py-4">
              <div className="flex items-center gap-3">
                {hasEnoughCredits ? (
                  <Coins className="h-5 w-5 text-primary" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-destructive" />
                )}
                <div>
                  <p className="text-sm font-medium text-foreground">
                    Cost: {costCredits} credit{costCredits !== 1 ? "s" : ""}{" "}
                    ({costCredits} min)
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Your balance: {credits} minutes
                  </p>
                </div>
              </div>
              {!hasEnoughCredits && (
                <Button size="sm" variant="outline" asChild>
                  <a href="/buy-credits">Buy Credits</a>
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* Upload progress */}
        {isSubmitting && uploadProgress > 0 && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Uploading...</span>
              <span className="font-medium text-foreground">
                {uploadProgress}%
              </span>
            </div>
            <Progress value={uploadProgress} />
          </div>
        )}

        {/* Submit */}
        <Button
          size="lg"
          disabled={
            !file || !language || !duration || !hasEnoughCredits || isSubmitting
          }
          onClick={handleSubmit}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {uploadProgress > 0 ? "Uploading..." : "Creating job..."}
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Start Processing
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
