import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

const faqs = [
  {
    question: "What video formats are supported?",
    answer:
      "We support MP4, MOV (QuickTime), WebM, and MKV formats. Maximum file size: 1GB for Starter and Pro plans, 2GB for Studio plan. Maximum duration: 1 hour for Starter and Pro plans, 2 hours for Studio plan.",
  },
  {
    question: "How does the credit system work?",
    answer:
      "1 credit equals 1 minute of video processing. Credits are deducted when you submit a video based on its duration (rounded up to the nearest minute). Credits never expire.",
  },
  {
    question: "What languages are supported?",
    answer:
      "We support 24+ languages including English, Spanish, French, German, Italian, Portuguese, Dutch, Russian, Japanese, Korean, Chinese (Simplified and Traditional), Arabic, Hindi, Turkish, Polish, Swedish, Danish, Finnish, Norwegian, Thai, Vietnamese, Indonesian, and Ukrainian.",
  },
  {
    question: "How long does processing take?",
    answer:
      "Processing time depends on the video length and current load. Most videos under 30 minutes are processed within 5-15 minutes. You can track progress in real-time from your dashboard.",
  },
  {
    question: "What do I get after processing?",
    answer:
      "You receive two files: (1) your original video with subtitles permanently burned in, and (2) a WebVTT (.vtt) subtitle file that you can use separately in video players or editing software.",
  },
  {
    question: "Are my videos secure?",
    answer:
      "Yes. Videos are uploaded directly to secure Google Cloud Storage using signed URLs. Only you have access to your files, and they are automatically deleted after 30 days.",
  },
  {
    question: "What happens if processing fails?",
    answer:
      "If processing fails for any reason, your credits are automatically refunded to your account. You can retry the job or contact our support team for help.",
  },
  {
    question: "Can I get a refund?",
    answer:
      "Credits are non-refundable once purchased. However, failed processing jobs are automatically credited back. If you encounter issues, please contact our support team.",
  },
]

export function FaqAccordion() {
  return (
    <Accordion type="single" collapsible className="w-full">
      {faqs.map((faq, index) => (
        <AccordionItem key={index} value={`item-${index}`}>
          <AccordionTrigger className="text-left text-foreground">
            {faq.question}
          </AccordionTrigger>
          <AccordionContent className="text-muted-foreground leading-relaxed">
            {faq.answer}
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}
