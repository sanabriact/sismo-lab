import { useState } from "react";
import Logo from "../../assets/sidebar/svg/logo";
import EventActionsMenu from "./Events/EventActionsMenu";

const Sidebar = () => {
  /* UseState form for stress mode button. */
  const [stressMode, setStressMode] = useState(false);

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
        <div className="p-4 flex gap-7 items-center border-b border-white/20">
          <Logo />
          <h2 className="text-xl font-bold">SismoLab</h2>
        </div>

        <ul className="flex-1 p-4 space-y-2">
          <li>
            <a className="block p-2 rounded-lg hover:bg-white/10">Inicio</a>
          </li>
          <li>
            <EventActionsMenu/>
          </li>

          <li>
            <a href="/check-structure" className="block p-2 rounded-lg hover:bg-white/10">Verificar estructura</a>
          </li>

          <li>
            <a href="" className="block p-2 rounded-lg hover:bg-white/10">Elemento 4 de prueba</a>
          </li>

          <li>
            <a href="" className="block p-2 rounded-lg hover:bg-white/10">Elemento 5 de prueba</a>
          </li>

          <li>
            <a href="" className="block p-2 rounded-lg hover:bg-white/10">Elemento 6 de prueba</a>
          </li>
          <li>
            <a href="" className="block p-2 rounded-lg hover:bg-white/10">Elemento 7 de prueba</a>
          </li>
          <li>
            <a href="" className="block p-2 rounded-lg hover:bg-white/10">Elemento 8 de prueba</a>
          </li>

        </ul>

        {/* 
          Stress mode button
        */}

        <div className="p-4 border-t border-white/20">
            {/* 
              Label with content that shows "Modo estrés" and toggle type button.
            */}
            <label className="w-full flex items-center justify-between gap-2 p-2 rounded-lg hover:bg-white/20 transition-colors cursor-pointer">
            <span>Modo estrés</span>
            
            {/* 
              Div that contains the button for activating stress mode.
            */}
            <div className="relative">
              <input
                type="checkbox"
                checked={stressMode}
                onChange={(e) => setStressMode(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-10 h-5 bg-white/20 rounded-full peer-checked:bg-emerald-500 transition-colors"></div>
              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
            </div>
          </label>
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;