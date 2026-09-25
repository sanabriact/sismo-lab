import { useEffect, useState } from "react";
import { ObservatoryService } from "../../../services/seismicObservatory/seismicObservatoryService";
import type { SeismicObservatory } from "../../../models/interfaces/observatory/SeismicObservatory";
import { TreeView } from "../../../components/Tree/TreeView";

const VisualizeTrees = () => {
    /* 
        Here we define two states: Data and error.
        Data will help us to mantain the observatory state
        Error will help us to mantain the error state if something goes wrong while fetching the data.
    */
    const [data, setData] = useState<SeismicObservatory | null>(null);
    const [error, setError] = useState<string | null>(null);

    /* 
        When the DOM loads, then call the fetch data function.
    */
    useEffect(() => {
        fetchData();
    }, []);

    /* 
        Here we use a asynchronous function for calling the observatoryService and get the observatory state.
        If something goes wrong, a message will be shown on the web console and will be saved in the error state.
    */
    const fetchData = async () => {
        try {
            const observatory = await ObservatoryService.getObservatory();
            setData(observatory);
        } catch (error) {
            console.error("Error obteniendo observatorio (pages) " + error)
            setError("No se pudo cargar los árboles.")
        }

    }

    return (
        <section className="p-8 space-y-8">
            {/* 
                Here we ask various things:
                1. Exists an error? 
                    Yes -> Show error message.
                    No -> Next question
                2. Data have not been loaded yet (asynchronous function)?
                    Yes -> Show a loading message
                    No -> Renderize the tree, calling the component TreeView and sending for each AVL and BST tree, its equivalent data trees.
            */}
            {error ? (
                <p className="text-red-600">{error}</p>
            ) : !data ?(
                <p>Cargando árboles...</p>
            ): (
            <>
                <h1 className="text-3xl font-bold text-gray-900">Visualizar eventos</h1>
                <div>
                    <h2 className="mb-2 text-xl font-semibold">AVL</h2>
                    <div className="overflow-auto rounded-lg border border-gray-200">
                        <TreeView data={data.avl_tree} type="avl"/>
                    </div>
                </div>
                <div>
                    <h2 className="mb-2 text-xl font-semibold">BST</h2>
                    <div className="overflow-auto rounded-lg border border-gray-200">
                        <TreeView data={data.bst_tree} type="bst"/>
                    </div>
                </div>
            </>
            )}
        </section>
    );
};

export default VisualizeTrees;