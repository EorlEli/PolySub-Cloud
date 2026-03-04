import { Badge } from "@/components/ui/badge"
import type { JobStatus } from "@/lib/types"
import { cn } from "@/lib/utils"

const statusConfig: Record<
  JobStatus,
  { label: string; className: string }
> = {
  UPLOADING: {
    label: "Uploading",
    className: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  },
  QUEUED: {
    label: "Queued",
    className: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20",
  },
  PROCESSING: {
    label: "Processing",
    className: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  },
  SUCCEEDED: {
    label: "Completed",
    className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  },
  FAILED: {
    label: "Failed",
    className: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
  },
}

export function JobStatusBadge({ status }: { status: JobStatus }) {
  const config = statusConfig[status] || {
    label: status || "Unknown",
    className: "bg-muted text-muted-foreground border-muted",
  }

  return (
    <Badge variant="outline" className={cn("font-medium", config.className)}>
      {config.label}
    </Badge>
  )
}
