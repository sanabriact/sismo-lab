import EventActionsMenu from "./Events/EventActionsMenu";

const Sidebar = () => {
  return (
    <aside
      className={`
        fixed top-0 left-0 z-40
        h-screen w-64
        bg-[#04172f] text-white
        shadow-lg
      `}
    >
      <nav className="h-full flex flex-col">
        <div className="p-4 flex justify-between items-center border-b border-white/20">
          <h2 className="text-xl font-bold">SismoLab</h2>
        </div>

        <ul className="flex-1 p-4 space-y-2">
          <li>
            <a href="/trees" className="block p-2 rounded-lg hover:bg-white/10">Visualizador de eventos</a>
          </li>

          <li>
            <EventActionsMenu />
          </li>


          <li className="p-2">
            Elemento 3 de prueba
          </li>

          <li className="p-2">
            Elemento 4 de prueba
          </li>

          <li className="p-2">
            Elemento 5 de prueba
          </li>

          <li className="p-2">
            Elemento 6 de prueba
          </li>
          <li className="p-2">
            Elemento 7 de prueba
          </li>
          <li className="p-2">
            Elemento 8 de prueba
          </li>

        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;