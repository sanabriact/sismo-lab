import Sidebar from "../components/Sidebar/Sidebar";

const DefaultLayout = () => {
  return (
    <div className="min-h-screen">

      <Sidebar/>
      <main>
        {/* Contenido de la página */}
      </main>

    </div>
  );
};

export default DefaultLayout;