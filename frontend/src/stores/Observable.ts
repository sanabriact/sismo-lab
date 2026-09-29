export class Observable<T> {
    private listeners = new Set< () => void>();
    private value: T;

    constructor(initial: T){
        this.value = initial
    }

    getSnapshot = (): T => this.value
    subscribe = (listener: () => void): (() => void) => {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    };

    set(next: T): void {
        if (Object.is(next, this.value)) return;
        this.value = next;
        this.listeners.forEach((listener) => listener());
    }
}