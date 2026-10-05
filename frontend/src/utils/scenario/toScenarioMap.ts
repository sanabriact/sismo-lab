// ------------------------------------------------------------------
// t oS ce na ri oM ap
// ------------------------------------------------------------------

import type { SeismicObservatory } from "../../models/interfaces/observatory/SeismicObservatory";
import type { Node } from "../../models/interfaces/tree/Node";
import type { SeismicEvent } from "../../models/interfaces/tree/SeismicEvent";

function eventsFromTree(node: Node | null): SeismicEvent[] {
    if (!node) return [];

    return [
        node.value,
        ...eventsFromTree(node.left_child),
        ...eventsFromTree(node.right_child),
    ];
}

export function toScenarioMap(observatory: SeismicObservatory) {
    return {
        zones: observatory.zones,
        stations: observatory.stations,
        events: eventsFromTree(observatory.avl_tree.root),
    };
}
