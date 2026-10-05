export class Observable<T> {
    private listeners = new Set< () => void>();
    private value: T;

    constructor(initial: T){
        this.value = initial
    }

    // Returns the current value
    getSnapshot = (): T => this.value
    // Registers a listener; returns an unsubscribe function
    subscribe = (listener: () => void): (() => void) => {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    };

    // Updates the value and notifies listeners only if it changed
    set(next: T): void {
        if (Object.is(next, this.value)) return;
        this.value = next;
        this.listeners.forEach((listener) => listener());
    }
}