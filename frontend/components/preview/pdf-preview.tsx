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
    <div className="flex flex-col items-center justify-center overflow-x-auto rounded-xl border border-white/10 bg-[#18181B]/70 p-3 sm:p-6 lg:p-10">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        style={{ width: `${(zoom / 100) * 640}px` }}
        className="aspect-[8.5/11] max-w-full shrink-0 overflow-hidden rounded-sm bg-[#F5F4F0] shadow-[0_20px_60px_rgba(0,0,0,0.5)] transition-[width] duration-200"
      >
        <object
          data={`${pdfUrl}#toolbar=0&navpanes=0`}
          type="application/pdf"
          className="h-full w-full border-0 bg-white"
        >
          <iframe
            title="Generated PaperChat PDF Preview"
            src={`${pdfUrl}#toolbar=0&navpanes=0`}
            className="h-full w-full border-0 bg-white"
          />
        </object>
      </motion.div>
    </div>
  );
}
