import { io, Socket } from "socket.io-client"

const API_URL = import.meta.env.VITE_API_URL;

class SocketService {
    private socket: Socket | null = null;

    connect(): Socket {
        if (!this.socket) {
            this.socket= io(API_URL, { transports: ["websocket"]});
        }
        return this.socket;
    }
}

export const socketService = new SocketService();