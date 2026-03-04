"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import {
  Card,
  CardContent,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { JobStatusBadge } from "@/components/app/job-status-badge"
import {
  FileVideo,
  Upload,
  ArrowRight,
  Clock,
  Coins,
} from "lucide-react"
import type { Job } from "@/lib/types"
import { SUPPORTED_LANGUAGES } from "@/lib/constants"
import { useAuth } from "@/contexts/AuthContext"
import { collection, query, where, orderBy, onSnapshot } from "firebase/firestore"
import { db } from "@/lib/firebase"

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, "0")}`
}

export default function JobsPage() {
  const { user } = useAuth()
  const [jobs, setJobs] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setIsLoading(false);
      return;
    }

    const q = query(
      collection(db, "jobs"),
      where("uid", "==", user.uid),
      orderBy("createdAt", "desc")
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const fetchedJobs = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setJobs(fetchedJobs);
      setIsLoading(false);
    }, (error) => {
      console.error("Error fetching jobs:", error);
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, [user]);


  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">My Jobs</h1>
          <p className="mt-1 text-muted-foreground">
            Track the status of your subtitle processing jobs.
          </p>
        </div>
        <Button asChild>
          <Link href="/upload">
            <Upload className="mr-2 h-4 w-4" />
            New Upload
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-lg" />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-16">
            <FileVideo className="h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-semibold text-foreground">
              No jobs yet
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Upload your first video to get started.
            </p>
            <Button className="mt-6" asChild>
              <Link href="/upload">Upload Video</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {jobs.map((job) => (
            <Link
              key={job.id}
              href={`/jobs/${job.id}`}
              className="group flex items-center justify-between rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent"
            >
              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                  <FileVideo className="h-5 w-5 text-muted-foreground" />
                </div>
                <div className="flex flex-col gap-1">
                  <p className="text-sm font-medium text-foreground">
                    {job.originalFilename || 'Unknown File'}
                  </p>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                    <span>
                      {SUPPORTED_LANGUAGES.find(
                        (l) => l.code === job.targetLanguage
                      )?.name || job.targetLanguage}
                    </span>
                    {job.durationSeconds && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDuration(job.durationSeconds)}
                      </span>
                    )}
                    {job.costCredits && (
                      <span className="flex items-center gap-1">
                        <Coins className="h-3 w-3" />
                        {job.costCredits} credits
                      </span>
                    )}
                    <span>
                      {new Date(job.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <JobStatusBadge status={job.status} />
                <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
