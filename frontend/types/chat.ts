export type InputMode = "link" | "text";

export type ProviderId = "chatgpt" | "claude" | "gemini" | "perplexity";

export interface ConversationInput {
  mode: InputMode;
  provider: ProviderId;
  link?: string;
  rawText?: string;
}

export interface GeneratedDocumentState {
  filename: string;
  objectUrl: string;
  sourceUrl?: string;
}
