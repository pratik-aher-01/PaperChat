"""Content cleaner service for removing conversational fluff and normalizing content."""

import re

FILLER_PHRASES = (
    r"as an ai language model,?",
    r"sure[!\.\s]+i'(?:d|m) (?:be )?(?:happy|glad) to help(?: you)?(?: with that)?[!\.]?",
    r"certainly[!\.]?",
    r"spot on[!\.]?",
    r"you (?:nailed|crushed) (?:both|the) questions?[!\.]?",
    r"you said:?",
    r"hope this helps[!\.]?",
    r"let me know if you have any questions[!\.]?",
    r"let's begin with the very first topic on your syllabus[!\.]?",
)


class ContentCleaner:
    """Clean conversational noise and normalize markdown structure."""

    def clean_text(self, text: str, strip_fluff: bool = True) -> str:
        """Clean markdown text by removing filler phrases and normalizing spacing."""
        if not text:
            return ""

        cleaned = text.strip()

        if strip_fluff:
            for pattern in FILLER_PHRASES:
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

        # Remove repetitive leading/trailing empty lines
        lines = [line.rstrip() for line in cleaned.splitlines()]
        cleaned_lines: list[str] = []

        for line in lines:
            if not line and cleaned_lines and not cleaned_lines[-1]:
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def deduplicate_code_blocks(self, text: str) -> str:
        """Remove identical duplicate code blocks that occur within close proximity."""
        code_blocks = re.findall(r"```[\s\S]*?```", text)
        if len(code_blocks) <= 1:
            return text

        seen: set[str] = set()
        result_text = text

        for cb in code_blocks:
            norm_cb = "".join(cb.split())
            if norm_cb in seen:
                result_text = result_text.replace(cb, "", 1)
            else:
                seen.add(norm_cb)

        return result_text.strip()
