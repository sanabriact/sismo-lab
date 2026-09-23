import { useState } from "react";
import Logo from "../../assets/sidebar/svg/logo";

import routes from "../../routes";
import { NavLink } from "react-router-dom";
import { sidebarGroups } from "../../routes/sidebarGroups";
import RouteGroupMenu from "./Events/RouteGroupMenu";

const Sidebar = () => {
  /* UseState form for stress mode button. */
  const [stressMode, setStressMode] = useState(false);
  const linkClass = `block p-2 rounded-lg hover:bg-white/10`;
  const ungroupedRoutes = routes.filter((route) => !route.group)

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
          <Logo/>
          <h2 className="text-xl font-bold">SismoLab</h2>
        </div>

        <ul className="flex-1 p-4 space-y-2">
          {ungroupedRoutes.map(({ path, title }) => (
            <li key={path}>
              <NavLink to={path} className={linkClass}>
                {title}
              </NavLink>
            </li>
          ))}

          {sidebarGroups.map(({ group, title }) => (
            <li key={group}>
              <RouteGroupMenu group={group} title={title} />
            </li>
          ))}
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