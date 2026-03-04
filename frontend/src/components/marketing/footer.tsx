import Link from "next/link"

const footerLinks = {
  Product: [
    { href: "/pricing", label: "Pricing" },
    { href: "/faq", label: "FAQ" },
    { href: "/dashboard", label: "Dashboard" },
  ],
  Company: [
    { href: "/about", label: "About" },
    { href: "/contact", label: "Contact" },
  ],
  Legal: [
    { href: "#", label: "Privacy Policy" },
    { href: "#", label: "Terms of Service" },
  ],
}

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-6xl px-4 py-12">
        <div className="flex flex-col gap-8 md:flex-row md:justify-between">
          <div className="flex flex-col gap-3">
            <Link
              href="/"
              className="flex items-center gap-2 font-semibold text-foreground"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
                PS
              </div>
              <span className="text-lg">PolySub</span>
            </Link>
            <p className="max-w-xs text-sm text-muted-foreground leading-relaxed">
              Professional subtitle burning for your videos. Fast cloud
              processing with 24+ languages supported.
            </p>
          </div>

          <div className="flex gap-12">
            {Object.entries(footerLinks).map(([category, links]) => (
              <div key={category} className="flex flex-col gap-3">
                <h4 className="text-sm font-semibold text-foreground">
                  {category}
                </h4>
                {links.map((link) => (
                  <Link
                    key={link.label}
                    href={link.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-12 border-t border-border pt-6">
          <p className="text-center text-sm text-muted-foreground">
            {`\u00A9 ${new Date().getFullYear()} PolySub. All rights reserved.`}
          </p>
        </div>
      </div>
    </footer>
  )
}
