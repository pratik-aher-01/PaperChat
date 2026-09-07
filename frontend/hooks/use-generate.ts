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
        const trimmedText = (input.rawText || "").trim();
        if (trimmedText.length < 10) {
          setError("Pasted text is too short. Please provide at least a couple of sentences.");
          return;
        }
        if (trimmedText.length > 500_000) {
          setError("Pasted text is too long (maximum 500,000 characters).");
          return;
        }
      } else {
        const trimmedLink = (input.link || "").trim();
        if (!/^https?:\/\//i.test(trimmedLink)) {
          setError("Please enter a valid URL starting with http:// or https://");
          return;
        }

        try {
          const parsed = new URL(trimmedLink);
          if (!parsed.hostname || parsed.hostname.length > 255 || trimmedLink.length > 2048) {
            setError("Please enter a valid share URL.");
            return;
          }
        } catch {
          setError("Please enter a valid share URL.");
          return;
        }
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
