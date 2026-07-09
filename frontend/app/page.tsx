"use client";

import { useEffect, useState, useRef } from "react";

// ── Types ──────────────────────────────────────────────────────────────────────
interface HealthData {
  status: string;
  db: string;
  environment?: string;
}

interface DashboardStats {
  employees: number;
  projects: number;
  total_seats: number;
  occupied_seats: number;
  available_seats: number;
  reserved_seats: number;
  active_allocations: number;
  occupancy_percentage: number;
}

interface SeatItem {
  id: string;
  floor: number;
  zone: string;
  bay: string;
  seat_number: string;
  status: "available" | "occupied" | "reserved" | "maintenance";
}

// ── Constants ──────────────────────────────────────────────────────────────────
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Helpers ────────────────────────────────────────────────────────────────────
function fmt(n: number): string {
  return n.toLocaleString("en-US");
}

function useCountUp(target: number, duration = 1000, active = true): number {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!active || target === 0) return;
    const start = performance.now();
    const raf = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      setVal(Math.round(ease * target));
      if (t < 1) requestAnimationFrame(raf);
    };
    requestAnimationFrame(raf);
  }, [target, duration, active]);
  return active ? val : target;
}

// ── OccupancyRing ──────────────────────────────────────────────────────────────
function OccupancyRing({ pct, loaded }: { pct: number; loaded: boolean }) {
  const radius = 80;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (pct / 100) * circ;

  // Color by occupancy
  const color =
    pct >= 90 ? "#FF4D6D" : pct >= 70 ? "#FFB800" : "#9B5DE5";
  const glow =
    pct >= 90
      ? "rgba(255,77,109,0.3)"
      : pct >= 70
      ? "rgba(255,184,0,0.3)"
      : "rgba(155,93,229,0.3)";

  const animated = useCountUp(Math.round(pct * 100) / 100, 1200, loaded);

  return (
    <div className="relative flex flex-col items-center justify-center">
      {/* Ambient glow behind ring */}
      <div
        className="absolute rounded-full"
        style={{
          width: 200,
          height: 200,
          background: `radial-gradient(ellipse at center, ${glow} 0%, transparent 70%)`,
          filter: "blur(20px)",
          animation: "pulse-glow 3s ease-in-out infinite",
        }}
      />
      <svg width={200} height={200} style={{ transform: "rotate(-90deg)" }}>
        {/* Outer tick marks */}
        {Array.from({ length: 36 }).map((_, i) => {
          const angle = (i / 36) * 2 * Math.PI;
          const x1 = 100 + 96 * Math.cos(angle);
          const y1 = 100 + 96 * Math.sin(angle);
          const x2 = 100 + (i % 3 === 0 ? 88 : 92) * Math.cos(angle);
          const y2 = 100 + (i % 3 === 0 ? 88 : 92) * Math.sin(angle);
          return (
            <line
              key={i}
              x1={x1} y1={y1} x2={x2} y2={y2}
              stroke={i % 3 === 0 ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.05)"}
              strokeWidth={i % 3 === 0 ? 1.5 : 1}
            />
          );
        })}
        {/* Track */}
        <circle cx={100} cy={100} r={radius} className="ring-track" />
        {/* Fill */}
        <circle
          cx={100}
          cy={100}
          r={radius}
          className="ring-fill"
          stroke={color}
          strokeDasharray={circ}
          strokeDashoffset={loaded ? offset : circ}
          style={{
            filter: `drop-shadow(0 0 8px ${color})`,
            transition: "stroke-dashoffset 1.4s cubic-bezier(0.22,1,0.36,1), stroke 0.4s ease",
          }}
        />
      </svg>
      {/* Center label */}
      <div className="absolute flex flex-col items-center">
        <span
          className="metric-num font-bold text-4xl"
          style={{ color, textShadow: `0 0 24px ${glow}` }}
        >
          {loaded ? animated.toFixed(1) : "—"}%
        </span>
        <span className="text-xs uppercase tracking-[0.2em] mt-1" style={{ color: "var(--text-muted)" }}>
          Occupancy
        </span>
      </div>
    </div>
  );
}

// ── SkeletonBox ────────────────────────────────────────────────────────────────
function SkeletonBox({ className = "", style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={`skeleton rounded-lg ${className}`} style={style} />;
}

// ── MetricCard ─────────────────────────────────────────────────────────────────
interface MetricCardProps {
  label: string;
  value: number;
  sub?: string;
  color: string;
  glow: string;
  dim: string;
  loaded: boolean;
  delay?: string;
  icon: React.ReactNode;
}

function MetricCard({ label, value, sub, color, dim, loaded, delay = "", icon }: MetricCardProps) {
  const animated = useCountUp(value, 900, loaded);
  return (
    <div
      className={`glass-card rounded-2xl p-5 relative overflow-hidden animate-slide-up ${delay}`}
      style={{ boxShadow: `0 0 0 1px rgba(255,255,255,0.04) inset, 0 4px 32px rgba(0,0,0,0.5)` }}
    >
      {/* Glow sweep */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: `radial-gradient(ellipse 60% 50% at 50% 0%, ${dim} 0%, transparent 70%)` }}
      />
      {/* Top bar */}
      <div className="flex items-center justify-between mb-4">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: dim, border: `1px solid ${color}22` }}
        >
          {icon}
        </div>
        <span className="text-[10px] uppercase tracking-[0.18em]" style={{ color: "var(--text-muted)" }}>
          live
        </span>
      </div>
      {/* Value */}
      {loaded ? (
        <p className="metric-num font-bold text-3xl animate-count-up" style={{ color }}>
          {fmt(animated)}
        </p>
      ) : (
        <SkeletonBox className="h-9 w-28 mb-1" />
      )}
      <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{label}</p>
      {sub && loaded && (
        <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{sub}</p>
      )}
      {/* Bottom accent */}
      <div
        className="absolute bottom-0 left-0 right-0 h-px"
        style={{ background: `linear-gradient(90deg, transparent, ${color}44, transparent)` }}
      />
    </div>
  );
}

// ── FloorMapDot ────────────────────────────────────────────────────────────────
function FloorMapDot({ seat }: { seat: SeatItem }) {
  const label = `Floor ${seat.floor} · Zone ${seat.zone} · ${seat.bay} · ${seat.seat_number} · ${seat.status}`;
  return (
    <div
      title={label}
      className={`seat-dot ${seat.status}`}
    />
  );
}

// ── HealthBadge ────────────────────────────────────────────────────────────────
function HealthBadge({ health, loaded }: { health: HealthData | null; loaded: boolean }) {
  if (!loaded) return <SkeletonBox className="h-6 w-28 rounded-full" />;
  const ok = health?.status === "ok" && health?.db === "connected";
  return (
    <div
      className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
      style={{
        background: ok ? "rgba(0,214,143,0.1)" : "rgba(255,77,109,0.1)",
        border: `1px solid ${ok ? "rgba(0,214,143,0.25)" : "rgba(255,77,109,0.25)"}`,
        color: ok ? "var(--green)" : "var(--red)",
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full animate-blink"
        style={{ background: ok ? "var(--green)" : "var(--red)" }}
      />
      {ok ? "ALL SYSTEMS OPERATIONAL" : "DEGRADED"}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [stats, setStats]   = useState<DashboardStats | null>(null);
  const [seats, setSeats]   = useState<SeatItem[]>([]);

  const [healthLoaded, setHealthLoaded] = useState(false);
  const [statsLoaded,  setStatsLoaded]  = useState(false);
  const [seatsLoaded,  setSeatsLoaded]  = useState(false);

  const [currentTime, setCurrentTime] = useState("");
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Clock ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    const tick = () =>
      setCurrentTime(
        new Date().toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    tick();
    tickRef.current = setInterval(tick, 1000);
    return () => { if (tickRef.current) clearInterval(tickRef.current); };
  }, []);

  // ── Health poll (every 15 s) ───────────────────────────────────────────────
  useEffect(() => {
    const fetch_health = async () => {
      try {
        const r = await fetch(`${API_BASE}/health`);
        if (r.ok) setHealth(await r.json());
      } catch {
        setHealth({ status: "error", db: "unreachable" });
      } finally {
        setHealthLoaded(true);
      }
    };
    fetch_health();
    const id = setInterval(fetch_health, 15_000);
    return () => clearInterval(id);
  }, []);

  // ── Dashboard stats ────────────────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/dashboard/stats`);
        if (r.ok) setStats(await r.json());
      } catch { /* keep null */ }
      finally { setStatsLoaded(true); }
    })();
  }, []);

  // ── Seat map (first 100) ───────────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/seats/`);
        if (r.ok) {
          const data: SeatItem[] = await r.json();
          setSeats(data.slice(0, 100));
        }
      } catch { /* keep empty */ }
      finally { setSeatsLoaded(true); }
    })();
  }, []);

  const pct = stats?.occupancy_percentage ?? 0;

  // Floor breakdown from seat dots
  const floors = [1, 2, 3, 4, 5];
  const seatsByFloor = (f: number) => seats.filter((s) => s.floor === f);

  return (
    <div
      className="min-h-screen relative"
      style={{
        background: "var(--canvas)",
        backgroundImage: `
          radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,245,255,0.07) 0%, transparent 60%),
          radial-gradient(ellipse 60% 40% at 90% 100%, rgba(155,93,229,0.06) 0%, transparent 60%),
          linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.012) 1px, transparent 1px)
        `,
        backgroundSize: "100% 100%, 100% 100%, 32px 32px, 32px 32px",
      }}
    >
      {/* ── Top chrome bar ───────────────────────────────────────────────── */}
      <div
        className="border-b flex items-center justify-between px-6 py-3"
        style={{ borderColor: "rgba(255,255,255,0.05)", background: "rgba(11,15,25,0.8)", backdropFilter: "blur(12px)" }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div
            className="w-7 h-7 rounded-md flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #00F5FF22, #9B5DE522)", border: "1px solid rgba(0,245,255,0.2)" }}
          >
            <svg width={14} height={14} viewBox="0 0 14 14" fill="none">
              <rect x={1} y={1} width={5} height={5} rx={1} fill="#00F5FF" fillOpacity={0.8} />
              <rect x={8} y={1} width={5} height={5} rx={1} fill="#9B5DE5" fillOpacity={0.8} />
              <rect x={1} y={8} width={5} height={5} rx={1} fill="#9B5DE5" fillOpacity={0.5} />
              <rect x={8} y={8} width={5} height={5} rx={1} fill="#FFB800" fillOpacity={0.8} />
            </svg>
          </div>
          <span className="text-sm font-semibold tracking-widest" style={{ color: "var(--text-secondary)", letterSpacing: "0.22em" }}>
            ETHARA <span style={{ color: "rgba(255,255,255,0.15)" }}>//</span>{" "}
            <span className="gradient-brand">SEAT CORE</span>
          </span>
        </div>

        {/* Right cluster */}
        <div className="flex items-center gap-4">
          <HealthBadge health={health} loaded={healthLoaded} />
          <div
            className="text-xs font-mono px-3 py-1.5 rounded-md"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", color: "var(--text-muted)", letterSpacing: "0.1em" }}
          >
            {currentTime || "––:––:––"}
          </div>
          {/* Env chip */}
          {health?.environment && (
            <span
              className="text-[10px] uppercase tracking-widest px-2 py-1 rounded"
              style={{ background: "rgba(0,245,255,0.06)", color: "var(--cyan)", border: "1px solid rgba(0,245,255,0.12)" }}
            >
              {health.environment}
            </span>
          )}
        </div>
      </div>

      {/* ── Page body ─────────────────────────────────────────────────────── */}
      <div className="max-w-[1400px] mx-auto px-6 py-8 space-y-8">

        {/* ── Section heading ───────────────────────────────────────────── */}
        <div className="animate-slide-up">
          <div className="flex items-baseline gap-3 mb-1">
            <h1 className="text-2xl font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>
              Executive Cockpit
            </h1>
            <span className="text-xs px-2 py-0.5 rounded tracking-widest uppercase"
              style={{ background: "rgba(155,93,229,0.1)", color: "var(--purple)", border: "1px solid rgba(155,93,229,0.2)" }}>
              Live
            </span>
          </div>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            Real-time capacity overview · {stats ? fmt(stats.employees) : "—"} employees · {stats ? fmt(stats.projects) : "—"} active projects
          </p>
        </div>

        {/* ── Primary analytics row ─────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-[auto_1fr] gap-6">

          {/* Occupancy ring card */}
          <div
            className="glass-card rounded-2xl p-8 flex flex-col items-center justify-center animate-slide-up delay-100 relative overflow-hidden"
            style={{ minWidth: 280, boxShadow: "0 0 0 1px rgba(255,255,255,0.04) inset, 0 8px 48px rgba(0,0,0,0.6)" }}
          >
            {/* Background glow sweep */}
            <div className="absolute inset-0 pointer-events-none"
              style={{ background: "radial-gradient(ellipse 80% 60% at 50% 100%, rgba(155,93,229,0.08) 0%, transparent 70%)" }} />

            <p className="text-[10px] uppercase tracking-[0.25em] mb-6" style={{ color: "var(--text-muted)" }}>
              Seat Utilisation
            </p>

            {statsLoaded ? (
              <OccupancyRing pct={pct} loaded={statsLoaded} />
            ) : (
              <div className="skeleton rounded-full" style={{ width: 200, height: 200 }} />
            )}

            {/* Legend */}
            <div className="flex gap-5 mt-6">
              {[
                { label: "Occupied", color: "var(--purple)" },
                { label: "Available", color: "var(--cyan)" },
                { label: "Reserved", color: "var(--amber)" },
              ].map(({ label, color }) => (
                <div key={label} className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ background: color }} />
                  <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Metric cards grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {/* Total seats */}
            <MetricCard
              label="Total Capacity"
              value={stats?.total_seats ?? 0}
              sub={`${stats?.projects ?? 0} active projects`}
              color="var(--text-primary)"
              glow="rgba(255,255,255,0.15)"
              dim="rgba(255,255,255,0.03)"
              loaded={statsLoaded}
              delay="delay-150"
              icon={<svg width={16} height={16} viewBox="0 0 16 16" fill="none"><rect x={1} y={1} width={6} height={6} rx={1} fill="rgba(255,255,255,0.6)"/><rect x={9} y={1} width={6} height={6} rx={1} fill="rgba(255,255,255,0.3)"/><rect x={1} y={9} width={6} height={6} rx={1} fill="rgba(255,255,255,0.3)"/><rect x={9} y={9} width={6} height={6} rx={1} fill="rgba(255,255,255,0.6)"/></svg>}
            />
            {/* Active allocations */}
            <MetricCard
              label="Active Allocations"
              value={stats?.active_allocations ?? 0}
              sub="currently seated"
              color="var(--purple)"
              glow="rgba(155,93,229,0.3)"
              dim="rgba(155,93,229,0.08)"
              loaded={statsLoaded}
              delay="delay-200"
              icon={<svg width={16} height={16} viewBox="0 0 16 16" fill="none"><circle cx={8} cy={5} r={3} fill="#9B5DE5" fillOpacity={0.9}/><path d="M2 14c0-3.314 2.686-5 6-5s6 1.686 6 5" stroke="#9B5DE5" strokeWidth={1.5} strokeLinecap="round"/></svg>}
            />
            {/* Available seats */}
            <MetricCard
              label="Open Desks"
              value={stats?.available_seats ?? 0}
              sub="ready to allocate"
              color="var(--cyan)"
              glow="rgba(0,245,255,0.3)"
              dim="rgba(0,245,255,0.08)"
              loaded={statsLoaded}
              delay="delay-300"
              icon={<svg width={16} height={16} viewBox="0 0 16 16" fill="none"><circle cx={8} cy={8} r={6} stroke="#00F5FF" strokeWidth={1.5} strokeOpacity={0.8}/><path d="M5.5 8.5l2 2 3-4" stroke="#00F5FF" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"/></svg>}
            />
            {/* Employees */}
            <MetricCard
              label="Total Employees"
              value={stats?.employees ?? 0}
              color="var(--amber)"
              glow="rgba(255,184,0,0.3)"
              dim="rgba(255,184,0,0.08)"
              loaded={statsLoaded}
              delay="delay-400"
              icon={<svg width={16} height={16} viewBox="0 0 16 16" fill="none"><circle cx={5.5} cy={5} r={2.5} fill="#FFB800" fillOpacity={0.8}/><circle cx={10.5} cy={5} r={2.5} fill="#FFB800" fillOpacity={0.5}/><path d="M1 14c0-2.485 2.015-4 4.5-4s4.5 1.515 4.5 4" stroke="#FFB800" strokeWidth={1.5} strokeLinecap="round"/><path d="M10.5 10c1.5 0 4 0.8 4 4" stroke="#FFB800" strokeWidth={1.5} strokeLinecap="round" strokeOpacity={0.6}/></svg>}
            />
            {/* Reserved */}
            <MetricCard
              label="Reserved / Blocked"
              value={stats?.reserved_seats ?? 0}
              color="rgba(255,255,255,0.35)"
              glow="rgba(255,255,255,0.1)"
              dim="rgba(255,255,255,0.02)"
              loaded={statsLoaded}
              delay="delay-500"
              icon={<svg width={16} height={16} viewBox="0 0 16 16" fill="none"><rect x={2} y={7} width={12} height={7} rx={1.5} stroke="rgba(255,255,255,0.4)" strokeWidth={1.5}/><path d="M5 7V5a3 3 0 016 0v2" stroke="rgba(255,255,255,0.4)" strokeWidth={1.5} strokeLinecap="round"/></svg>}
            />
            {/* Occupancy % */}
            <div
              className="glass-card rounded-2xl p-5 relative overflow-hidden animate-slide-up delay-600 flex flex-col justify-between"
              style={{ boxShadow: "0 0 0 1px rgba(255,255,255,0.04) inset, 0 4px 24px rgba(0,0,0,0.4)" }}
            >
              <div style={{ background: "rgba(0,245,255,0.03)" }} className="absolute inset-0 pointer-events-none" />
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] uppercase tracking-[0.2em]" style={{ color: "var(--text-muted)" }}>Occupancy Rate</span>
                <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 rounded"
                  style={{ background: "rgba(0,245,255,0.06)", color: "var(--cyan)", border: "1px solid rgba(0,245,255,0.12)" }}>live</span>
              </div>
              {statsLoaded ? (
                <>
                  <p className="metric-num font-bold text-3xl" style={{ color: "var(--cyan)" }}>
                    {pct.toFixed(2)}%
                  </p>
                  {/* Mini progress bar */}
                  <div className="mt-3 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${pct}%`,
                        background: "linear-gradient(90deg, #9B5DE5, #00F5FF)",
                        boxShadow: "0 0 8px rgba(0,245,255,0.4)",
                        transition: "width 1.4s cubic-bezier(0.22,1,0.36,1)",
                      }}
                    />
                  </div>
                  <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
                    {fmt(stats?.occupied_seats ?? 0)} of {fmt(stats?.total_seats ?? 0)} seats in use
                  </p>
                </>
              ) : (
                <>
                  <SkeletonBox className="h-9 w-24 mb-2" />
                  <SkeletonBox className="h-1.5 w-full" />
                </>
              )}
              <div className="absolute bottom-0 left-0 right-0 h-px"
                style={{ background: "linear-gradient(90deg, transparent, rgba(0,245,255,0.3), transparent)" }} />
            </div>
          </div>
        </div>

        {/* ── Live Floor Map ────────────────────────────────────────────── */}
        <div
          className="glass-card rounded-2xl p-6 animate-slide-up delay-500 relative overflow-hidden"
          style={{ boxShadow: "0 0 0 1px rgba(255,255,255,0.04) inset, 0 8px 48px rgba(0,0,0,0.5)" }}
        >
          {/* Background glow */}
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: "radial-gradient(ellipse 60% 40% at 50% 100%, rgba(0,245,255,0.04) 0%, transparent 70%)" }} />

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-1.5 h-1.5 rounded-full animate-blink" style={{ background: "var(--cyan)" }} />
                <h2 className="text-sm font-semibold tracking-widest uppercase" style={{ color: "var(--text-secondary)" }}>
                  Live Floor Map Preview
                </h2>
              </div>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                First 100 seats · real-time status · hover for details
              </p>
            </div>
            {/* Legend */}
            <div className="flex items-center gap-4">
              {[
                { label: "Available", cls: "available" },
                { label: "Occupied",  cls: "occupied"  },
                { label: "Reserved",  cls: "reserved"  },
              ].map(({ label, cls }) => (
                <div key={cls} className="flex items-center gap-1.5">
                  <div className={`seat-dot ${cls}`} style={{ width: 8, height: 8 }} />
                  <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Floor rows */}
          {seatsLoaded ? (
            seats.length > 0 ? (
              <div className="space-y-4">
                {floors.map((f) => {
                  const floorSeats = seatsByFloor(f);
                  if (floorSeats.length === 0) return null;
                  const floorOccupied = floorSeats.filter((s) => s.status === "occupied").length;
                  const floorPct = Math.round((floorOccupied / floorSeats.length) * 100);
                  return (
                    <div key={f} className="flex items-center gap-4">
                      {/* Floor label */}
                      <div className="w-14 flex-shrink-0">
                        <p className="text-[10px] uppercase tracking-[0.15em]" style={{ color: "var(--text-muted)" }}>
                          Floor {f}
                        </p>
                        <p className="text-[10px] metric-num" style={{ color: "var(--purple)" }}>{floorPct}%</p>
                      </div>
                      {/* Separator */}
                      <div className="w-px h-8 self-center" style={{ background: "rgba(255,255,255,0.06)" }} />
                      {/* Dots */}
                      <div className="flex flex-wrap gap-1">
                        {floorSeats.map((seat) => (
                          <FloorMapDot key={seat.id} seat={seat} />
                        ))}
                      </div>
                    </div>
                  );
                })}
                {/* Summary bar */}
                <div
                  className="mt-4 pt-4 flex items-center justify-between text-xs"
                  style={{ borderTop: "1px solid rgba(255,255,255,0.05)", color: "var(--text-muted)" }}
                >
                  <span>Showing {seats.length} of {fmt(stats?.total_seats ?? 0)} total seats</span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full animate-blink" style={{ background: "var(--cyan)" }} />
                    Updated just now
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 gap-3">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <svg width={20} height={20} viewBox="0 0 20 20" fill="none">
                    <rect x={2} y={2} width={7} height={7} rx={1} fill="rgba(255,255,255,0.15)"/>
                    <rect x={11} y={2} width={7} height={7} rx={1} fill="rgba(255,255,255,0.08)"/>
                    <rect x={2} y={11} width={7} height={7} rx={1} fill="rgba(255,255,255,0.08)"/>
                    <rect x={11} y={11} width={7} height={7} rx={1} fill="rgba(255,255,255,0.05)"/>
                  </svg>
                </div>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>No seat data available</p>
                <p className="text-xs" style={{ color: "var(--text-muted)", opacity: 0.6 }}>Ensure the API is running on port 8000</p>
              </div>
            )
          ) : (
            // Skeleton
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-4">
                  <SkeletonBox className="w-14 h-8 flex-shrink-0" />
                  <div className="flex flex-wrap gap-1">
                    {Array.from({ length: 20 }).map((_, j) => (
                      <SkeletonBox key={j} style={{ width: 6, height: 6, borderRadius: 2 }} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── AI Query teaser ────────────────────────────────────────────── */}
        <div
          className="glass-card rounded-2xl p-6 animate-slide-up delay-700 relative overflow-hidden"
          style={{ boxShadow: "0 0 0 1px rgba(255,255,255,0.04) inset, 0 4px 24px rgba(0,0,0,0.4)" }}
        >
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: "radial-gradient(ellipse 50% 60% at 0% 50%, rgba(155,93,229,0.06) 0%, transparent 70%)" }} />
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: "rgba(155,93,229,0.12)", border: "1px solid rgba(155,93,229,0.2)" }}>
              <svg width={16} height={16} viewBox="0 0 16 16" fill="none">
                <path d="M8 2L10 6H14L11 9L12 13L8 11L4 13L5 9L2 6H6L8 2Z" fill="#9B5DE5" fillOpacity={0.85}/>
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>AI Assistant</p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>POST /ai/query · natural language seat lookup</p>
            </div>
          </div>
          <div
            className="rounded-xl p-4 font-mono text-sm"
            style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(155,93,229,0.12)", color: "var(--text-secondary)" }}
          >
            <span style={{ color: "var(--purple)", opacity: 0.7 }}>POST</span>{" "}
            <span style={{ color: "var(--text-muted)" }}>/ai/query</span>
            <br />
            <span style={{ color: "var(--text-muted)" }}>{`{ "query": "Where is `}</span>
            <span style={{ color: "var(--cyan)" }}>{"jane.smith@ethara.com"}</span>
            <span style={{ color: "var(--text-muted)" }}>{`" }`}</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-px"
            style={{ background: "linear-gradient(90deg, transparent, rgba(155,93,229,0.3), transparent)" }} />
        </div>

        {/* ── Footer ─────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between pt-2 pb-6">
          <p className="text-xs" style={{ color: "var(--text-muted)", opacity: 0.5 }}>
            Ethara Seat Core · v0.1.0
          </p>
          <p className="text-xs font-mono" style={{ color: "var(--text-muted)", opacity: 0.5 }}>
            {API_BASE}
          </p>
        </div>
      </div>
    </div>
  );
}
