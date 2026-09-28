import { useEffect } from "react";
import { socketService } from "../../services/socket/socketService";

export function useObservatorySocket(onEvent: (payload: unknown) => void) {
    useEffect(() => {
        const socket = socketService.connect()
        socket.on("report_processed", onEvent)
        return () => { socket.off("report_processed", onEvent)};
    }, [onEvent])
}