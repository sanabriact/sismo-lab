// Flips a Y coordinate: map origin is bottom-left, screen origin is top-left
export function yScreen(size: number, y: number) {
    return size-y;
}