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
    const body = (await response.json()) as ApiErrorBody;
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (body.detail?.message) {
      return body.detail.message;
    }
  } catch {
    // Fall through to generic status text.
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
