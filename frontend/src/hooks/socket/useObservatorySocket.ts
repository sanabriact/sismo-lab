// ------------------------------------------------------------------
// u se Ob se rv at or yS oc ke t
// ------------------------------------------------------------------

import { useEffect } from "react";
import { socketService } from "../../services/socket/socketService";
import type { TreeOperation } from "../../models/interfaces/realTime/TreeOperation";

// Establishes socket connection and listens for tree operations; unsubscribes on cleanup
export function useObservatorySocket(onOperation: (op: TreeOperation) => void) {
    useEffect(() => {
        const socket = socketService.connect()
        socket.on("tree:operation", onOperation)
        return () => { socket.off("tree:operation", onOperation)};
    }, [onOperation])
}