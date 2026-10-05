// Maps a magnitude (-2 to 10) to a marker radius (4 to 22)
export function magnitudeByRadio(magnitude: number) {
    // Clamp to the valid magnitude range
    const clamped = Math.max(-2, Math.min(10, magnitude));
    // Linear scale: min radius 4 plus up to 18 extra
    return 4 + ((clamped + 2) / 12) * 18;
}