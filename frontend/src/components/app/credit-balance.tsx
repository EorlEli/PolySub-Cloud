"use client"

import { Coins } from "lucide-react"

export function CreditBalance({ credits }: { credits: number | undefined }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-primary/10 px-3 py-1.5">
      <Coins className="h-4 w-4 text-primary" />
      <span className="text-sm font-semibold text-primary">
        {credits ?? 0} min
      </span>
    </div>
  )
}
