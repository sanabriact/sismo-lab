import { useNavigate } from "react-router-dom";

/* 
    Page for when the user wants to enter to a page that doesn't exists.
    useNavigate help us to redirect to home when the user clicks on "Volver al inicio".
*/
const Fallback = () => {
    const navigate = useNavigate();
    return (
        <div className="flex flex-col items-center justify-center min-h-screen gap-4">
            <span className="text-6xl font-bold text-gray-200 dark:text-gray-700">404</span>
            <h1 className="text-xl font-semibold text-black">
                Página no encontrada
            </h1>
            <button
                onClick={() => navigate("/home")}
                className="mt-2 px-5 py-2 rounded-xl hover:bg-gray-100"
            >
                Volver al inicio
            </button>
        </div>
    );
};

export default Fallback;