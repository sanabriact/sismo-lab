import { useState } from "react";
import MapScenery from "../../components/scenery/MapScenery";
import type { Zone } from "../../models/interfaces/scenery/Zone";
import type { SeismicEvent } from "../../models/interfaces/tree/SeismicEvent";

const zones: Zone[] = [
  {
    id: "z1",
    name: "Zona Norte",
    is_populated: true,
    x_min: 0,
    x_max: 400,
    y_min: 600,
    y_max: 1000,
  },
  {
    id: "z2",
    name: "Zona Sur",
    is_populated: false,
    x_min: 400,
    x_max: 1000,
    y_min: 0,
    y_max: 600,
  },
  {
    id: "z3",
    name: "Zona Arriba Derecha",
    is_populated: true,
    x_min: 400,
    x_max: 1000,
    y_min: 600,
    y_max: 1000
  },
  {
    id: "z4",
    name: "Zona Abajo Izquierda",
    is_populated: false,
    x_min: 0,
    x_max: 1000,
    y_min: 0,
    y_max: 600
  }
];

const events: SeismicEvent[] = [
  {
    key: [3, 7.0, 1],
    epicenter_x: 20,
    epicenter_y: 30,
    depth: 10,
    datetime: "2024-06-01T12:00:00",
    revision: 1,
    reporting_stations: [],
    attention_status: "pending",
    event_status: "active",
    populated_zone: false,
    expensive_acces: false,
    eliminated: false,
    archived: false,
  },
  {
    key: [2, 5.5, 4],
    epicenter_x: 20,
    epicenter_y: 30,
    depth: 10,
    datetime: "2024-06-01T12:00:00",
    revision: 1,
    reporting_stations: [],
    attention_status: "pending",
    event_status: "active",
    populated_zone: false,
    expensive_acces: false,
    eliminated: false,
    archived: false,
  },
  {
    key: [1, 3.2, 3],
    epicenter_x: 105,
    epicenter_y: 105,
    depth: 23,
    datetime: "2025-06-01T12:00:00",
    revision: 2,
    reporting_stations: [],
    attention_status: "pending",
    event_status: "active",
    populated_zone: false,
    expensive_acces: false,
    eliminated: false,
    archived: false,
  },
];

const SeismicMapPage = () => {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <section className="min-h-screen w-full px-6 py-10 lg:px-10">
      <MapScenery
        zones={zones}
        events={events}
        selectedEventId={selectedId}
        onSelectEvent={setSelectedId}
      />
    </section>
  );
};

export default SeismicMapPage;