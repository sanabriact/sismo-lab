import { useEffect, useState } from "react";
import { ObservatoryService } from "../../../services/seismicObservatory/seismicObservatoryService";
import type { SeismicObservatory } from "../../../models/SeismicObservatory";

const VisualizeTrees = () => {
    const [data, setData] = useState<SeismicObservatory | null>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        const observatory = await ObservatoryService.getObservatory();
        setData(observatory);
    }
    return (
        <section className="flex min-h-screen items-center justify-center">
            <div className="w-full max-w-4xl text-center">
                <h1 className="text-4xl font-bold leading-tight text-gray-900 md:text-5xl">
                    Visualizar árboles
                </h1>
                <pre>{JSON.stringify(data, null, 2)}</pre>
            </div>
        </section>
    );
};

export default VisualizeTrees;