import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check } from "lucide-react"
import { CREDIT_PACKS } from "@/lib/constants"
import { cn } from "@/lib/utils"

const features = [
  "Burned-in subtitles",
  "WebVTT file export",
  "24+ languages",
  "Cloud processing",
  "Secure file storage",
  "No expiration",
]

export function PricingCards() {
  return (
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
            <span className="text-sm text-muted-foreground">.{String(pack.priceUsd % 100).padStart(2, "0")}</span>
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
            asChild
          >
            <Link href="/signup">Buy {pack.name}</Link>
          </Button>
        </div>
      ))}
    </div>
  )
}
