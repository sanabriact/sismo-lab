// ------------------------------------------------------------------
// U pd at eE ve nt Pa yl oa d
// ------------------------------------------------------------------

export interface UpdateEventPayload {
    event_id: number;
    magnitude: number;
    depth: number;
    epicenter_x: number;
    epicenter_y: number;
    datetime: string;
    station: number;
}
