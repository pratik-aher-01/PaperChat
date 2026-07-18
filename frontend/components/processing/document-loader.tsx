"use client";

import { motion } from "framer-motion";
import { FileText } from "lucide-react";

export function DocumentLoader() {
  return (
    <div className="relative flex size-20 items-center justify-center">
      <motion.div
        className="absolute inset-0 rounded-2xl border border-white/15"
        animate={{ rotate: 360 }}
        transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="absolute inset-3 rounded-xl border border-white/10"
        animate={{ rotate: -360 }}
        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
      />
      <FileText className="size-6 text-white" strokeWidth={1.75} />
    </div>
  );
}
