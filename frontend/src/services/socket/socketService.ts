// ------------------------------------------------------------------
// s oc ke tS er vi ce
// ------------------------------------------------------------------

import { io, Socket } from "socket.io-client"

const API_URL = import.meta.env.VITE_API_URL;

class SocketService {
    private socket: Socket | null = null;

    // Returns the shared socket, creating it on first call
    connect(): Socket {
        if (!this.socket) {
            this.socket = io(API_URL);
        }
        return this.socket;
    }
}

export const socketService = new SocketService();