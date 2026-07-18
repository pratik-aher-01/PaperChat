"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useGenerate } from "@/hooks/use-generate";
import { cn } from "@/lib/utils";
import type { InputMode, ProviderId } from "@/types/chat";

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
  const { error, isSubmitting, submit } = useGenerate();

  return (
    <form
      className="mx-auto w-full max-w-[580px] rounded-[18px] border border-white/12 bg-[#18181B] p-3 text-left shadow-[0_24px_70px_rgba(0,0,0,0.38),inset_0_1px_0_rgba(255,255,255,0.07)] sm:p-4"
      onSubmit={(event) => {
        event.preventDefault();
        submit({ mode, provider, link, rawText });
      }}
    >
      <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
        {[
          { id: "link", label: "share link" },
          { id: "text", label: "paste text" },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setMode(tab.id as InputMode)}
            disabled={tab.id === "text"}
            className={cn(
              "rounded-md px-1.5 py-1 text-zinc-500 transition hover:text-white",
              mode === tab.id && "bg-white text-black hover:text-black",
              tab.id === "text" && "cursor-not-allowed opacity-45 hover:text-zinc-500",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {mode === "link" ? (
          <motion.input
            key="link"
            type="url"
            value={link}
            onChange={(event) => setLink(event.target.value)}
            placeholder="https://chatgpt.com/share/..."
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.18 }}
            className="h-11 w-full rounded-lg border border-white/12 bg-[#09090B] px-4 text-sm font-medium text-white outline-none placeholder:text-zinc-500 focus:border-white/35"
          />
        ) : (
          <motion.div
            key="text"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.18 }}
          >
            <Textarea
              value={rawText}
              onChange={(event) => setRawText(event.target.value)}
              placeholder="Paste the full conversation text here..."
              className="min-h-24 resize-none rounded-lg border-white/12 bg-[#09090B] px-4 py-3 text-sm font-medium text-white outline-none placeholder:text-zinc-500 focus-visible:border-white/35 focus-visible:ring-white/10"
            />
          </motion.div>
        )}
      </AnimatePresence>

      {error && <p className="mt-2 text-xs font-medium text-zinc-300">{error}</p>}

      <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          {providers.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-label={item.name}
              onClick={() => setProvider(item.id)}
              className={cn(
                "grid size-10 place-items-center rounded-lg border border-white/12 bg-[#09090B] text-zinc-400 transition hover:border-white/25 hover:text-white",
                provider === item.id && "bg-white text-black hover:text-black",
              )}
            >
              <ProviderMark mark={item.id} />
            </button>
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
