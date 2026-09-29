import { useEffect } from "react";
import { socketService } from "../../services/socket/socketService";
import type { TreeOperation } from "../../models/interfaces/realTime/TreeOperation";

export function useObservatorySocket(onOperation: (op: TreeOperation) => void) {
    useEffect(() => {
        const socket = socketService.connect()
        socket.on("tree:operation", onOperation)
        return () => { socket.off("tree:operation", onOperation)};
    }, [onOperation])
}