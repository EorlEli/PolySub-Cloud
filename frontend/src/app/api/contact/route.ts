import { NextResponse } from "next/server";
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(request: Request) {
    try {
        const { name, email, subject, message } = await request.json();

        if (!name || !email || !subject || !message) {
            return NextResponse.json(
                { error: "All fields are required." },
                { status: 400 }
            );
        }

        await resend.emails.send({
            from: "PolySub Contact Form <noreply@polysub.app>",
            to: "hello@polysub.app",
            replyTo: email,
            subject: `[Contact] ${subject}`,
            text: `Name: ${name}\nEmail: ${email}\n\n${message}`,
        });

        return NextResponse.json({ success: true });
    } catch (error: any) {
        console.error("Contact form error:", error);
        return NextResponse.json(
            { error: "Failed to send message. Please try again." },
            { status: 500 }
        );
    }
}
