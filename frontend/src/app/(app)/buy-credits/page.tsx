"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Check, Coins, Loader2 } from "lucide-react"
import { CREDIT_PACKS } from "@/lib/constants"
import { cn } from "@/lib/utils"
import { toast } from "sonner"
import { useAuth } from "@/contexts/AuthContext"

const features = [
  "Burned-in subtitles",
  "WebVTT file export",
  "24+ languages",
  "Cloud processing",
  "Secure storage",
  "No expiration",
]

export default function BuyCreditsPage() {
  const [loadingPack, setLoadingPack] = useState<string | null>(null)
  const { credits, loading: isLoading } = useAuth()

  const handlePurchase = async (packId: string) => {
    setLoadingPack(packId)
    try {
      const res = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ packId }),
      })

      if (!res.ok) throw new Error("Failed to create checkout session")

      const { url } = await res.json()
      if (url) {
        window.location.href = url
      }
    } catch {
      toast.error("Failed to start checkout. Please try again.")
    } finally {
      setLoadingPack(null)
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Buy Credits</h1>
        <p className="mt-1 text-muted-foreground">
          Purchase processing credits. 1 credit = 1 minute of video.
        </p>
        <div className="mt-3 flex items-center gap-2">
          <Coins className="h-4 w-4 text-primary" />
          <span className="text-sm text-muted-foreground">
            Current balance:{" "}
          </span>
          {isLoading ? (
            <Skeleton className="h-5 w-16" />
          ) : (
            <span className="text-sm font-semibold text-foreground">
              {credits ?? 0} minutes
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {CREDIT_PACKS.map((pack) => (
          <div
            key={pack.id}
            className={cn(
              "relative flex flex-col rounded-xl border p-6",
              pack.popular
                ? "border-primary bg-card shadow-lg shadow-primary/10"
                : "border-border bg-card"
            )}
          >
            {pack.popular && (
              <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
                Most Popular
              </Badge>
            )}

            <div className="flex flex-col gap-1">
              <h3 className="text-lg font-semibold text-foreground">
                {pack.name}
              </h3>
              <p className="text-sm text-muted-foreground">
                {pack.credits} minutes of video
              </p>
            </div>

            <div className="mt-6 flex items-baseline gap-1">
              <span className="text-4xl font-bold text-foreground">
                ${(pack.priceUsd / 100).toFixed(0)}
              </span>
              <span className="text-sm text-muted-foreground">
                .{String(pack.priceUsd % 100).padStart(2, "0")}
              </span>
            </div>

            <p className="mt-1 text-xs text-muted-foreground">
              ${((pack.priceUsd / pack.credits) / 100).toFixed(2)} per minute
            </p>

            <ul className="mt-6 flex flex-col gap-3">
              {features.map((feature) => (
                <li
                  key={feature}
                  className="flex items-center gap-2 text-sm text-muted-foreground"
                >
                  <Check className="h-4 w-4 shrink-0 text-primary" />
                  {feature}
                </li>
              ))}
            </ul>

            <Button
              className="mt-8"
              variant={pack.popular ? "default" : "outline"}
              onClick={() => handlePurchase(pack.id)}
              disabled={loadingPack !== null}
            >
              {loadingPack === pack.id ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Buy {pack.name}
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}
