// ------------------------------------------------------------------
// S ce ne ry
// ------------------------------------------------------------------

import { useState } from "react";
import MapScenery from "../../components/scenery/MapScenery";
import { useObservable } from "../../stores/useObservable";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";

const SeismicMapPage = () => {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { zones, stations, events } = useObservable(scenarioStore);

  return (
    <section className="min-h-screen w-full">
      <MapScenery
        zones={zones}
        stations={stations}
        events={events}
        selectedEventId={selectedId}
        onSelectEvent={setSelectedId}
      />
    </section>
  );
};

export default SeismicMapPage;  