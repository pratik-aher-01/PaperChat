export type InputMode = "link" | "text";

export type ProviderId = "chatgpt" | "claude" | "gemini" | "perplexity";

export interface PdfSettings {
  pageFormat: "A4" | "Letter" | "Legal";
  layout: "single" | "two-column" | "auto";
  fontFamily: "inter" | "serif" | "mono" | "dyslexic";
  fontSize: "small" | "medium" | "large";
  lineSpacing: "compact" | "normal" | "relaxed";
  margin: "narrow" | "normal" | "wide";
  theme: "default" | "dark" | "academic" | "minimal";
  showCover: boolean;
  showHeaders: boolean;
}

export interface ConversationInput {
  mode: InputMode;
  provider: ProviderId;
  link?: string;
  rawText?: string;
  options?: PdfSettings;
}

export interface GeneratedDocumentState {
  filename: string;
  objectUrl: string;
  sourceUrl?: string;
}
