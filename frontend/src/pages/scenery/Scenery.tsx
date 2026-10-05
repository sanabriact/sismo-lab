import { useState } from "react";
import MapScenery from "../../components/scenery/MapScenery";
import { useObservable } from "../../stores/useObservable";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";

// Page that renders the seismic map with the current scenario data
const SeismicMapPage = () => {
  // Currently selected seismic event (null = none)
  const [selectedId, setSelectedId] = useState<number | null>(null);
  // Subscribe to scenario store data
  const { zones, stations, events } = useObservable(scenarioStore);

  return (
    <section className="min-h-screen w-full">
      {/* Map with zones, stations and events; selection state lives in this page */}
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