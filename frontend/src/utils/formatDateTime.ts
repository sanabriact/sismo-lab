// Format a date and time using the UTC display shared by event tables.
export function formatDateTime(value: string): string {
    return `${new Date(value).toLocaleString("es-CO", {
        timeZone: "UTC",
        dateStyle: "short",
        timeStyle: "medium",
    })} UTC`;
}
