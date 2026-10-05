// ------------------------------------------------------------------
// E ve nt sF or m
// ------------------------------------------------------------------

import { useEffect, useState } from "react";
import type { EventFormValues } from "../../models/types/event/EventFormValues";
import type { EventFormProps } from "../../models/types/event/EventFormProps";

const inputBase =
    "w-full rounded border border-gray-300 px-3 py-2 transition-colors";

const EventForm = ({
    mode,
    values,
    stations,
    submitting,
    minimumDatetime,
    submitText,
    onChange,
    onSubmit,
}: EventFormProps) => {
    const [touched, setTouched] = useState<Set<keyof EventFormValues>>(
        new Set(),
    );

    useEffect(() => {
        setTouched(new Set());
    }, [mode, values.id]);

    const changeField = (field: keyof EventFormValues, value: string) => {
        setTouched((current) => new Set(current).add(field));
        onChange({ ...values, [field]: value });
    };

    const fieldClass = (field: keyof EventFormValues) => {
        const faded = mode === "edit" && !touched.has(field);
        return `${inputBase} ${faded ? "text-gray-400" : "text-gray-900"}`;
    };

    return (
        <form
            onSubmit={onSubmit}
            className="grid gap-5 rounded-lg border border-gray-200 bg-white p-6 shadow-sm md:grid-cols-2"
        >
            <Field label="ID numérico">
                <input
                    required
                    disabled={mode === "edit"}
                    min="1"
                    max="999999"
                    step="1"
                    type="number"
                    value={values.id}
                    onChange={(e) => changeField("id", e.target.value)}
                    className={
                        mode === "edit"
                            ? `${inputBase} cursor-not-allowed bg-gray-100 text-gray-400`
                            : fieldClass("id")
                    }
                />
            </Field>

            <Field label="Magnitud">
                <input
                    required
                    min="-2"
                    max="10"
                    step="0.1"
                    type="number"
                    value={values.magnitude}
                    onChange={(e) => changeField("magnitude", e.target.value)}
                    className={fieldClass("magnitude")}
                />
            </Field>

            <Field label="Profundidad (km)">
                <input
                    required
                    min="0"
                    max="700"
                    step="0.1"
                    type="number"
                    value={values.depth}
                    onChange={(e) => changeField("depth", e.target.value)}
                    className={fieldClass("depth")}
                />
            </Field>

            <Field label="Coordenada X (km)">
                <input
                    required
                    min="0"
                    max="1000"
                    step="0.1"
                    type="number"
                    value={values.epicenter_x}
                    onChange={(e) => changeField("epicenter_x", e.target.value)}
                    className={fieldClass("epicenter_x")}
                />
            </Field>

            <Field label="Coordenada Y (km)">
                <input
                    required
                    min="0"
                    max="1000"
                    step="0.1"
                    type="number"
                    value={values.epicenter_y}
                    onChange={(e) => changeField("epicenter_y", e.target.value)}
                    className={fieldClass("epicenter_y")}
                />
            </Field>

            <Field label="Fecha y hora">
                <input
                    required
                    min={minimumDatetime}
                    type="datetime-local"
                    value={values.datetime}
                    onChange={(e) => changeField("datetime", e.target.value)}
                    className={fieldClass("datetime")}
                />
            </Field>

            <Field label="Estación">
                <select
                    required
                    value={values.station}
                    onChange={(e) => changeField("station", e.target.value)}
                    className={fieldClass("station")}
                >
                    <option value="">Selecciona una estación</option>
                    {stations.map((station) => (
                        <option key={station.id} value={station.id}>
                            {station.name} (#{station.id})
                        </option>
                    ))}
                </select>
            </Field>

            <div className="flex items-end">
                <button
                    disabled={submitting}
                    type="submit"
                    className="w-full rounded bg-[#04172f] px-4 py-2 font-medium text-white hover:bg-[#08264d] disabled:opacity-60"
                >
                    {submitting ? "Guardando…" : submitText}
                </button>
            </div>
        </form>
    );
};

const Field = ({
    label,
    children,
}: {
    label: string;
    children: React.ReactNode;
}) => (
    <label className="grid gap-1 text-sm font-medium text-gray-700">
        {label}
        {children}
    </label>
);

export default EventForm;