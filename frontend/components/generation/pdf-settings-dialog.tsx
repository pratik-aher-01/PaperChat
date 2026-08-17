"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Maximize2, RotateCcw, Settings, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PdfSettings } from "@/types/chat";

export const DEFAULT_PDF_SETTINGS: PdfSettings = {
  pageFormat: "A4",
  layout: "single",
  fontFamily: "inter",
  fontSize: "medium",
  lineSpacing: "normal",
  margin: "normal",
  theme: "default",
  showCover: true,
  showHeaders: true,
};

interface PdfSettingsDialogProps {
  settings: PdfSettings;
  onChange: (settings: PdfSettings) => void;
}

export function PdfSettingsDialog({ settings, onChange }: PdfSettingsDialogProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [draft, setDraft] = useState<PdfSettings>(settings);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isCustomized = JSON.stringify(settings) !== JSON.stringify(DEFAULT_PDF_SETTINGS);

  const handleOpen = () => {
    setDraft(settings);
    setIsOpen(true);
  };

  const handleSave = () => {
    onChange(draft);
    setIsOpen(false);
  };

  const handleReset = () => {
    setDraft(DEFAULT_PDF_SETTINGS);
  };

  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          {/* Backdrop overlay - completely hides/blurs background content */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            className="absolute inset-0 bg-black/85 backdrop-blur-md"
          />

          {/* Compact Single-Page Dialog Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 8 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
            className="relative z-10 w-full max-w-2xl rounded-2xl border border-white/15 bg-[#121214] p-5 text-zinc-100 shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h2 className="text-base font-semibold text-white">PDF Generation Settings</h2>
                <p className="text-[11px] text-zinc-400">Configure page layout, typography, and styling prior to PDF export.</p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href="/settings"
                  className="inline-flex items-center gap-1 rounded-md border border-white/15 bg-white/10 px-2.5 py-1 text-xs font-medium text-white transition hover:bg-white/20"
                >
                  <Maximize2 className="size-3" />
                  Full Preview
                </a>
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="rounded-lg p-1 text-zinc-400 transition hover:bg-white/10 hover:text-white"
                >
                  <X className="size-4" />
                </button>
              </div>
            </div>

            {/* Compact Non-Scrolling Content Grid */}
            <div className="space-y-3.5 py-3 text-[11px]">
              {/* Row 1: Page Format & Column Layout */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1.5 block font-medium text-zinc-300">Page Format</label>
                  <div className="grid grid-cols-3 gap-1.5">
                    {[
                      { id: "A4", label: "A4" },
                      { id: "Letter", label: "US Letter" },
                      { id: "Legal", label: "US Legal" },
                    ].map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => setDraft({ ...draft, pageFormat: opt.id as PdfSettings["pageFormat"] })}
                        className={`rounded-md border py-1.5 text-center font-medium transition ${
                          draft.pageFormat === opt.id
                            ? "border-white bg-white text-black font-semibold"
                            : "border-white/10 bg-[#09090B] text-zinc-400 hover:border-white/25 hover:text-white"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block font-medium text-zinc-300">Column Layout</label>
                  <div className="grid grid-cols-3 gap-1.5">
                    {[
                      { id: "single", label: "Single" },
                      { id: "two-column", label: "Two Col" },
                      { id: "auto", label: "Auto Flow" },
                    ].map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => setDraft({ ...draft, layout: opt.id as PdfSettings["layout"] })}
                        className={`rounded-md border py-1.5 text-center font-medium transition ${
                          draft.layout === opt.id
                            ? "border-white bg-white text-black font-semibold"
                            : "border-white/10 bg-[#09090B] text-zinc-400 hover:border-white/25 hover:text-white"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Row 2: Font Family (with visual representation) */}
              <div>
                <label className="mb-1.5 block font-medium text-zinc-300">Font Family (Visual Preview)</label>
                <div className="grid grid-cols-4 gap-1.5">
                  {[
                    { id: "inter", label: "Inter (Sans)", style: { fontFamily: "Inter, system-ui, sans-serif" } },
                    { id: "serif", label: "Georgia (Serif)", style: { fontFamily: "Georgia, Cambria, serif" } },
                    { id: "mono", label: "JetBrains (Mono)", style: { fontFamily: '"JetBrains Mono", Consolas, monospace' } },
                    { id: "dyslexic", label: "OpenDyslexic", style: { fontFamily: '"OpenDyslexic", "Lexend", sans-serif' } },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setDraft({ ...draft, fontFamily: opt.id as PdfSettings["fontFamily"] })}
                      style={opt.style}
                      className={`rounded-md border px-2 py-2 text-center text-xs transition ${
                        draft.fontFamily === opt.id
                          ? "border-white bg-white text-black font-semibold shadow-sm"
                          : "border-white/10 bg-[#09090B] text-zinc-300 hover:border-white/25 hover:text-white"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Row 3: Font Size, Line Spacing, Page Margins */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="mb-1.5 block font-medium text-zinc-300">Font Size</label>
                  <div className="grid grid-cols-3 gap-1">
                    {[
                      { id: "small", label: "Small" },
                      { id: "medium", label: "Med" },
                      { id: "large", label: "Large" },
                    ].map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => setDraft({ ...draft, fontSize: opt.id as PdfSettings["fontSize"] })}
                        className={`rounded-md border py-1.5 text-center font-medium transition ${
                          draft.fontSize === opt.id
                            ? "border-white bg-white text-black font-semibold"
                            : "border-white/10 bg-[#09090B] text-zinc-400 hover:border-white/25 hover:text-white"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block font-medium text-zinc-300">Line Spacing</label>
                  <div className="grid grid-cols-3 gap-1">
                    {[
                      { id: "compact", label: "Tight" },
                      { id: "normal", label: "Normal" },
                      { id: "relaxed", label: "Relaxed" },
                    ].map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => setDraft({ ...draft, lineSpacing: opt.id as PdfSettings["lineSpacing"] })}
                        className={`rounded-md border py-1.5 text-center font-medium transition ${
                          draft.lineSpacing === opt.id
                            ? "border-white bg-white text-black font-semibold"
                            : "border-white/10 bg-[#09090B] text-zinc-400 hover:border-white/25 hover:text-white"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block font-medium text-zinc-300">Margins</label>
                  <div className="grid grid-cols-3 gap-1">
                    {[
                      { id: "narrow", label: "Narrow" },
                      { id: "normal", label: "Normal" },
                      { id: "wide", label: "Wide" },
                    ].map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => setDraft({ ...draft, margin: opt.id as PdfSettings["margin"] })}
                        className={`rounded-md border py-1.5 text-center font-medium transition ${
                          draft.margin === opt.id
                            ? "border-white bg-white text-black font-semibold"
                            : "border-white/10 bg-[#09090B] text-zinc-400 hover:border-white/25 hover:text-white"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Row 4: Theme */}
              <div>
                <label className="mb-1.5 block font-medium text-zinc-300">Document Theme</label>
                <div className="grid grid-cols-4 gap-1.5">
                  {[
                    { id: "default", label: "Technical" },
                    { id: "minimal", label: "Minimal" },
                    { id: "dark", label: "Dark Mode" },
                    { id: "academic", label: "Academic" },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setDraft({ ...draft, theme: opt.id as PdfSettings["theme"] })}
                      className={`rounded-md border py-1.5 text-center font-medium transition ${
                        draft.theme === opt.id
                          ? "border-white bg-white text-black font-semibold"
                          : "border-white/10 bg-[#09090B] text-zinc-400 hover:border-white/25 hover:text-white"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Row 5: Toggles */}
              <div className="grid grid-cols-2 gap-3 pt-1">
                <label className="flex items-center justify-between rounded-md border border-white/10 bg-[#09090B] px-3 py-2 cursor-pointer transition hover:border-white/20">
                  <span className="text-zinc-300 font-medium">Include Cover Page</span>
                  <input
                    type="checkbox"
                    checked={draft.showCover}
                    onChange={(e) => setDraft({ ...draft, showCover: e.target.checked })}
                    className="size-3.5 rounded border-white/20 bg-zinc-800 text-white accent-white cursor-pointer"
                  />
                </label>

                <label className="flex items-center justify-between rounded-md border border-white/10 bg-[#09090B] px-3 py-2 cursor-pointer transition hover:border-white/20">
                  <span className="text-zinc-300 font-medium">Running Header & Footer</span>
                  <input
                    type="checkbox"
                    checked={draft.showHeaders}
                    onChange={(e) => setDraft({ ...draft, showHeaders: e.target.checked })}
                    className="size-4 rounded border-white/20 bg-zinc-800 text-white accent-white cursor-pointer"
                  />
                </label>
              </div>
            </div>

            {/* Footer Actions */}
            <div className="flex items-center justify-between border-t border-white/10 pt-3 mt-1 text-xs">
              <button
                type="button"
                onClick={handleReset}
                className="flex items-center gap-1 text-zinc-400 transition hover:text-white"
              >
                <RotateCcw className="size-3" />
                Reset defaults
              </button>

              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsOpen(false)}
                  className="h-8 px-3 text-xs text-zinc-400 hover:bg-white/10 hover:text-white"
                >
                  Cancel
                </Button>
                <Button
                  type="button"
                  onClick={handleSave}
                  className="h-8 gap-1 rounded-md bg-white px-4 text-xs font-semibold text-black hover:bg-zinc-200"
                >
                  <Check className="size-3.5" />
                  Save & Apply
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );

  return (
    <>
      <button
        type="button"
        onClick={handleOpen}
        title="Configure PDF Layout"
        aria-label="Configure PDF Layout"
        className="relative flex items-center gap-1.5 rounded-md border border-white/10 bg-[#09090B] px-2.5 py-1 text-xs font-medium text-zinc-400 transition hover:border-white/25 hover:bg-white/[0.06] hover:text-white"
      >
        <Settings className="size-3.5" />
        <span>Layout settings</span>
        {isCustomized && (
          <span className="size-1.5 rounded-full bg-emerald-400" />
        )}
      </button>

      {mounted && createPortal(modalContent, document.body)}
    </>
  );
}
