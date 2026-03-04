import type { Metadata } from "next"
import { HowItWorks } from "@/components/marketing/how-it-works"

export const metadata: Metadata = {
  title: "How it Works",
  description:
    "Learn how PolySub works in three simple steps: upload your video, AI processing, and download your subtitled video.",
}

export default function HowItWorksPage() {
  return <HowItWorks />
}
