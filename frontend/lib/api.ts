import type { ConversationInput } from "@/types/chat";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export interface GeneratedPdf {
  blob: Blob;
  filename: string;
}

interface ApiErrorBody {
  detail?: string | { code?: string; message?: string };
}

export async function generatePdf(input: ConversationInput): Promise<GeneratedPdf> {
  if (input.mode !== "link") {
    throw new Error("Paste-text generation is not supported by the MVP backend yet.");
  }

  const url = input.link?.trim();
  if (!url) {
    throw new Error("Add a shared conversation link first.");
  }

  const options = input.options
    ? {
        layout: input.options.layout,
        page_format: input.options.pageFormat,
        font_family: input.options.fontFamily,
        font_size: input.options.fontSize,
        line_spacing: input.options.lineSpacing,
        margin: input.options.margin,
        theme: input.options.theme,
        show_cover: input.options.showCover,
        show_headers: input.options.showHeaders,
      }
    : undefined;

  const response = await fetch(`${apiBaseUrl()}/api/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url, options }),
  });

  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }

  const blob = await response.blob();
  return {
    blob,
    filename: filenameFromDisposition(response.headers.get("Content-Disposition")),
  };
}

function apiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

async function errorMessage(response: Response) {
  try {
    const body = (await response.json()) as ApiErrorBody & { code?: string; message?: string };
    const code = (typeof body.detail === "object" ? body.detail?.code : body.code) ?? "";
    const rawMsg = (typeof body.detail === "string" ? body.detail : body.detail?.message || body.message) ?? "";

    if (code === "unsupported_platform") {
      return "This URL is not recognized. Please use a public share link from ChatGPT, Claude, Gemini, or Perplexity.";
    }
    if (code === "fetch_failed" || rawMsg.toLowerCase().includes("blocked unsafe")) {
      return "Could not access the shared chat. Please make sure the link is public and accessible.";
    }
    if (code === "rate_limited" || response.status === 429) {
      return "You're sending requests too quickly. Please wait a moment before trying again.";
    }
    if (code === "parser_failed") {
      return "Unable to parse this chat transcript. Please ensure the conversation contains visible messages.";
    }

    if (rawMsg) {
      return rawMsg;
    }
  } catch {
    // Fall through to generic status text.
  }

  if (response.status === 429) {
    return "Rate limit exceeded. Please wait a few moments and try again.";
  }
  if (response.status === 502) {
    return "Could not fetch the chat link. Please make sure it is a valid, publicly accessible share URL.";
  }

  return response.statusText || "PaperChat could not generate the PDF.";
}

function filenameFromDisposition(disposition: string | null) {
  if (!disposition) {
    return "paperchat-conversation.pdf";
  }

  const match = disposition.match(/filename="?([^"]+)"?/i);
  return match?.[1] ?? "paperchat-conversation.pdf";
}
