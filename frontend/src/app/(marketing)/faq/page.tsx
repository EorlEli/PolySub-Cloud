import type { Metadata } from "next"
import { FaqAccordion } from "@/components/marketing/faq-accordion"
import Link from "next/link"

export const metadata: Metadata = {
  title: "FAQ",
  description:
    "Frequently asked questions about PolySub's video subtitle processing service.",
}

export default function FaqPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 md:py-24">
      <div className="mx-auto max-w-2xl">
        <div className="flex flex-col items-center text-center">
          <h1 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl text-balance">
            Frequently Asked Questions
          </h1>
          <p className="mt-4 text-lg text-muted-foreground leading-relaxed text-pretty">
            Find answers to common questions about PolySub.
          </p>
        </div>

        <div className="mt-12">
          <FaqAccordion />
        </div>

        <div className="mt-12 text-center">
          <p className="text-muted-foreground">
            {"Still have questions? "}
            <Link
              href="/contact"
              className="text-primary underline-offset-4 hover:underline"
            >
              Contact us
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
