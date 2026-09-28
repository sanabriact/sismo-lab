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
    1: "#8fae7d",
    2: "#e0a83e",
    3: "#c8553d"
}

export default function MapScenery({ zones, events, selectedEventId = null, onSelectEvent }: SeismicMapProps) {
    const [hoverId, setOnHover] = useState<number | null>(null);

    return (
        <div className="flex w-full flex-col gap-4 lg:flex-row lg:items-start">
            <div
                className="relative aspect-square w-full flex-1 rounded-2xl border border-slate-800 bg-slate-950 p-3 shadow-inner shadow-black/40"
                style={{ maxWidth: "min(82vh, 100%)" }}
            >
                <svg
                    viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
                    className="h-full w-full"
                    role="img"
                    aria-label="Plano geográfico del observatorio sísmico"
                >
                    <defs>
                        <filter id="glow" x="-75%" y="-75%" width="250%" height="250%">
                            <feGaussianBlur stdDeviation="4" result="blur" />
                            <feMerge>
                                <feMergeNode in="blur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                    </defs>

                    <rect x={MARGIN.left} y={MARGIN.top} width={SIZE} height={SIZE} fill="#0f172a" />

                    {TICKS.map((t) => (
                        <g key={`grid-${t}`}>
                            <line
                                x1={MARGIN.left + t}
                                y1={MARGIN.top}
                                x2={MARGIN.left + t}
                                y2={MARGIN.top + SIZE}
                                stroke={t % 500 === 0 ? "#2d3f5c" : "#182338"}
                                strokeWidth={t % 500 === 0 ? 1 : 0.5}
                            />
                            <line
                                x1={MARGIN.left}
                                y1={MARGIN.top + yScreen(SIZE, t)}
                                x2={MARGIN.left + SIZE}
                                y2={MARGIN.top + yScreen(SIZE, t)}
                                stroke={t % 500 === 0 ? "#2d3f5c" : "#182338"}
                                strokeWidth={t % 500 === 0 ? 1 : 0.5}
                            />
                        </g>
                    ))}

                    <line
                        x1={MARGIN.left}
                        y1={MARGIN.top + SIZE}
                        x2={MARGIN.left + SIZE}
                        y2={MARGIN.top + SIZE}
                        stroke="#94a3b8"
                        strokeWidth={1.5}
                    />
                    <line
                        x1={MARGIN.left}
                        y1={MARGIN.top}
                        x2={MARGIN.left}
                        y2={MARGIN.top + SIZE}
                        stroke="#94a3b8"
                        strokeWidth={1.5}
                    />

                    {TICKS.map((t) => (
                        <text
                            key={`xt-${t}`}
                            x={MARGIN.left + t}
                            y={MARGIN.top + SIZE + 18}
                            fontSize={11}
                            fontFamily="ui-monospace, monospace"
                            textAnchor="middle"
                            fill="#94a3b8"
                        >
                            {t}
                        </text>
                    ))}
                    {TICKS.map((t) => (
                        <text
                            key={`yt-${t}`}
                            x={MARGIN.left - 10}
                            y={MARGIN.top + yScreen(SIZE, t) + 4}
                            fontSize={11}
                            fontFamily="ui-monospace, monospace"
                            textAnchor="end"
                            fill="#94a3b8"
                        >
                            {t}
                        </text>
                    ))}

                    <text
                        x={MARGIN.left + SIZE / 2}
                        y={VIEW_H - 6}
                        fontSize={12}
                        fontFamily="ui-monospace, monospace"
                        textAnchor="middle"
                        fill="#cbd5e1"
                    >
                        X (km)
                    </text>
                    <text
                        x={14}
                        y={MARGIN.top + SIZE / 2}
                        fontSize={12}
                        fontFamily="ui-monospace, monospace"
                        textAnchor="middle"
                        fill="#cbd5e1"
                        transform={`rotate(-90, 14, ${MARGIN.top + SIZE / 2})`}
                    >
                        Y (km)
                    </text>

                    {zones.map((z) => (
                        <g key={z.id}>
                            <rect
                                x={MARGIN.left + z.x_min}
                                y={MARGIN.top + yScreen(SIZE, z.y_max)}
                                width={z.x_max - z.x_min}
                                height={z.y_max - z.y_min}
                                fill={z.is_populated ? "rgba(251,191,36,0.10)" : "rgba(148,163,184,0.08)"}
                                stroke={z.is_populated ? "#d97706" : "#475569"}
                                strokeDasharray={z.is_populated ? "0" : "5 3"}
                                strokeWidth={1.25}
                            />
                            <text
                                x={MARGIN.left + z.x_min + 6}
                                y={MARGIN.top + yScreen(SIZE, z.y_max) + 16}
                                fontSize={11}
                                fontFamily="ui-monospace, monospace"
                                fill="#e2e8f0"
                                fontWeight={500}
                            >
                                {z.name}
                            </text>
                        </g>
                    ))}

                    {events
                        .filter((e) => !e.eliminated)
                        .map((ev) => (
                            <g key={ev.key[2]}>
                                <circle
                                    cx={MARGIN.left + ev.epicenter_x}
                                    cy={MARGIN.top + yScreen(SIZE, ev.epicenter_y)}
                                    r={magnitudeByRadio(ev.key[1])}
                                    fill={PRIORITY_COLOR[ev.key[0]]}
                                    fillOpacity={ev.archived ? 0.3 : 0.85}
                                    filter={ev.key[0] === 3 && !ev.archived ? "url(#glow)" : undefined}
                                    stroke={
                                        ev.key[2] === selectedEventId
                                            ? "#38bdf8"
                                            : ev.attention_status === "pending"
                                                ? "#e2e8f0"
                                                : "#475569"
                                    }
                                    strokeWidth={
                                        ev.key[2] === selectedEventId ? 3 : ev.attention_status === "pending" ? 1.5 : 1
                                    }
                                    strokeDasharray={ev.attention_status === "pending" ? "0" : "3 2"}
                                    className="cursor-pointer transition-opacity"
                                    onMouseEnter={() => setOnHover(ev.key[2])}
                                    onMouseLeave={() => setOnHover(null)}
                                    onClick={() => onSelectEvent?.(ev.key[2])}
                                />

                                {ev.expensive_acces && (
                                    <circle
                                        cx={MARGIN.left + ev.epicenter_x}
                                        cy={MARGIN.top + yScreen(SIZE, ev.epicenter_y)}
                                        r={magnitudeByRadio(ev.key[1]) + 5}
                                        fill="none"
                                        stroke="#f87171"
                                        strokeWidth={1.5}
                                        strokeDasharray="2 3"
                                        pointerEvents="none"
                                    />
                                )}

                                {(ev.key[2] === hoverId || ev.key[2] === selectedEventId) && (
                                    <text
                                        x={MARGIN.left + ev.epicenter_x}
                                        y={MARGIN.top + yScreen(SIZE, ev.epicenter_y) - magnitudeByRadio(ev.key[1]) - 8}
                                        fontSize={11}
                                        fontFamily="ui-monospace, monospace"
                                        textAnchor="middle"
                                        fill="#e2e8f0"
                                        pointerEvents="none"
                                    >
                                        {toFormatId(ev.key[2])} · M{ev.key[1].toFixed(1)}
                                    </text>
                                )}
                            </g>
                        ))}
                </svg>
            </div>

            <div className="w-full shrink-0 rounded-2xl border border-slate-800 bg-slate-950 p-5 font-mono text-sm text-slate-300 lg:w-56">
                <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">Prioridad</p>
                <div className="flex flex-col gap-2.5">
                    {([1, 2, 3] as const).map((p) => (
                        <span key={p} className="flex items-center gap-2.5">
                            <span
                                className="inline-block h-2.5 w-2.5 rounded-full ring-2 ring-slate-950"
                                style={{ backgroundColor: PRIORITY_COLOR[p] }}
                            />
                            {p === 1 ? "Baja" : p === 2 ? "Media" : "Alta"}
                        </span>
                    ))}
                </div>

                <p className="mb-3 mt-6 text-xs font-semibold uppercase tracking-widest text-slate-500">Estado</p>
                <div className="flex flex-col gap-2.5">
                    <span className="flex items-center gap-2.5">
                        <span className="inline-block h-2.5 w-2.5 rounded-full border-2 border-slate-200 bg-slate-700" />
                        Pendiente
                    </span>
                    <span className="flex items-center gap-2.5">
                        <span className="inline-block h-2.5 w-2.5 rounded-full border-2 border-dashed border-slate-500 bg-slate-700" />
                        Revisado
                    </span>
                    <span className="flex items-center gap-2.5">
                        <span className="inline-block h-2.5 w-2.5 rounded-full border-2 border-dashed border-red-400" />
                        Acceso costoso
                    </span>
                    <span className="flex items-center gap-2.5">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-slate-500 opacity-30" />
                        Archivado
                    </span>
                </div>
            </div>
        </div>
    );
}