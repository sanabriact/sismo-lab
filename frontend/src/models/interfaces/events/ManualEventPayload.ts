// ------------------------------------------------------------------
// M an ua lE ve nt Pa yl oa d
// ------------------------------------------------------------------

export interface ManualEventPayload {
    id: number;
    magnitude: number;
    depth: number;
    epicenter_x: number;
    epicenter_y: number;
    datetime: string;
    station: number;
}
