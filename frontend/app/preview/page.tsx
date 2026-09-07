"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

import { PdfPreview } from "@/components/preview/pdf-preview";
import { PreviewToolbar } from "@/components/preview/preview-toolbar";
import { readGeneratedDocument } from "@/lib/generated-document";
import type { GeneratedDocumentState } from "@/types/chat";

export default function PreviewPage() {
  const router = useRouter();
  const [zoom, setZoom] = useState(100);
  const [document, setDocument] = useState<GeneratedDocumentState | null>(null);

  useEffect(() => {
    const generatedDocument = readGeneratedDocument();
    if (!generatedDocument) {
      router.replace("/");
      return;
    }
    setDocument(generatedDocument);
  }, [router]);

  if (!document) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#09090B] px-5 text-white">
        <p className="text-sm text-zinc-400">Opening your document...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#09090B] px-5 py-10 text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-7">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="flex flex-col gap-2"
        >
          <p className="text-sm font-medium text-zinc-500">Ready</p>
          <h1 className="text-3xl font-semibold tracking-normal">
            Your document is ready
          </h1>
          <p className="text-sm text-zinc-400">{document.filename}</p>
        </motion.div>

        <PreviewToolbar
          zoom={zoom}
          onZoomIn={() => setZoom((value) => Math.min(160, value + 10))}
          onZoomOut={() => setZoom((value) => Math.max(60, value - 10))}
          onRegenerate={() => router.push("/processing")}
          onDownload={() => {
            const safeFilename =
              document.filename
                .replace(/[^a-zA-Z0-9_\-\.\s]/g, "")
                .replace(/\.{2,}/g, ".")
                .trim() || "paperchat-document.pdf";
            const link = window.document.createElement("a");
            link.href = document.objectUrl;
            link.download = safeFilename.endsWith(".pdf") ? safeFilename : `${safeFilename}.pdf`;
            link.rel = "noopener noreferrer";
            link.click();
          }}
          onDownloadMarkdown={() => {
            const rawStored = window.sessionStorage.getItem("paperchat:input");
            let mdContent = `# ${document.filename.replace(/\.pdf$/i, "")}\n\nGenerated via PaperChat\n`;
            if (rawStored) {
              try {
                const parsed = JSON.parse(rawStored);
                if (parsed.rawText) {
                  mdContent = `---\ntitle: "${document.filename.replace(/\.pdf$/i, "")}"\nsource: "PaperChat Pasted Text"\ndate: "${new Date().toISOString().split("T")[0]}"\n---\n\n${parsed.rawText}`;
                } else if (parsed.link) {
                  mdContent = `---\ntitle: "${document.filename.replace(/\.pdf$/i, "")}"\nsource_url: "${parsed.link}"\ndate: "${new Date().toISOString().split("T")[0]}"\n---\n\nExported conversation from ${parsed.link}\n`;
                }
              } catch {
                // Keep default content
              }
            }
            const blob = new Blob([mdContent], { type: "text/markdown;charset=utf-8" });
            const mdUrl = URL.createObjectURL(blob);
            const mdLink = window.document.createElement("a");
            const safeBasename = document.filename.replace(/\.pdf$/i, "").replace(/[^a-zA-Z0-9_\-\.\s]/g, "") || "paperchat-document";
            mdLink.href = mdUrl;
            mdLink.download = `${safeBasename}.md`;
            mdLink.click();
            URL.revokeObjectURL(mdUrl);
          }}
          onFullscreen={() => {
            const element = window.document.documentElement;
            if (!window.document.fullscreenElement) {
              element.requestFullscreen?.();
            } else {
              window.document.exitFullscreen?.();
            }
          }}
        />

        <PdfPreview pdfUrl={document.objectUrl} zoom={zoom} />
      </div>
    </main>
  );
}
