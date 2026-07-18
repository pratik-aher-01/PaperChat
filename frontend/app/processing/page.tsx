"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

import { DocumentLoader } from "@/components/processing/document-loader";
import { ProcessingCard } from "@/components/processing/processing-card";
import { ProgressBar } from "@/components/processing/progress-bar";
import { Button } from "@/components/ui/button";
import { generatePdf } from "@/lib/api";
import {
  INPUT_STORAGE_KEY,
  writeGeneratedDocument,
} from "@/lib/generated-document";
import { PROCESSING_STAGES, formatEstimatedTime } from "@/lib/paperchat-data";
import type { ConversationInput } from "@/types/chat";

const TOTAL_DURATION = PROCESSING_STAGES.reduce(
  (total, stage) => total + stage.duration,
  0,
);

export default function ProcessingPage() {
  const router = useRouter();
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const hasStarted = useRef(false);

  useEffect(() => {
    const tick = 100;
    const interval = window.setInterval(() => {
      setElapsed((current) => {
        if (isComplete) return TOTAL_DURATION;
        return Math.min(current + tick, TOTAL_DURATION * 0.92);
      });
    }, tick);

    return () => window.clearInterval(interval);
  }, [isComplete]);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    const rawInput = window.sessionStorage.getItem(INPUT_STORAGE_KEY);
    if (!rawInput) {
      router.replace("/");
      return;
    }

    async function runGeneration() {
      try {
        const input = JSON.parse(rawInput as string) as ConversationInput;
        const result = await generatePdf(input);
        const objectUrl = URL.createObjectURL(result.blob);

        writeGeneratedDocument({
          filename: result.filename,
          objectUrl,
          sourceUrl: input.link,
        });
        setIsComplete(true);
        window.setTimeout(() => router.push("/preview"), 450);
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught.message
            : "PaperChat could not generate the PDF.",
        );
      }
    }

    void runGeneration();
  }, [router]);

  const { activeIndex, progress, remainingSeconds } = useMemo(() => {
    let cursor = 0;
    let active = PROCESSING_STAGES.length - 1;

    for (let index = 0; index < PROCESSING_STAGES.length; index += 1) {
      cursor += PROCESSING_STAGES[index].duration;
      if (elapsed < cursor) {
        active = index;
        break;
      }
    }

    return {
      activeIndex: active,
      progress: Math.min(100, (elapsed / TOTAL_DURATION) * 100),
      remainingSeconds: Math.max(0, (TOTAL_DURATION - elapsed) / 1000),
    };
  }, [elapsed]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#09090B] px-5 py-12 text-white">
      <section className="flex w-full max-w-md flex-col items-center gap-8">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <DocumentLoader />
        </motion.div>

        <div className="text-center">
          <p className="mb-2 text-sm font-medium text-zinc-500">PaperChat</p>
          <h1 className="text-3xl font-semibold tracking-normal">
            {error ? "Generation stopped" : "Structuring your document"}
          </h1>
          <p className="mt-3 text-sm text-zinc-400">
            {error ?? formatEstimatedTime(remainingSeconds)}
          </p>
        </div>

        <ProgressBar progress={progress} />

        <div className="flex w-full flex-col gap-2">
          {PROCESSING_STAGES.map((stage, index) => (
            <ProcessingCard
              key={stage.id}
              index={index}
              label={stage.label}
              status={
                index < activeIndex
                  ? "done"
                  : index === activeIndex
                    ? "active"
                    : "pending"
              }
            />
          ))}
        </div>

        {error && (
          <Button
            type="button"
            className="rounded-lg bg-white px-6 text-black hover:bg-zinc-200"
            onClick={() => router.push("/")}
          >
            Try another link
          </Button>
        )}
      </section>
    </main>
  );
}
