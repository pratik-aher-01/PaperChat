import type { GeneratedDocumentState, PdfSettings } from "@/types/chat";

export const INPUT_STORAGE_KEY = "paperchat:input";
export const DOCUMENT_STORAGE_KEY = "paperchat:generated-document";
export const SETTINGS_STORAGE_KEY = "paperchat:settings";

export function readGeneratedDocument(): GeneratedDocumentState | null {
  const raw = window.sessionStorage.getItem(DOCUMENT_STORAGE_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as GeneratedDocumentState;
  } catch {
    window.sessionStorage.removeItem(DOCUMENT_STORAGE_KEY);
    return null;
  }
}

export function writeGeneratedDocument(document: GeneratedDocumentState) {
  window.sessionStorage.setItem(DOCUMENT_STORAGE_KEY, JSON.stringify(document));
}

export function clearGeneratedDocument() {
  const current = readGeneratedDocument();
  if (current?.objectUrl) {
    URL.revokeObjectURL(current.objectUrl);
  }
  window.sessionStorage.removeItem(DOCUMENT_STORAGE_KEY);
}

export function readPdfSettings(): PdfSettings | null {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(SETTINGS_STORAGE_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as PdfSettings;
  } catch {
    window.sessionStorage.removeItem(SETTINGS_STORAGE_KEY);
    return null;
  }
}

export function writePdfSettings(settings: PdfSettings) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
}
