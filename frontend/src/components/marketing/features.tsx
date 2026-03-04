import { Languages, Cloud, Download, Shield, Clock, FileText } from "lucide-react"

const features = [
  {
    icon: Languages,
    title: "24+ Languages",
    description:
      "Support for over 24 languages including English, Spanish, French, Japanese, Arabic, and many more.",
  },
  {
    icon: Cloud,
    title: "Cloud Processing",
    description:
      "Videos are processed on powerful cloud infrastructure. No local hardware required.",
  },
  {
    icon: Download,
    title: "Dual Output",
    description:
      "Get your video with burned-in subtitles and a separate WebVTT file for flexible use.",
  },
  {
    icon: Shield,
    title: "Secure Uploads",
    description:
      "Files are uploaded directly to secure cloud storage with signed URLs. Your content stays private.",
  },
  {
    icon: Clock,
    title: "Fast Turnaround",
    description:
      "Most videos are processed in minutes, not hours. Track progress in real-time from your dashboard.",
  },
  {
    icon: FileText,
    title: "Credit-Based Pricing",
    description:
      "Pay only for what you use. 1 credit = 1 minute of video. No subscriptions required.",
  },
]

export function Features() {
  return (
    <section className="border-t border-border bg-background py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-4">
        <div className="flex flex-col items-center text-center">
          <h2 className="text-3xl font-bold tracking-tight text-foreground md:text-4xl text-balance">
            Everything you need for video subtitles
          </h2>
          <p className="mt-4 max-w-2xl text-muted-foreground leading-relaxed text-pretty">
            A complete solution for adding professional subtitles to your videos
            in any language.
          </p>
        </div>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group rounded-xl border border-border bg-card p-6 transition-colors hover:border-primary/30 hover:bg-card/80"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <feature.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
