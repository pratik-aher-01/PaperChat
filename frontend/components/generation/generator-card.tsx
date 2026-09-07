"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useGenerate } from "@/hooks/use-generate";
import { readPdfSettings, writePdfSettings } from "@/lib/generated-document";
import { cn } from "@/lib/utils";
import type { InputMode, PdfSettings, ProviderId } from "@/types/chat";

import { DEFAULT_PDF_SETTINGS, PdfSettingsDialog } from "./pdf-settings-dialog";
import { ProviderMark } from "./provider-mark";

const providers: { name: string; id: ProviderId }[] = [
  { name: "ChatGPT", id: "chatgpt" },
  { name: "Claude", id: "claude" },
  { name: "Gemini", id: "gemini" },
  { name: "Perplexity", id: "perplexity" },
];

export function GeneratorCard() {
  const [mode, setMode] = useState<InputMode>("link");
  const [provider, setProvider] = useState<ProviderId>("chatgpt");
  const [link, setLink] = useState("");
  const [rawText, setRawText] = useState("");
  const [pdfSettings, setPdfSettings] = useState<PdfSettings>(DEFAULT_PDF_SETTINGS);
  const { error, isSubmitting, submit } = useGenerate();

  useEffect(() => {
    const saved = readPdfSettings();
    if (saved) {
      setPdfSettings(saved);
    }
  }, []);

  const handleSettingsChange = (newSettings: PdfSettings) => {
    setPdfSettings(newSettings);
    writePdfSettings(newSettings);
  };

  return (
    <form
      className="mx-auto w-full max-w-[580px] rounded-[18px] border border-white/12 bg-[#18181B] p-3 text-left shadow-[0_24px_70px_rgba(0,0,0,0.38),inset_0_1px_0_rgba(255,255,255,0.07)] sm:p-4"
      onSubmit={(event) => {
        event.preventDefault();
        submit({ mode, provider, link, rawText, options: pdfSettings });
      }}
    >
      <div className="mb-2 flex items-center justify-between text-sm font-semibold">
        <div className="flex items-center gap-2">
          {[
            { id: "link", label: "share link" },
            { id: "text", label: "paste text" },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setMode(tab.id as InputMode)}
              className={cn(
                "rounded-md px-2 py-1 text-xs sm:text-sm text-zinc-400 transition hover:text-white",
                mode === tab.id && "bg-white text-black font-semibold hover:text-black",
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <PdfSettingsDialog settings={pdfSettings} onChange={handleSettingsChange} />
      </div>

      <div className="my-2.5">
        {mode === "link" ? (
          <input
            key="link-input"
            type="url"
            value={link}
            onChange={(event) => setLink(event.target.value)}
            placeholder="Paste public chat link (ChatGPT, Claude, Gemini, Perplexity)..."
            className="h-11 w-full rounded-xl border border-white/15 bg-[#09090B] px-3.5 text-sm font-medium text-white outline-none placeholder:text-zinc-500 focus:border-white/40 focus:ring-1 focus:ring-white/20 transition-all"
          />
        ) : (
          <Textarea
            key="text-input"
            value={rawText}
            onChange={(event) => setRawText(event.target.value)}
            placeholder="Paste raw conversation transcript here (User: ... Assistant: ...)..."
            className="min-h-28 resize-none rounded-xl border border-white/15 bg-[#09090B] px-3.5 py-3 text-sm font-medium text-white outline-none placeholder:text-zinc-500 focus-visible:border-white/40 focus-visible:ring-1 focus-visible:ring-white/20 transition-all"
          />
        )}
      </div>

      {error && (
        <p className="mb-2 text-xs font-medium text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-lg">
          {error}
        </p>
      )}

      <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          {providers.map((item) => (
            <div
              key={item.id}
              title={item.name}
              className="grid size-10 cursor-default place-items-center rounded-lg border border-white/20 bg-white shadow-sm"
            >
              <ProviderMark mark={item.id} />
            </div>
          ))}
        </div>

        <Button
          type="submit"
          disabled={isSubmitting}
          className="h-10 min-w-40 rounded-lg bg-white px-7 text-sm font-semibold text-black hover:bg-zinc-200"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Generating
            </>
          ) : (
            "Generate"
          )}
        </Button>
      </div>
    </form>
  );
}
