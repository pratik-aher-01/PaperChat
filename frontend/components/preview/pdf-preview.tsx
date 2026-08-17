"use client";

import { motion } from "framer-motion";

export function PdfPreview({
  pdfUrl,
  zoom,
}: {
  pdfUrl: string;
  zoom: number;
}) {
  return (
    <div className="flex justify-center overflow-auto rounded-xl border border-white/10 bg-[#18181B]/70 p-6 sm:p-10">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        style={{ width: `${(zoom / 100) * 640}px` }}
        className="aspect-[8.5/11] shrink-0 overflow-hidden rounded-sm bg-[#F5F4F0] shadow-[0_35px_100px_rgba(0,0,0,0.45)] transition-[width] duration-200"
      >
        <iframe
          title="Generated PaperChat PDF Preview"
          src={`${pdfUrl}#toolbar=0&navpanes=0`}
          sandbox="allow-scripts allow-same-origin allow-downloads"
          referrerPolicy="no-referrer"
          className="h-full w-full border-0 bg-white"
        />
      </motion.div>
    </div>
  );
}
