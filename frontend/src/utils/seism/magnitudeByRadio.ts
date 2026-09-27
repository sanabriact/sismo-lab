export function magnitudeByRadio(magnitude: number) {
    const clamped = Math.max(-2, Math.min(10, magnitude));
    return 4 + ((clamped + 2) / 12) * 18;
}