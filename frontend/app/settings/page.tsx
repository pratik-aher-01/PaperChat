"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronLeft,
  Columns,
  FileDown,
  FileText,
  Move,
  Palette,
  PanelTop,
  RotateCcw,
  Sparkles,
  Type,
} from "lucide-react";

import {
  readPdfSettings,
  writePdfSettings,
} from "@/lib/generated-document";
import type { PdfSettings } from "@/types/chat";

const FONT_STACKS: Record<PdfSettings["fontFamily"], string> = {
  inter: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  serif: "Georgia, 'Times New Roman', serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
  dyslexic: "Verdana, 'Trebuchet MS', sans-serif",
};

const FONT_SIZES: Record<PdfSettings["fontSize"], number> = {
  small: 12,
  medium: 13.5,
  large: 15.5,
};

const LINE_HEIGHTS: Record<PdfSettings["lineSpacing"], number> = {
  compact: 1.35,
  normal: 1.6,
  relaxed: 1.9,
};

const MARGINS: Record<PdfSettings["margin"], number> = {
  narrow: 22,
  normal: 36,
  wide: 56,
};

const PAGE_RATIOS: Record<PdfSettings["pageFormat"], string> = {
  A4: "210 / 297",
  Letter: "8.5 / 11",
  Legal: "8.5 / 14",
};

const PAGE_META: Record<PdfSettings["pageFormat"], string> = {
  A4: "210 × 297 mm",
  Letter: "8.5 × 11 in",
  Legal: "8.5 × 14 in",
};

interface ThemeConfig {
  name: string;
  page: string;
  text: string;
  heading: string;
  sub: string;
  divider: string;
  codeBg: string;
  codeText: string;
  chip: string;
  glow: string;
}

const THEMES: Record<PdfSettings["theme"], ThemeConfig> = {
  default: {
    name: "Technical",
    page: "#111114",
    text: "#E4E4E7",
    heading: "#34D399",
    sub: "#A1A1AA",
    divider: "#27272A",
    codeBg: "#000000",
    codeText: "#6EE7B7",
    chip: "#34D399",
    glow: "#10B981",
  },
  minimal: {
    name: "Minimal",
    page: "#FCFCFB",
    text: "#3F3F46",
    heading: "#18181B",
    sub: "#8A8A93",
    divider: "#E4E4E7",
    codeBg: "#F4F4F5",
    codeText: "#3F3F46",
    chip: "#18181B",
    glow: "#D4D4D8",
  },
  dark: {
    name: "Dark Mode",
    page: "#000000",
    text: "#F4F4F5",
    heading: "#FFFFFF",
    sub: "#A1A1AA",
    divider: "#27272A",
    codeBg: "#18181B",
    codeText: "#5EEAD4",
    chip: "#FFFFFF",
    glow: "#71717A",
  },
  academic: {
    name: "Academic",
    page: "#F6F1E7",
    text: "#3B3529",
    heading: "#6B2B2B",
    sub: "#8A7F68",
    divider: "#D8CFB8",
    codeBg: "#ECE4D2",
    codeText: "#5A4A2E",
    chip: "#6B2B2B",
    glow: "#B4553F",
  },
};

const DEFAULTS: PdfSettings = {
  pageFormat: "A4",
  layout: "single",
  fontFamily: "inter",
  fontSize: "medium",
  lineSpacing: "normal",
  margin: "normal",
  theme: "default",
  showCover: true,
  showHeaders: true,
};

function CardHeader({
  icon: Icon,
  title,
}: {
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  title: string;
}) {
  return (
    <div className="mb-4 flex items-center gap-2">
      <Icon className="size-3.5 text-zinc-500" strokeWidth={2} />
      <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
        {title}
      </span>
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <div className="mb-2 text-[12px] text-zinc-500">{children}</div>;
}

interface SegmentOption<T extends string> {
  value: T;
  label: string;
  font?: string;
}

function Segmented<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: SegmentOption<T>[];
  onChange: (val: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            style={opt.font ? { fontFamily: opt.font } : undefined}
            className={
              "rounded-lg border px-3 py-1.5 text-[12.5px] transition-all active:scale-95 " +
              (active
                ? "border-zinc-50 bg-zinc-50 text-zinc-950 font-semibold shadow-sm"
                : "border-zinc-800 bg-zinc-900/70 text-zinc-300 hover:border-zinc-700 hover:text-zinc-100")
            }
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

function ToggleRow({
  label,
  hint,
  checked,
  onChange,
  last,
}: {
  label: string;
  hint: string;
  checked: boolean;
  onChange: (val: boolean) => void;
  last?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={
        "group flex w-full items-center justify-between py-3 text-left " +
        (last ? "" : "border-b border-zinc-800/60")
      }
    >
      <div>
        <div className="text-[13px] text-zinc-200">{label}</div>
        <div className="mt-0.5 text-[11px] text-zinc-500">{hint}</div>
      </div>
      <span
        className={
          "relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors " +
          (checked ? "bg-emerald-400" : "bg-zinc-700 group-hover:bg-zinc-600")
        }
      >
        <span
          className="inline-block size-3.5 transform rounded-full bg-zinc-950 transition-transform"
          style={{ transform: checked ? "translateX(18px)" : "translateX(2px)" }}
        />
      </span>
    </button>
  );
}

export default function PaperChatSettingsPage() {
  const router = useRouter();
  const [settings, setSettings] = useState<PdfSettings>(DEFAULTS);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [mobileTab, setMobileTab] = useState<"controls" | "preview">("controls");

  useEffect(() => {
    const saved = readPdfSettings();
    if (saved) {
      setSettings(saved);
    }
  }, []);

  const set =
    <K extends keyof PdfSettings>(key: K) =>
    (value: PdfSettings[K]) =>
      setSettings((s) => ({ ...s, [key]: value }));

  const theme = THEMES[settings.theme];
  const fontFamily = FONT_STACKS[settings.fontFamily];
  const fontSize = FONT_SIZES[settings.fontSize];
  const lineHeight = LINE_HEIGHTS[settings.lineSpacing];
  const margin = MARGINS[settings.margin];

  const columnStyle: React.CSSProperties =
    settings.layout === "two-column"
      ? { columnCount: 2, columnGap: 20 }
      : settings.layout === "auto"
      ? { columnWidth: 150, columnGap: 18 }
      : { columnCount: 1 };

  const changedCount = (Object.keys(DEFAULTS) as (keyof PdfSettings)[]).filter(
    (k) => settings[k] !== DEFAULTS[k],
  ).length;
  const isDirty = changedCount > 0;

  const toc = [
    "What is a binary search tree?",
    "How does quicksort partition an array?",
    "What is the time complexity of merge sort?",
  ];

  const handleMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;
    setTilt({ x: px * 7, y: py * -7 });
  };
  const handleLeave = () => setTilt({ x: 0, y: 0 });

  const handleSaveAndApply = () => {
    writePdfSettings(settings);
    router.push("/");
  };

  return (
    <div className="flex min-h-screen lg:h-screen w-full flex-col lg:flex-row overflow-x-hidden bg-zinc-950 text-zinc-100">
      {/* Mobile Tab Switcher */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-zinc-800/80 bg-zinc-950/95 px-4 py-3 backdrop-blur-md lg:hidden">
        <button
          type="button"
          onClick={() => router.push("/")}
          className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200"
        >
          <ChevronLeft className="size-4" />
          Home
        </button>
        <div className="flex rounded-lg bg-zinc-900 p-1">
          <button
            type="button"
            onClick={() => setMobileTab("controls")}
            className={
              "rounded-md px-3 py-1 text-xs font-semibold transition " +
              (mobileTab === "controls"
                ? "bg-zinc-800 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200")
            }
          >
            Settings
          </button>
          <button
            type="button"
            onClick={() => setMobileTab("preview")}
            className={
              "rounded-md px-3 py-1 text-xs font-semibold transition " +
              (mobileTab === "preview"
                ? "bg-zinc-800 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200")
            }
          >
            Live Preview
          </button>
        </div>
      </div>

      {/* Sidebar */}
      <aside
        className={
          "w-full lg:w-[380px] shrink-0 flex-col border-r border-zinc-800/70 bg-zinc-950 " +
          (mobileTab === "controls" ? "flex" : "hidden lg:flex")
        }
      >
        <div className="px-5 sm:px-6 pb-4 pt-5 lg:pt-7">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="mb-4 hidden items-center gap-1 text-xs text-zinc-500 transition-colors hover:text-zinc-300 lg:flex"
          >
            <ChevronLeft className="size-3.5" />
            Back to home
          </button>
          <div className="flex items-center justify-between">
            <h1
              className="text-lg sm:text-xl font-semibold tracking-tight text-zinc-50"
            >
              Document settings
            </h1>
            {isDirty && (
              <span className="flex items-center gap-1 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2 py-0.5 text-[10.5px] font-medium text-emerald-400">
                <Sparkles className="size-3" />
                {changedCount} changed
              </span>
            )}
          </div>
          <p className="mt-1.5 text-[13px] leading-relaxed text-zinc-500">
            Configure page layout, typography, and styling before export.
          </p>
        </div>

        <div className="no-scrollbar flex-1 space-y-3 overflow-y-auto px-6 pb-5">
          <div className="rounded-2xl border border-zinc-800/60 bg-zinc-900/40 p-4">
            <CardHeader icon={FileText} title="Page setup" />
            <div className="space-y-4">
              <div>
                <FieldLabel>Page format</FieldLabel>
                <Segmented
                  value={settings.pageFormat}
                  onChange={set("pageFormat")}
                  options={[
                    { value: "A4", label: "A4" },
                    { value: "Letter", label: "US Letter" },
                    { value: "Legal", label: "US Legal" },
                  ]}
                />
              </div>
              <div>
                <FieldLabel>Column layout</FieldLabel>
                <Segmented
                  value={settings.layout}
                  onChange={set("layout")}
                  options={[
                    { value: "single", label: "Single" },
                    { value: "two-column", label: "Two col" },
                    { value: "auto", label: "Auto flow" },
                  ]}
                />
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-800/60 bg-zinc-900/40 p-4">
            <CardHeader icon={Type} title="Typography" />
            <div className="space-y-4">
              <div>
                <FieldLabel>Font family</FieldLabel>
                <Segmented
                  value={settings.fontFamily}
                  onChange={set("fontFamily")}
                  options={[
                    { value: "inter", label: "Inter", font: FONT_STACKS.inter },
                    { value: "serif", label: "Georgia", font: FONT_STACKS.serif },
                    { value: "mono", label: "JetBrains", font: FONT_STACKS.mono },
                    { value: "dyslexic", label: "OpenDyslexic", font: FONT_STACKS.dyslexic },
                  ]}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel>Font size</FieldLabel>
                  <Segmented
                    value={settings.fontSize}
                    onChange={set("fontSize")}
                    options={[
                      { value: "small", label: "Small" },
                      { value: "medium", label: "Med" },
                      { value: "large", label: "Large" },
                    ]}
                  />
                </div>
                <div>
                  <FieldLabel>Line spacing</FieldLabel>
                  <Segmented
                    value={settings.lineSpacing}
                    onChange={set("lineSpacing")}
                    options={[
                      { value: "compact", label: "Tight" },
                      { value: "normal", label: "Normal" },
                      { value: "relaxed", label: "Relaxed" },
                    ]}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-800/60 bg-zinc-900/40 p-4">
            <CardHeader icon={Move} title="Spacing" />
            <FieldLabel>Margins</FieldLabel>
            <Segmented
              value={settings.margin}
              onChange={set("margin")}
              options={[
                { value: "narrow", label: "Narrow" },
                { value: "normal", label: "Normal" },
                { value: "wide", label: "Wide" },
              ]}
            />
          </div>

          <div className="rounded-2xl border border-zinc-800/60 bg-zinc-900/40 p-4">
            <CardHeader icon={Palette} title="Document theme" />
            <div className="grid grid-cols-2 gap-2">
              {(Object.keys(THEMES) as PdfSettings["theme"][]).map((key) => {
                const t = THEMES[key];
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => set("theme")(key)}
                    className={
                      "flex items-center gap-2 rounded-xl border px-3 py-2.5 text-left transition-all active:scale-95 " +
                      (settings.theme === key
                        ? "border-zinc-50 bg-zinc-900 shadow-sm"
                        : "border-zinc-800 hover:border-zinc-700")
                    }
                  >
                    <span
                      className="size-3.5 shrink-0 rounded-full border border-zinc-700"
                      style={{ backgroundColor: t.page }}
                    />
                    <span className="text-[12.5px] text-zinc-200">{t.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-800/60 bg-zinc-900/40 p-4">
            <CardHeader icon={PanelTop} title="Page elements" />
            <ToggleRow
              label="Include cover page"
              hint="Adds a title page before contents"
              checked={settings.showCover}
              onChange={set("showCover")}
            />
            <ToggleRow
              label="Running header & footer"
              hint="Page numbers and source on every page"
              checked={settings.showHeaders}
              onChange={set("showHeaders")}
              last
            />
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-zinc-800/70 px-6 py-4">
          <button
            type="button"
            onClick={() => setSettings(DEFAULTS)}
            disabled={!isDirty}
            className={
              "flex items-center gap-1.5 text-[13px] transition-colors " +
              (isDirty ? "text-zinc-400 hover:text-zinc-200" : "cursor-not-allowed text-zinc-700")
            }
          >
            <RotateCcw className="size-3.5" />
            Reset defaults
          </button>
          <button
            type="button"
            onClick={handleSaveAndApply}
            className="flex items-center gap-1.5 rounded-lg bg-zinc-50 px-4 py-2 text-[13px] font-medium text-zinc-950 transition-all hover:bg-white active:scale-95"
          >
            <FileDown className="size-3.5" />
            Save & apply
          </button>
        </div>
      </aside>

      {/* Main Preview */}
      <main
        className={
          "relative flex-1 flex-col items-center justify-center overflow-hidden px-4 sm:px-8 lg:px-10 py-6 lg:py-10 " +
          (mobileTab === "preview" ? "flex min-h-[80vh]" : "hidden lg:flex")
        }
      >
        <div
          className="absolute inset-0 opacity-[0.12]"
          style={{
            backgroundImage: "radial-gradient(circle, #52525B 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 60% 50% at 50% 50%, rgba(0,0,0,0) 0%, rgba(9,9,11,0.9) 100%)",
          }}
        />

        <div className="relative z-10 mb-6 flex items-center gap-2 text-[12.5px] text-zinc-500">
          <span className="font-medium text-zinc-300">{settings.pageFormat}</span>
          <span className="text-zinc-700">·</span>
          <span>{PAGE_META[settings.pageFormat]}</span>
          <span className="text-zinc-700">·</span>
          <span>{THEMES[settings.theme].name}</span>
        </div>

        <div
          className="relative z-10 flex items-center justify-center"
          style={{ height: "min(74vh, 720px)" }}
          onMouseMove={handleMove}
          onMouseLeave={handleLeave}
        >
          <div
            className="absolute rounded-full transition-all duration-500"
            style={{
              width: "70%",
              height: "70%",
              backgroundColor: theme.glow,
              opacity: 0.28,
              filter: "blur(90px)",
            }}
          />

          <div
            className="relative overflow-hidden shadow-2xl transition-[background-color] duration-300"
            style={{
              height: "100%",
              aspectRatio: PAGE_RATIOS[settings.pageFormat],
              backgroundColor: theme.page,
              boxShadow: "0 30px 80px -20px rgba(0,0,0,0.8)",
              transform: `perspective(1400px) rotateY(${tilt.x}deg) rotateX(${tilt.y}deg)`,
              transition: "transform 0.2s ease-out, background-color 0.3s ease",
            }}
          >
            <div
              className="relative size-full overflow-hidden"
              style={{
                padding: margin,
                fontFamily,
                color: theme.text,
                fontSize,
                lineHeight,
              }}
            >
              {settings.showHeaders && (
                <div
                  className="mb-4 flex items-center justify-between pb-2"
                  style={{
                    fontSize: fontSize * 0.7,
                    color: theme.sub,
                    borderBottom: `1px solid ${theme.divider}`,
                  }}
                >
                  <span>Shared via PaperChat</span>
                  <span>chatgpt.com/share/8f2c1a</span>
                </div>
              )}

              {settings.showCover ? (
                <div
                  className="mb-5 text-center"
                  style={{ borderBottom: `1px solid ${theme.divider}`, paddingBottom: 16 }}
                >
                  <div
                    style={{
                      fontSize: fontSize * 1.7,
                      fontWeight: 600,
                      color: theme.heading,
                      letterSpacing: "-0.01em",
                    }}
                  >
                    Data Structures & Algorithms
                  </div>
                  <div style={{ fontSize: fontSize * 0.75, color: theme.sub, marginTop: 5 }}>
                    Generated Aug 3, 2026 · 3 topics
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    fontSize: fontSize * 1.3,
                    fontWeight: 600,
                    color: theme.heading,
                    marginBottom: 14,
                  }}
                >
                  Data Structures & Algorithms
                </div>
              )}

              <div style={{ marginBottom: 18 }}>
                <div
                  style={{
                    fontSize: fontSize * 0.75,
                    color: theme.chip,
                    fontWeight: 600,
                    letterSpacing: "0.06em",
                    marginBottom: 7,
                  }}
                >
                  CONTENTS
                </div>
                {toc.map((t, i) => (
                  <div key={t} style={{ fontSize: fontSize * 0.9, color: theme.text, marginBottom: 3 }}>
                    {i + 1}. {t}
                  </div>
                ))}
              </div>

              <div style={columnStyle}>
                <div style={{ breakInside: "avoid", marginBottom: 16 }}>
                  <div style={{ fontWeight: 600, color: theme.heading, marginBottom: 5 }}>
                    1. {toc[0]}
                  </div>
                  <p style={{ margin: 0 }}>
                    A binary search tree keeps every left descendant smaller than
                    its parent and every right descendant larger, which gives
                    average-case O(log n) lookup, insertion, and deletion.
                  </p>
                </div>

                <div style={{ breakInside: "avoid", marginBottom: 16 }}>
                  <div style={{ fontWeight: 600, color: theme.heading, marginBottom: 5 }}>
                    2. {toc[1]}
                  </div>
                  <p style={{ margin: 0, marginBottom: 7 }}>
                    Quicksort picks a pivot, then partitions the array so smaller
                    elements land left and larger ones land right:
                  </p>
                  <div
                    style={{
                      backgroundColor: theme.codeBg,
                      color: theme.codeText,
                      fontFamily: FONT_STACKS.mono,
                      fontSize: fontSize * 0.8,
                      padding: "9px 11px",
                      borderRadius: 6,
                    }}
                  >
                    while (i &lt;= j) &#123; swap(arr[i++], arr[j--]) &#125;
                  </div>
                </div>

                <div style={{ breakInside: "avoid" }}>
                  <div style={{ fontWeight: 600, color: theme.heading, marginBottom: 5 }}>
                    3. {toc[2]}
                  </div>
                  <p style={{ margin: 0 }}>
                    Merge sort splits the array in half recursively, then merges
                    sorted halves back together in linear time, giving O(n log n)
                    in every case.
                  </p>
                </div>
              </div>

              {settings.showHeaders && (
                <div
                  className="absolute flex items-center justify-between"
                  style={{
                    bottom: margin * 0.4,
                    left: margin,
                    right: margin,
                    fontSize: fontSize * 0.65,
                    color: theme.sub,
                  }}
                >
                  <span>PaperChat</span>
                  <span>Page 1 of 3</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
