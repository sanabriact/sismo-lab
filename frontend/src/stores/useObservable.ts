// ------------------------------------------------------------------
// u se Ob se rv ab le
// ------------------------------------------------------------------

import { useSyncExternalStore } from "react";
import type { Observable } from "./Observable";

// Subscribes a component to an Observable and re-renders on changes
export function useObservable<T>(observable: Observable<T>): T  {
    return useSyncExternalStore(observable.subscribe, observable.getSnapshot);
}