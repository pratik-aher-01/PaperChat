"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";

import { clearGeneratedDocument, INPUT_STORAGE_KEY } from "@/lib/generated-document";
import type { ConversationInput } from "@/types/chat";

export function useGenerate() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    (input: ConversationInput) => {
      setError(null);

      const hasContent =
        (input.mode === "link" && input.link?.trim()) ||
        (input.mode === "text" && input.rawText?.trim());

      if (!hasContent) {
        setError("Add a shared link or paste a conversation first.");
        return;
      }

      if (input.mode === "text") {
        setError("Paste-text generation is not connected in the MVP yet. Use a shared link.");
        return;
      }

      setIsSubmitting(true);
      clearGeneratedDocument();
      window.sessionStorage.setItem(INPUT_STORAGE_KEY, JSON.stringify(input));
      router.push("/processing");
    },
    [router],
  );

  return { error, isSubmitting, submit };
}
