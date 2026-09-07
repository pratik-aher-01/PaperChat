"use client";

import type { ReactNode } from "react";
import {
  ArrowDown,
  BookOpenText,
  Braces,
  Check,
  FileText,
  GraduationCap,
  Layers3,
  LibraryBig,
  NotebookTabs,
  PanelTop,
  Printer,
  Search,
  Sparkles,
  WandSparkles,
} from "lucide-react";

import { GeneratorCard } from "@/components/generation/generator-card";
import { SITE } from "@/lib/paperchat-data";

const problems = [
  { label: "Slow", detail: "Endless chat scroll buries the useful parts." },
  { label: "Messy", detail: "Answers, follow-ups, code, and notes blur together." },
  { label: "Difficult to search", detail: "Important context becomes hard to retrieve." },
  { label: "Impossible to print", detail: "Raw chats do not behave like study material." },
];

const timeline = [
  "Paste Chat",
  "AI Organizes Everything",
  "Generate Beautiful PDF",
  "Study Anywhere",
];

const features = [
  { icon: WandSparkles, title: "AI Organization" },
  { icon: FileText, title: "Professional PDF Layout" },
  { icon: NotebookTabs, title: "Topic Detection" },
  { icon: Braces, title: "Code Formatting" },
  { icon: Printer, title: "Print Ready" },
  { icon: BookOpenText, title: "Revision Friendly" },
  { icon: Sparkles, title: "Fast Export" },
  { icon: PanelTop, title: "Beautiful Typography" },
];

const audiences = [
  "Students",
  "Researchers",
  "Developers",
  "Engineers",
  "Professionals",
  "Content Creators",
];

const roadmap = [
  "Chat",
  "Structured Knowledge",
  "PDF",
  "DOCX",
  "PPT",
  "Flashcards",
  "Mind Maps",
];

export function LandingPage() {
  return (
    <main className="min-h-screen overflow-x-hidden bg-[#09090B] text-[#FAFAFA]">
      <Hero />
      <MarketingSections />
    </main>
  );
}

function Hero() {
  return (
    <section className="relative isolate flex min-h-[100dvh] flex-col justify-between px-4 sm:px-6">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_-15%,rgba(255,255,255,0.12),transparent_40%),linear-gradient(to_bottom,rgba(255,255,255,0.03),transparent_50%)]" />
      <SiteHeader />
      <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-center justify-center gap-4 py-4 text-center sm:gap-6 sm:py-8">
        <div className="max-w-3xl">
          <h1 className="text-balance text-2xl font-semibold leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-[4.5rem]">
            Turn AI conversations into beautiful documents.
          </h1>
        </div>
        <div className="w-full max-w-xl">
          <GeneratorCard />
        </div>
        <p className="max-w-xl text-balance text-xs sm:text-sm font-normal leading-relaxed text-[#A1A1AA]">
          {SITE.description}
        </p>
      </div>

      {/* Scroll to explore hint */}
      <div className="mx-auto pb-4 pt-2 text-center">
        <a
          href="#features"
          className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-[11px] font-medium text-zinc-400 backdrop-blur-sm transition hover:border-white/20 hover:text-zinc-200 active:scale-95"
        >
          <span>Scroll to explore</span>
          <ArrowDown className="size-3 animate-bounce" />
        </a>
      </div>
    </section>
  );
}

function SiteHeader() {
  return (
    <header className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between">
      <a href="#" className="group inline-flex items-center gap-2">
        <LogoMark />
        <span className="text-sm font-medium text-zinc-100">PaperChat</span>
      </a>
      <a
        href={SITE.github}
        className="inline-flex h-9 items-center gap-2 rounded-lg border border-white/10 bg-white/[0.035] px-3 text-sm font-medium text-zinc-300 transition hover:border-white/20 hover:bg-white/[0.065] hover:text-white"
      >
        <GithubMark />
        <span>GitHub</span>
      </a>
    </header>
  );
}

function MarketingSections() {
  return (
    <div id="features" className="border-t border-white/[0.06] bg-[#09090B]">
      <Section
        eyebrow="Why PaperChat"
        title="AI chats are brilliant while you are inside them. They fall apart when you need to revisit them."
      >
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
          {problems.map((problem) => (
            <div
              key={problem.label}
              className="rounded-lg border border-white/10 bg-[#18181B] p-5"
            >
              <div className="mb-6 flex size-9 items-center justify-center rounded-lg border border-white/10 bg-white/[0.035]">
                <Search className="size-4 text-zinc-300" />
              </div>
              <h3 className="text-base font-medium">{problem.label}</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                {problem.detail}
              </p>
            </div>
          ))}
        </div>
      </Section>

      <Section eyebrow="How it works" title="From raw conversation to polished study document in four calm steps.">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {timeline.map((item, index) => (
            <div
              key={item}
              className="relative rounded-lg border border-white/10 bg-[#18181B] p-5"
            >
              <span className="text-xs font-medium text-zinc-500">
                0{index + 1}
              </span>
              <h3 className="mt-6 text-lg font-medium">{item}</h3>
              {index < timeline.length - 1 && (
                <ArrowDown className="mt-6 size-4 text-zinc-600 lg:absolute lg:right-5 lg:top-1/2 lg:mt-0 lg:-rotate-90" />
              )}
            </div>
          ))}
        </div>
      </Section>

      <Section eyebrow="Features" title="Everything needed to make AI output feel composed, durable, and ready to use.">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="flex items-center gap-3 rounded-lg border border-white/10 bg-[#18181B] p-4"
            >
              <feature.icon className="size-4 text-zinc-300 shrink-0" />
              <span className="text-sm font-medium text-zinc-100">
                {feature.title}
              </span>
            </div>
          ))}
        </div>
      </Section>

      <Section eyebrow="Who it is for" title="For anyone turning conversation into material they need to keep.">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {audiences.map((audience) => (
            <div
              key={audience}
              className="flex items-center justify-between rounded-lg border border-white/10 bg-[#18181B] p-5"
            >
              <div className="flex items-center gap-3">
                <GraduationCap className="size-4 text-zinc-400" />
                <span className="font-medium">{audience}</span>
              </div>
              <Check className="size-4 text-zinc-500" />
            </div>
          ))}
        </div>
      </Section>

      <Section eyebrow="Future vision" title="A conversation becomes a portable knowledge system.">
        <div className="rounded-lg border border-white/10 bg-[#18181B] p-3">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-7">
            {roadmap.map((item, index) => (
              <div key={item} className="flex items-center gap-2 lg:block">
                <div className="rounded-lg border border-white/10 bg-[#09090B] p-4 text-center w-full">
                  <div className="mx-auto mb-3 grid size-8 place-items-center rounded-lg bg-white text-black">
                    <Layers3 className="size-4" />
                  </div>
                  <span className="text-sm font-medium">{item}</span>
                </div>
                {index < roadmap.length - 1 && (
                  <ArrowDown className="size-4 shrink-0 text-zinc-600 sm:hidden" />
                )}
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Footer />
    </div>
  );
}

function Section({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="px-4 sm:px-6 py-14 sm:py-20 lg:py-24">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 sm:mb-10 max-w-3xl">
          <p className="mb-2 text-xs sm:text-sm font-medium text-zinc-500">{eyebrow}</p>
          <h2 className="text-balance text-2xl font-semibold leading-snug tracking-tight sm:text-4xl lg:text-5xl">
            {title}
          </h2>
        </div>
        {children}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/[0.06] px-4 sm:px-6 py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 text-sm text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-zinc-200">
          <LogoMark />
          <span className="font-medium">PaperChat</span>
        </div>
        <p>Built with care for learners.</p>
        <a
          href={SITE.github}
          className="inline-flex items-center gap-2 text-zinc-400 transition hover:text-white"
        >
          <GithubMark />
          GitHub
        </a>
        <p>Copyright 2026 PaperChat.</p>
      </div>
    </footer>
  );
}

function LogoMark() {
  return (
    <span className="grid size-8 place-items-center rounded-lg border border-white/10 bg-white text-black shadow-[0_10px_30px_rgba(255,255,255,0.08)]">
      <LibraryBig className="size-4" />
    </span>
  );
}

function GithubMark() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" aria-hidden="true">
      <path
        d="M12 2.4c-5.3 0-9.6 4.3-9.6 9.6 0 4.2 2.7 7.8 6.5 9.1.5.1.7-.2.7-.5v-1.8c-2.7.6-3.2-1.1-3.2-1.1-.4-1-.9-1.3-.9-1.3-.8-.5.1-.5.1-.5.9.1 1.3.9 1.3.9.8 1.3 2 1 2.5.8.1-.6.3-1 .6-1.2-2.1-.2-4.3-1.1-4.3-4.7 0-1 .4-1.9.9-2.5-.1-.2-.4-1.2.1-2.5 0 0 .7-.2 2.6.9.8-.2 1.6-.3 2.4-.3s1.7.1 2.4.3c1.8-1.2 2.6-.9 2.6-.9.5 1.3.2 2.3.1 2.5.6.7.9 1.5.9 2.5 0 3.7-2.2 4.5-4.3 4.7.3.3.6.9.6 1.7v2.5c0 .3.2.6.7.5 3.8-1.3 6.5-4.9 6.5-9.1 0-5.3-4.3-9.6-9.6-9.6Z"
        fill="currentColor"
      />
    </svg>
  );
}
