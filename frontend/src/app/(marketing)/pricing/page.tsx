import type { Metadata } from "next"
import { PricingCards } from "@/components/marketing/pricing-cards"

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "Simple credit-based pricing for video subtitle processing. Buy credits and use them whenever you need.",
}

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 md:py-24">
      <div className="flex flex-col items-center text-center">
        <h1 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl text-balance">
          Simple, transparent pricing
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-muted-foreground leading-relaxed text-pretty">
          Buy credits and use them whenever you need. 1 credit = 1 minute of
          video. No subscriptions, no hidden fees, no expiration.
        </p>
      </div>

      <div className="mt-16">
        <PricingCards />
      </div>
    </div>
  )
}
