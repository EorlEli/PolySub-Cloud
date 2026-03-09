import type { Metadata } from "next"
import { ContactForm } from "@/components/marketing/contact-form"
import { Mail, MessageSquare } from "lucide-react"

export const metadata: Metadata = {
  title: "Contact",
  description:
    "Get in touch with the PolySub team. We're here to help with any questions or issues.",
}

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 md:py-24">
      <div className="mx-auto max-w-3xl">
        <div className="flex flex-col items-center text-center">
          <h1 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl text-balance">
            Get in touch
          </h1>
          <p className="mt-4 text-lg text-muted-foreground leading-relaxed text-pretty">
            {"Have a question or need help? We'd love to hear from you."}
          </p>
        </div>

        <div className="mt-12 grid gap-6 sm:grid-cols-2">
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <Mail className="h-5 w-5 text-primary" />
            </div>
            <h3 className="mt-4 font-semibold text-foreground">Email</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              hello@polysub.com
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <MessageSquare className="h-5 w-5 text-primary" />
            </div>
            <h3 className="mt-4 font-semibold text-foreground">
              Response Time
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              We typically respond within 24 hours
            </p>
          </div>
        </div>

        <div className="mt-12 rounded-xl border border-border bg-card p-6 md:p-8">
          <h2 className="mb-6 text-xl font-semibold text-foreground">
            Send us a message
          </h2>
          <ContactForm />
        </div>
      </div>
    </div>
  )
}
