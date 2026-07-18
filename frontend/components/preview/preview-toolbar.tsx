"use client";

import { Download, Maximize2, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";

import { Button } from "@/components/ui/button";

export function PreviewToolbar({
  onFullscreen,
  onDownload,
  onRegenerate,
  onZoomIn,
  onZoomOut,
  zoom,
}: {
  onFullscreen: () => void;
  onDownload: () => void;
  onRegenerate: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  zoom: number;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-[#18181B] px-4 py-3">
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={onZoomOut}
          className="grid size-8 place-items-center rounded-lg text-zinc-400 transition hover:bg-white/10 hover:text-white"
          aria-label="Zoom out"
        >
          <ZoomOut className="size-4" />
        </button>
        <span className="w-12 text-center text-xs font-medium text-zinc-400">
          {zoom}%
        </span>
        <button
          type="button"
          onClick={onZoomIn}
          className="grid size-8 place-items-center rounded-lg text-zinc-400 transition hover:bg-white/10 hover:text-white"
          aria-label="Zoom in"
        >
          <ZoomIn className="size-4" />
        </button>
        <button
          type="button"
          onClick={onFullscreen}
          className="ml-1 grid size-8 place-items-center rounded-lg text-zinc-400 transition hover:bg-white/10 hover:text-white"
          aria-label="Fullscreen"
        >
          <Maximize2 className="size-4" />
        </button>
      </div>

      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="rounded-lg border border-white/10 bg-white/[0.035] text-zinc-200 hover:bg-white/10"
          onClick={onRegenerate}
        >
          <RotateCcw className="size-4" />
          Regenerate
        </Button>
        <Button
          type="button"
          size="sm"
          className="rounded-lg bg-white text-black hover:bg-zinc-200"
          onClick={onDownload}
        >
          <Download className="size-4" />
          Download PDF
        </Button>
      </div>
    </div>
  );
}
