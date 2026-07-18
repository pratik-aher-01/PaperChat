"use client";

import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

type Status = "pending" | "active" | "done";

export function ProcessingCard({
  index,
  label,
  status,
}: {
  index: number;
  label: string;
  status: Status;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: index * 0.05 }}
      className={cn(
        "flex items-center gap-3 rounded-xl border px-4 py-3.5 transition-colors",
        status === "active" && "border-white/25 bg-[#18181B]",
        status === "done" && "border-white/10 bg-white/[0.035]",
        status === "pending" && "border-white/[0.07] bg-transparent",
      )}
    >
      <div
        className={cn(
          "grid size-7 shrink-0 place-items-center rounded-full border text-xs",
          status === "done" && "border-white bg-white text-black",
          status === "active" && "border-white/35 text-white",
          status === "pending" && "border-white/10 text-zinc-500",
        )}
      >
        {status === "done" ? (
          <Check className="size-4" strokeWidth={2.4} />
        ) : status === "active" ? (
          <Loader2 className="size-4 animate-spin" strokeWidth={2} />
        ) : (
          index + 1
        )}
      </div>
      <span
        className={cn(
          "text-sm font-medium",
          status === "pending" ? "text-zinc-500" : "text-white",
        )}
      >
        {label}
      </span>
    </motion.div>
  );
}
