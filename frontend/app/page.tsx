"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ApiStatus {
  status: string;
  environment: string;
  db: string;
}

function StatusBadge({ db }: { db: string | null }) {
  if (db === null)
    return (
      <span id="api-status-loading" className="inline-flex items-center gap-2 text-sm text-gray-400">
        <span className="h-2 w-2 rounded-full bg-gray-500 animate-pulse" />
        Checking API…
      </span>
    );
  if (db === "connected")
    return (
      <span id="api-status-connected" className="inline-flex items-center gap-2 text-sm text-emerald-400">
        <span className="h-2 w-2 rounded-full bg-emerald-400" />
        API online · DB connected
      </span>
    );
  return (
    <span id="api-status-offline" className="inline-flex items-center gap-2 text-sm text-amber-400">
      <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
      API online · DB not connected (run docker-compose up)
    </span>
  );
}

const features = [
  {
    icon: "🪑",
    title: "Seat Allocation",
    desc: "Allocate, release, and track seats across 5 floors and 10 zones for 5,000+ employees.",
  },
  {
    icon: "📋",
    title: "Project Mapping",
    desc: "Map employees to projects. View team locations, utilization, and pending joiners at a glance.",
  },
  {
    icon: "📊",
    title: "Live Dashboard",
    desc: "Real-time summary: total seats, occupied, available, reserved — by floor, zone, and project.",
  },
  {
    icon: "🤖",
    title: "AI Assistant",
    desc: "Natural-language queries: \"Where is Amit seated?\" or \"Show available seats on Floor 3.\"",
  },
];

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [fetchError, setFetchError] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => r.json())
      .then((data: ApiStatus) => setApiStatus(data))
      .catch(() => setFetchError(true));
  }, []);

  return (
    <main className="relative min-h-screen overflow-hidden">
      {/* ── Background orbs ────────────────────────────────────── */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div
          className="animate-float animate-pulse-glow absolute -top-40 -left-40 h-[600px] w-[600px] rounded-full"
          style={{
            background:
              "radial-gradient(circle, rgba(99,102,241,0.18) 0%, transparent 70%)",
          }}
        />
        <div
          className="animate-float animate-pulse-glow absolute -bottom-40 -right-40 h-[500px] w-[500px] rounded-full delay-300"
          style={{
            background:
              "radial-gradient(circle, rgba(6,182,212,0.15) 0%, transparent 70%)",
            animationDelay: "2s",
          }}
        />
        <div
          className="animate-pulse-glow absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[800px] w-[800px] rounded-full"
          style={{
            background:
              "radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 60%)",
          }}
        />
      </div>

      {/* ── Grid overlay ─────────────────────────────────────────── */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.8) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.8) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* ── Navbar ───────────────────────────────────────────────── */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 animate-fade-in">
        <div className="flex items-center gap-3">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-xl text-lg font-bold"
            style={{
              background: "linear-gradient(135deg, #6366f1, #06b6d4)",
            }}
          >
            E
          </div>
          <span className="text-lg font-semibold tracking-tight text-white">
            Ethara
          </span>
        </div>

        <div className="flex items-center gap-6 text-sm text-gray-400">
          <a
            id="nav-api-docs"
            href={`${API_URL}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-white"
          >
            API Docs
          </a>
          <a
            id="nav-health"
            href={`${API_URL}/health`}
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-white"
          >
            Health
          </a>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-4xl px-8 pt-24 pb-20 text-center">
        {/* Status badge */}
        <div className="animate-slide-up mb-8 flex justify-center">
          <div
            className="rounded-full px-4 py-1.5 text-xs font-medium tracking-wide"
            style={{
              background: "rgba(99,102,241,0.12)",
              border: "1px solid rgba(99,102,241,0.3)",
              color: "#a5b4fc",
            }}
          >
            Scaffold v0.1 · Next.js + FastAPI + PostgreSQL
          </div>
        </div>

        <h1
          className="animate-slide-up delay-100 text-5xl font-extrabold tracking-tight leading-tight sm:text-6xl md:text-7xl"
          style={{
            background: "linear-gradient(135deg, #e0e7ff 0%, #a5b4fc 40%, #67e8f9 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          Ethara Seat
          <br />
          Allocation System
        </h1>

        <p className="animate-slide-up delay-200 mt-6 text-lg leading-relaxed text-gray-400 sm:text-xl max-w-2xl mx-auto">
          Full-stack platform for managing seat allocation and project mapping
          for <span className="text-white font-medium">5,000+ employees</span>{" "}
          across multiple floors and zones — with an AI-powered assistant.
        </p>

        {/* API status */}
        <div className="animate-slide-up delay-300 mt-8 flex justify-center">
          {fetchError ? (
            <span id="api-status-error" className="inline-flex items-center gap-2 text-sm text-red-400">
              <span className="h-2 w-2 rounded-full bg-red-400" />
              Cannot reach API at {API_URL}
            </span>
          ) : (
            <StatusBadge db={apiStatus?.db ?? null} />
          )}
        </div>

        {/* CTA buttons */}
        <div className="animate-slide-up delay-400 mt-10 flex flex-wrap justify-center gap-4">
          <a
            id="cta-api-docs"
            href={`${API_URL}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-white transition-all duration-200 hover:scale-105 hover:shadow-lg"
            style={{
              background: "linear-gradient(135deg, #6366f1, #4f46e5)",
              boxShadow: "0 0 20px rgba(99,102,241,0.3)",
            }}
          >
            View API Docs
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
          <a
            id="cta-health"
            href={`${API_URL}/health`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-gray-300 transition-all duration-200 hover:scale-105 hover:text-white"
            style={{
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.1)",
            }}
          >
            Check Health
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </a>
        </div>
      </section>

      {/* ── Feature cards ─────────────────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-5xl px-8 pb-24">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f, i) => (
            <div
              key={f.title}
              id={`feature-${f.title.toLowerCase().replace(/\s+/g, "-")}`}
              className="animate-slide-up rounded-2xl p-6 transition-all duration-300 hover:scale-[1.02] hover:shadow-xl"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
                animationDelay: `${0.5 + i * 0.1}s`,
                backdropFilter: "blur(8px)",
              }}
            >
              <div className="mb-4 text-3xl">{f.icon}</div>
              <h2 className="mb-2 text-base font-semibold text-white">{f.title}</h2>
              <p className="text-sm leading-relaxed text-gray-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="relative z-10 border-t px-8 py-6 text-center text-xs text-gray-600" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        Ethara Seat Allocation & Project Mapping System · Scaffold v0.1 ·{" "}
        <a
          href={`${API_URL}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-gray-400 transition-colors"
        >
          FastAPI Swagger
        </a>
      </footer>
    </main>
  );
}
