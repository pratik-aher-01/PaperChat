export const SITE = {
  name: "PaperChat",
  description:
    "PaperChat restructures long AI chats into clean, topic-grouped, print-ready PDFs - searchable, skimmable, and built to read on paper.",
  github: "https://github.com",
} as const;

export const PROCESSING_STAGES = [
  { id: "reading", label: "Reading conversation", duration: 1800 },
  { id: "topics", label: "Grouping by topic", duration: 2400 },
  { id: "layout", label: "Designing document layout", duration: 2200 },
  { id: "render", label: "Rendering preview", duration: 1600 },
] as const;

export const DOCUMENT_SECTIONS = [
  { heading: "Conversation summary", lines: [92, 78, 86] },
  { heading: "Key concepts", lines: [88, 72, 80] },
  { heading: "Implementation notes", lines: [94, 84, 64] },
  { heading: "Revision checklist", lines: [76, 90, 70] },
] as const;

export function formatEstimatedTime(seconds: number) {
  if (seconds <= 0) return "Finishing up...";
  return `About ${Math.ceil(seconds)}s remaining`;
}
