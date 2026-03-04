import { Upload, Cpu, Download } from "lucide-react"

const steps = [
  {
    icon: Upload,
    step: "1",
    title: "Upload & Select",
    description:
      "Drop your video and choose your target language.",
  },
  {
    icon: Cpu,
    step: "2",
    title: "AI Processing",
    description:
      "Our multi-stage engine generates and verifies your subtitles.",
  },
  {
    icon: Download,
    step: "3",
    title: "Download",
    description:
      "Get your video with burned-in captions and the VTT file.",
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="scroll-mt-16 border-t border-border bg-muted/30 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-4">
        <div className="flex flex-col items-center text-center">
          <h2 className="text-3xl font-bold tracking-tight text-foreground md:text-4xl text-balance">
            How it works
          </h2>
          <p className="mt-4 max-w-2xl text-muted-foreground leading-relaxed text-pretty">
            Three simple steps to get professional subtitles on your videos.
          </p>
        </div>

        <div className="mt-16 grid gap-8 md:grid-cols-3">
          {steps.map((step) => (
            <div key={step.step} className="flex flex-col items-center text-center">
              <div className="relative mb-6">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                  <step.icon className="h-7 w-7 text-primary" />
                </div>
                <span className="absolute -right-2 -top-2 flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                  {step.step}
                </span>
              </div>
              <h3 className="text-xl font-semibold text-foreground">
                {step.title}
              </h3>
              <p className="mt-3 max-w-sm text-sm text-muted-foreground leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
