import { useState } from "react";
import { Clock3, FastForward } from "lucide-react";
import { useObservable } from "../../stores/useObservable";
import { clockStore } from "../../stores/clock/clockStore";
import { clockService } from "../../services/socket/clockService";

/* 
    UTC clock form is defined using the clock store and clock service.
*/
function formatClock(value: string | null): string {
    if (!value) return "Sin reloj";
    const instant = new Date(value);
    if (Number.isNaN(instant.getTime())) return "Sin reloj";
    return `${instant.toLocaleString("es-CO", {
        timeZone: "UTC",
        dateStyle: "short",
        timeStyle: "medium",
    })} UTC`;
}

/* 
    Transformation of UTC -> Local clock
*/
function formatLocalClock(value: string | null): string {
    if (!value) return "Sin reloj";
    const instant = new Date(value);
    if (Number.isNaN(instant.getTime())) return "Sin reloj";
    return instant.toLocaleString("es-CO", {
        dateStyle: "short",
        timeStyle: "medium",
    });
}

/* 
    Principal HTML view with a state of initial value of 1 hour.
*/
const AdvanceClock = () => {
    const clock = useObservable(clockStore);
    const [hours, setHours] = useState("1");
    const pending = clock.operation === "pending";

    /* 
        Handler for submitting advancing the clock or datetime.
    */
    const submit = () => {
        const value = Number(hours);
        if (!Number.isFinite(value) || value <= 0) return;
        clockService.advanceHours(value);
    };

    return (
        <section className="border-t border-white/20 px-4 py-4" aria-label="Reloj de simulación">
            {/* Text and icon */}
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
                <Clock3 size={16} aria-hidden="true" />
                <span>Reloj de simulación</span>
            </div>
            {/* Parragraphs indicating UTC or local time */}
            <div className="mb-3 space-y-1 text-xs text-blue-100">
                <p><span className="font-semibold text-white">UTC (simulación):</span> {formatClock(clock.currentTime)}</p>
                <p><span className="font-semibold text-white">Hora local (simulación):</span> {formatLocalClock(clock.currentTime)}</p>
            </div>
            {/* Label, button and input for submitting a clock advance */}
            <div className="flex items-end gap-2">
                <label className="min-w-0 flex-1 text-xs text-blue-100">
                    Horas
                    <input
                        type="number"
                        min="0.1"
                        step="0.1"
                        value={hours}
                        onChange={(event) => setHours(event.target.value)}
                        disabled={pending}
                        className="mt-1 w-full rounded border border-white/30 bg-white/10 px-2 py-1.5 text-sm text-white outline-none focus:border-white"
                    />
                </label>
                <button
                    type="button"
                    onClick={submit}
                    disabled={pending}
                    title="Avanzar el reloj"
                    aria-label="Avanzar el reloj"
                    className="flex h-9 items-center gap-1 rounded bg-emerald-500 px-2 text-xs font-semibold text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    <FastForward size={15} aria-hidden="true" />
                    <span>{pending ? "Avanzando" : "Avanzar"}</span>
                </button>
            </div>
            {/* Clock message depending of the observable state*/}
            {clock.message && <p className="mt-2 text-xs text-amber-200">{clock.message}</p>}
        </section>
    );
};

export default AdvanceClock;
