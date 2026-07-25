import Image from "next/image";
import type { ProviderId } from "@/types/chat";

export function ProviderMark({ mark }: { mark: ProviderId }) {
  if (mark === "chatgpt") {
    return (
      <Image
        src="/images/chat-gpt.png"
        alt="ChatGPT Logo"
        width={24}
        height={24}
        className="size-6 object-contain"
      />
    );
  }

  if (mark === "claude") {
    return (
      <Image
        src="/images/claude.png"
        alt="Claude Logo"
        width={24}
        height={24}
        className="size-6 object-contain"
      />
    );
  }

  if (mark === "gemini") {
    return (
      <Image
        src="/images/Gemini.png"
        alt="Gemini Logo"
        width={32}
        height={32}
        className="size-8 object-contain"
      />
    );
  }

  return (
    <Image
      src="/images/perplexity.png"
      alt="Perplexity Logo"
      width={32}
      height={32}
      className="size-8 object-contain"
    />
  );
}
