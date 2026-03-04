import type { Metadata } from "next"
import { Cloud, Cpu, Globe } from "lucide-react"

export const metadata: Metadata = {
  title: "About",
  description:
    "Learn about PolySub and the technology behind our video subtitle processing service.",
}

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 md:py-24">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl text-balance">
          About PolySub
        </h1>
        <p className="mt-6 text-lg text-muted-foreground leading-relaxed">
          PolySub is a cloud-based video processing service that makes it
          easy to add professional subtitles to any video. We combine automatic
          speech recognition with powerful video encoding to deliver high-quality
          results in minutes.
        </p>

        <div className="mt-16 flex flex-col gap-12">
          <div className="flex gap-5">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10">
              <Cloud className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                Cloud-Native Architecture
              </h2>
              <p className="mt-2 text-muted-foreground leading-relaxed">
                Every video is processed on Google Cloud infrastructure using
                dedicated Cloud Run Jobs. This means consistent performance,
                automatic scaling, and the ability to handle videos of any size
                without impacting your local machine.
              </p>
            </div>
          </div>

          <div className="flex gap-5">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10">
              <Cpu className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                AI-Powered Transcription
              </h2>
              <p className="mt-2 text-muted-foreground leading-relaxed">
                We use state-of-the-art speech recognition models to
                automatically transcribe your video content and generate
                accurate subtitles. The system supports 24+ languages with high
                accuracy, even for accented or technical speech.
              </p>
            </div>
          </div>

          <div className="flex gap-5">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10">
              <Globe className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                Multi-Language Support
              </h2>
              <p className="mt-2 text-muted-foreground leading-relaxed">
                Whether you need subtitles in English, Japanese, Arabic, or any
                of our 24+ supported languages, PolySub has you covered.
                Perfect for content creators reaching global audiences,
                businesses with international teams, or anyone looking to make
                their videos more accessible.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-16 rounded-xl border border-border bg-card p-8">
          <h2 className="text-xl font-semibold text-foreground">Our Mission</h2>
          <p className="mt-3 text-muted-foreground leading-relaxed">
            We believe every video should be accessible to everyone, regardless
            of language or hearing ability. PolySub exists to make subtitle
            creation as simple and affordable as possible, so creators can focus
            on making great content while we handle the technical details.
          </p>
        </div>
      </div>
    </div>
  )
}
