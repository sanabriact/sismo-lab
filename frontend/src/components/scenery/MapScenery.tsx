import { useState } from "react";
import type { SeismicMapProps } from "../../models/interfaces/scenery/SeismicMapProps";
import { toFormatId } from "../../utils/seism/toFormatId";
import { yScreen } from "../../utils/seism/yScreen";
import { magnitudeByRadio } from "../../utils/seism/magnitudeByRadio";

const SIZE = 1000;
const MARGIN = { top: 24, right: 24, bottom: 48, left: 64 };
const VIEW_W = MARGIN.left + SIZE + MARGIN.right;
const VIEW_H = MARGIN.top + SIZE + MARGIN.bottom;
const TICKS = Array.from({ length: 11 }, (_, i) => i * 100);

const PRIORITY_COLOR: Record<number, string> = {
    1: "#7fbf8e",
    2: "#f0b64a",
    3: "#ef5b45"
}

/* Palette used only for presentation of the plane. */
const PLOT = {
    axis: "#8a9bb8",
    tick: "#6f7f9c",
    title: "#b7c3d9",
    gridMajor: "#2a3b5a",
    gridMinor: "#17233b",
    populatedFill: "rgba(245,166,35,0.13)",
    populatedStroke: "#f5a623",
    emptyStroke: "#5b6b88",
    pending: "#f1f5f9",
    reviewed: "#64748b",
    costly: "#fb7185",
    selected: "#38bdf8",
};

export default function MapScenery({ zones, events, selectedEventId = null, onSelectEvent }: SeismicMapProps) {
    const [hoverId, setOnHover] = useState<number | null>(null);

    return (
        <div className="flex h-screen w-full flex-col gap-5 bg-gradient-to-br from-[#0b1426] via-[#060b17] to-[#03060d] p-5 lg:flex-row">
            <div
                className="relative flex min-h-0 min-w-0 flex-1 items-center justify-center overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900 via-slate-950 to-[#070c18] p-4 shadow-2xl shadow-black/50 ring-1 ring-inset ring-white/5"
            >
                <svg
                    viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
                    className="h-full w-full select-none"
                    role="img"
                    aria-label="Plano geográfico del observatorio sísmico"
                >
                    <defs>
                        <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
                            <feGaussianBlur stdDeviation="5" result="blur" />
                            <feMerge>
                                <feMergeNode in="blur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>

                        <radialGradient id="plot-bg" cx="50%" cy="45%" r="75%">
                            <stop offset="0%" stopColor="#13213d" />
                            <stop offset="100%" stopColor="#0a1120" />
                        </radialGradient>

                        <pattern id="zone-hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                            <line x1="0" y1="0" x2="0" y2="10" stroke="#64748b" strokeOpacity="0.22" strokeWidth="1.5" />
                        </pattern>
                    </defs>

                    {/* Plot surface */}
                    <rect
                        x={MARGIN.left}
                        y={MARGIN.top}
                        width={SIZE}
                        height={SIZE}
                        rx={6}
                        fill="url(#plot-bg)"
                    />

                    {/* Grid */}
                    {TICKS.map((t) => (
                        <g key={`grid-${t}`}>
                            <line
                                x1={MARGIN.left + t}
                                y1={MARGIN.top}
                                x2={MARGIN.left + t}
                                y2={MARGIN.top + SIZE}
                                stroke={t % 500 === 0 ? PLOT.gridMajor : PLOT.gridMinor}
                                strokeWidth={t % 500 === 0 ? 1.25 : 0.75}
                            />
                            <line
                                x1={MARGIN.left}
                                y1={MARGIN.top + yScreen(SIZE, t)}
                                x2={MARGIN.left + SIZE}
                                y2={MARGIN.top + yScreen(SIZE, t)}
                                stroke={t % 500 === 0 ? PLOT.gridMajor : PLOT.gridMinor}
                                strokeWidth={t % 500 === 0 ? 1.25 : 0.75}
                            />
                        </g>
                    ))}

                    {/* Axes */}
                    <line
                        x1={MARGIN.left}
                        y1={MARGIN.top + SIZE}
                        x2={MARGIN.left + SIZE}
                        y2={MARGIN.top + SIZE}
                        stroke={PLOT.axis}
                        strokeWidth={1.5}
                        strokeLinecap="round"
                    />
                    <line
                        x1={MARGIN.left}
                        y1={MARGIN.top}
                        x2={MARGIN.left}
                        y2={MARGIN.top + SIZE}
                        stroke={PLOT.axis}
                        strokeWidth={1.5}
                        strokeLinecap="round"
                    />

                    {TICKS.map((t) => (
                        <text
                            key={`xt-${t}`}
                            x={MARGIN.left + t}
                            y={MARGIN.top + SIZE + 20}
                            fontSize={12}
                            fontWeight={500}
                            textAnchor="middle"
                            fill={PLOT.tick}
                            style={{ fontVariantNumeric: "tabular-nums" }}
                        >
                            {t}
                        </text>
                    ))}
                    {TICKS.map((t) => (
                        <text
                            key={`yt-${t}`}
                            x={MARGIN.left - 12}
                            y={MARGIN.top + yScreen(SIZE, t) + 4}
                            fontSize={12}
                            fontWeight={500}
                            textAnchor="end"
                            fill={PLOT.tick}
                            style={{ fontVariantNumeric: "tabular-nums" }}
                        >
                            {t}
                        </text>
                    ))}

                    <text
                        x={MARGIN.left + SIZE / 2}
                        y={VIEW_H - 8}
                        fontSize={13}
                        fontWeight={600}
                        textAnchor="middle"
                        fill={PLOT.title}
                    >
                        X (km)
                    </text>
                    <text
                        x={14}
                        y={MARGIN.top + SIZE / 2}
                        fontSize={13}
                        fontWeight={600}
                        textAnchor="middle"
                        fill={PLOT.title}
                        transform={`rotate(-90, 14, ${MARGIN.top + SIZE / 2})`}
                    >
                        Y (km)
                    </text>

                    {/* Zones */}
                    {zones.map((z) => (
                        <g key={z.id}>
                            <rect
                                x={MARGIN.left + z.x_min}
                                y={MARGIN.top + yScreen(SIZE, z.y_max)}
                                width={z.x_max - z.x_min}
                                height={z.y_max - z.y_min}
                                rx={4}
                                fill={z.is_populated ? PLOT.populatedFill : "url(#zone-hatch)"}
                                stroke={z.is_populated ? PLOT.populatedStroke : PLOT.emptyStroke}
                                strokeOpacity={z.is_populated ? 0.85 : 0.7}
                                strokeDasharray={z.is_populated ? "0" : "6 4"}
                                strokeWidth={1.5}
                            />
                            <text
                                x={MARGIN.left + z.x_min + 10}
                                y={MARGIN.top + yScreen(SIZE, z.y_max) + 20}
                                fontSize={12}
                                fontWeight={600}
                                fill={z.is_populated ? "#fcd28a" : "#a9b6cc"}
                                style={{ paintOrder: "stroke", stroke: "#0a1120", strokeWidth: 3, strokeLinejoin: "round" }}
                            >
                                {z.name}
                            </text>
                        </g>
                    ))}

                    {/* Events */}
                    {events
                        .filter((e) => !e.eliminated)
                        .map((ev) => {
                            const cx = MARGIN.left + ev.epicenter_x;
                            const cy = MARGIN.top + yScreen(SIZE, ev.epicenter_y);
                            const r = magnitudeByRadio(ev.key[1]);
                            const color = PRIORITY_COLOR[ev.key[0]];
                            const isActive = ev.key[2] === hoverId || ev.key[2] === selectedEventId;
                            const label = `${toFormatId(ev.key[2])} · M${ev.key[1].toFixed(1)}`;
                            const labelW = label.length * 6.8 + 18;

                            return (
                                <g key={ev.key[2]}>
                                    {/* Soft ripple around the epicenter */}
                                    <circle
                                        cx={cx}
                                        cy={cy}
                                        r={r + 7}
                                        fill="none"
                                        stroke={color}
                                        strokeOpacity={ev.archived ? 0.08 : 0.28}
                                        strokeWidth={1}
                                        pointerEvents="none"
                                    />

                                    <circle
                                        cx={cx}
                                        cy={cy}
                                        r={r}
                                        fill={color}
                                        fillOpacity={ev.archived ? 0.3 : 0.85}
                                        filter={ev.key[0] === 3 && !ev.archived ? "url(#glow)" : undefined}
                                        stroke={
                                            ev.key[2] === selectedEventId
                                                ? PLOT.selected
                                                : ev.attention_status === "pending"
                                                    ? PLOT.pending
                                                    : PLOT.reviewed
                                        }
                                        strokeWidth={
                                            ev.key[2] === selectedEventId ? 3 : ev.attention_status === "pending" ? 1.75 : 1.25
                                        }
                                        strokeDasharray={ev.attention_status === "pending" ? "0" : "3 2"}
                                        className="cursor-pointer transition-all duration-150"
                                        onMouseEnter={() => setOnHover(ev.key[2])}
                                        onMouseLeave={() => setOnHover(null)}
                                        onClick={() => onSelectEvent?.(ev.key[2])}
                                    />

                                    {ev.expensive_acces && (
                                        <circle
                                            cx={cx}
                                            cy={cy}
                                            r={r + 5}
                                            fill="none"
                                            stroke={PLOT.costly}
                                            strokeWidth={1.75}
                                            strokeDasharray="2 3"
                                            strokeLinecap="round"
                                            pointerEvents="none"
                                        />
                                    )}

                                    {isActive && (
                                        <g pointerEvents="none">
                                            <rect
                                                x={cx - labelW / 2}
                                                y={cy - r - 34}
                                                width={labelW}
                                                height={22}
                                                rx={11}
                                                fill="#0a1120"
                                                fillOpacity={0.92}
                                                stroke={color}
                                                strokeOpacity={0.6}
                                            />
                                            <text
                                                x={cx}
                                                y={cy - r - 19}
                                                fontSize={11.5}
                                                fontWeight={600}
                                                textAnchor="middle"
                                                fill="#e2e8f0"
                                                style={{ fontVariantNumeric: "tabular-nums" }}
                                            >
                                                {label}
                                            </text>
                                        </g>
                                    )}
                                </g>
                            );
                        })}
                </svg>
            </div>

            {/* Legend */}
            <div className="w-full shrink-0 rounded-3xl border border-white/10 bg-slate-900/70 p-6 text-sm text-slate-300 shadow-xl shadow-black/30 ring-1 ring-inset ring-white/5 backdrop-blur lg:w-64 lg:self-start">
                <p className="mb-4 text-sm font-semibold text-slate-100">Prioridad</p>
                <div className="flex flex-col gap-3">
                    {([1, 2, 3] as const).map((p) => (
                        <span key={p} className="flex items-center gap-3">
                            <span
                                className="inline-block h-3 w-3 rounded-full ring-2 ring-slate-900"
                                style={{
                                    backgroundColor: PRIORITY_COLOR[p],
                                    boxShadow: `0 0 10px ${PRIORITY_COLOR[p]}80`,
                                }}
                            />
                            {p === 1 ? "Baja" : p === 2 ? "Media" : "Alta"}
                        </span>
                    ))}
                </div>

                <div className="my-6 border-t border-white/10" />

                <p className="mb-4 text-sm font-semibold text-slate-100">Estado</p>
                <div className="flex flex-col gap-3">
                    <span className="flex items-center gap-3">
                        <span className="inline-block h-3 w-3 rounded-full border-2 border-slate-100 bg-slate-700" />
                        Pendiente
                    </span>
                    <span className="flex items-center gap-3">
                        <span className="inline-block h-3 w-3 rounded-full border-2 border-dashed border-slate-500 bg-slate-700" />
                        Revisado
                    </span>
                    <span className="flex items-center gap-3">
                        <span className="inline-block h-3 w-3 rounded-full border-2 border-dashed border-rose-400" />
                        Acceso costoso
                    </span>
                    <span className="flex items-center gap-3">
                        <span className="inline-block h-3 w-3 rounded-full bg-slate-500 opacity-30" />
                        Archivado
                    </span>
                </div>
            </div>
        </div>
    );
}