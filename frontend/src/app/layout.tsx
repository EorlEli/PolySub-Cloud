import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { AuthProvider } from "@/contexts/AuthContext";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: {
        default: "PolySub - Burn Subtitles Into Any Video",
        template: "%s | PolySub",
    },
    description: "Upload your video, choose a language, and get it back with professional burned-in subtitles and a WebVTT file.",
};

export const viewport: Viewport = {
    themeColor: [
        { media: "(prefers-color-scheme: light)", color: "#f5f7fa" },
        { media: "(prefers-color-scheme: dark)", color: "#1a1d2e" },
    ],
    userScalable: true,
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className="antialiased min-h-screen bg-background text-foreground overflow-x-hidden transition-colors">
                <AuthProvider>
                    <ThemeProvider
                        attribute="class"
                        defaultTheme="dark"
                        enableSystem
                        disableTransitionOnChange
                    >
                        {children}
                        <Toaster richColors position="top-right" />
                    </ThemeProvider>
                </AuthProvider>
            </body>
        </html>
    );
}
