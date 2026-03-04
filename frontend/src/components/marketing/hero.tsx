import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Zap } from "lucide-react"

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Subtle gradient background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,var(--color-primary)/0.08,transparent_60%)]" />

      <div className="relative mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl items-center justify-center px-4">
        <div className="flex flex-col items-center text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-secondary/50 px-4 py-1.5 text-sm text-muted-foreground">
            <Zap className="h-3.5 w-3.5 text-primary" />
            <span>Cloud-powered video processing</span>
          </div>

          <h1 className="max-w-4xl text-balance text-4xl font-bold tracking-tight text-foreground md:text-6xl lg:text-7xl">
            Human-Level Accuracy Subtitles,{" "}
            <span className="text-primary">Powered by Multi-Stage AI</span>
          </h1>

          <p className="mt-6 max-w-2xl text-pretty text-lg text-muted-foreground leading-relaxed">
            Generate professional SRT/VTT files or burn high-quality captions
            directly into your video in minutes. Optimized for the world{"'"}s
            major languages with context-aware verification.
          </p>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <Button size="lg" asChild>
              <Link href="/signup">
                Generate Subtitles Now!
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>


        </div>
      </div>
    </section>
  )
}
