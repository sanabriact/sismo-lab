// ------------------------------------------------------------------
// u se Ob se rv ab le
// ------------------------------------------------------------------

import { useSyncExternalStore } from "react";
import type { Observable } from "./Observable";

export function useObservable<T>(observable: Observable<T>): T  {
    return useSyncExternalStore(observable.subscribe, observable.getSnapshot);
}