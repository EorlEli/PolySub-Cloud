"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { JobStatusBadge } from "@/components/app/job-status-badge"
import {
  Coins,
  Upload,
  ListVideo,
  ArrowRight,
  FileVideo,
} from "lucide-react"
import { SUPPORTED_LANGUAGES } from "@/lib/constants"
import { useAuth } from "@/contexts/AuthContext"
import { collection, query, where, orderBy, onSnapshot } from "firebase/firestore"
import { db } from "@/lib/firebase"

export default function DashboardPage() {
  const { user, credits, loading: userLoading } = useAuth()
  const [jobsData, setJobsData] = useState<any[]>([])
  const [jobsLoading, setJobsLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setJobsLoading(false);
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
      setJobsData(fetchedJobs);
      setJobsLoading(false);
    }, (error) => {
      console.error("Error fetching jobs:", error);
      setJobsLoading(false);
    });

    return () => unsubscribe();
  }, [user]);

  const recentJobs = jobsData.slice(0, 5)

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="mt-1 text-muted-foreground">
          Welcome back. Here is an overview of your account.
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Credit Balance
            </CardTitle>
            <Coins className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {userLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <p className="text-3xl font-bold text-foreground">
                {credits ?? 0}
                <span className="ml-1 text-sm font-normal text-muted-foreground">
                  minutes
                </span>
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Jobs
            </CardTitle>
            <ListVideo className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {jobsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <p className="text-3xl font-bold text-foreground">
                {jobsData.length ?? 0}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Completed
            </CardTitle>
            <FileVideo className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {jobsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <p className="text-3xl font-bold text-foreground">
                {jobsData.filter(
                  (j: any) => j.status === "done" || j.status === "succeeded"
                ).length ?? 0}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Card className="flex flex-col justify-between">
          <CardHeader>
            <CardTitle>Upload a Video</CardTitle>
            <CardDescription>
              Start a new subtitle job by uploading your video.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/upload">
                <Upload className="mr-2 h-4 w-4" />
                Upload Video
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="flex flex-col justify-between">
          <CardHeader>
            <CardTitle>Buy Credits</CardTitle>
            <CardDescription>
              Purchase more processing minutes for your videos.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" asChild>
              <Link href="/buy-credits">
                <Coins className="mr-2 h-4 w-4" />
                Buy Credits
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Recent jobs */}
      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">
            Recent Jobs
          </h2>
          {recentJobs.length > 0 && (
            <Button variant="ghost" size="sm" asChild>
              <Link href="/jobs">
                View all
                <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </Button>
          )}
        </div>

        {jobsLoading ? (
          <div className="mt-4 flex flex-col gap-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </div>
        ) : recentJobs.length === 0 ? (
          <Card className="mt-4">
            <CardContent className="flex flex-col items-center py-10">
              <FileVideo className="h-10 w-10 text-muted-foreground/50" />
              <p className="mt-3 text-sm text-muted-foreground">
                No jobs yet. Upload your first video to get started.
              </p>
              <Button className="mt-4" size="sm" asChild>
                <Link href="/upload">Upload Video</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="mt-4 flex flex-col gap-2">
            {recentJobs.map((job) => (
              <Link
                key={job.id}
                href={`/jobs/${job.id}`}
                className="flex items-center justify-between rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent"
              >
                <div className="flex flex-col gap-1">
                  <p className="text-sm font-medium text-foreground">
                    {job.originalFilename || 'Unknown File'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {SUPPORTED_LANGUAGES.find(
                      (l) => l.code === job.targetLanguage
                    )?.name || job.targetLanguage}{" "}
                    &middot;{" "}
                    {new Date(job.createdAt).toLocaleDateString()}
                  </p>
                </div>
                <JobStatusBadge status={job.status} />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
