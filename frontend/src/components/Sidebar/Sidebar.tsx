import { useState } from "react";
import { Undo2 } from "lucide-react";
import { useObservable } from "../../stores/useObservable";
import { useScenarioLoaded } from "../../hooks/scenario/useScenarioLoaded";
import { modeStore } from "../../stores/mode/modeStore";
import { modeService } from "../../services/socket/modeService";
import Logo from "../../assets/sidebar/svg/logo";

import routes from "../../routes";
import { NavLink } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { sidebarGroups } from "../../routes/sidebarGroups";
import RouteGroupMenu from "./events/RouteGroupMenu";
import AdvanceClock from "../clock/AdvanceClock";
import { actionStackService } from "../../services/socket/actionStackService";

const Sidebar = () => {
  /* 
    We define various things here:
    1. UseState form for stress mode button. 
    2. A common Tailwind className for every button on the sidebar.
    3. Routes that doesn't belong to a group.
  */
  const modeState = useObservable(modeStore);
  const busy = modeState.status === "pending" || modeState.status === "recovering";
  const modeMessage =
    modeState.status === "recovering" ? "Recuperando el equilibrio…"
      : modeState.reason
      ?? (modeState.mode === "stress" && !modeState.balanced
        ? `El árbol ya no es AVL (desbalance máx. ${modeState.maxImbalance})`
        : null);
  const linkClass = `block p-2 rounded-lg hover:bg-white/10`;

  const scenarioLoaded = useScenarioLoaded();
  const navigate = useNavigate();
  const [undoPending, setUndoPending] = useState(false);
  const [undoMessage, setUndoMessage] = useState<string | null>(null);
  const ungroupedRoutes = routes.filter((route) => !route.group && (scenarioLoaded || !route.requiresScenario));

  const undoLastAction = async () => {
    if (undoPending) return;

    setUndoPending(true);
    setUndoMessage(null);
    const response = await actionStackService.undo();
    setUndoPending(false);
    if (response.ok && response.action?.action_type === "LOAD_SCENARIO") {
      navigate("/load-scenario");
    }
    setUndoMessage(response.ok
      ? `Deshecha: ${response.action?.action_type ?? "acción"}`
      : response.reason ?? "No se pudo deshacer la acción.");
  };

  return (
    <aside
      className={`
        fixed top-0 left-0 z-40
        h-screen w-64
        overflow-y-auto
        bg-[#04172f] text-white
        shadow-lg
      `}
    >
      <nav className="h-full flex flex-col">
        <div className="p-4 flex gap-7 items-center border-b border-white/20">
          <Logo />
          <h2 className="text-xl font-bold">SismoLab</h2>
        </div>

        {/* 
          Here we renderize each ungrouped route (ex. Home.tsx).
          In general, we use NavLink for better routing use.
        */}
        <ul className="flex-1 p-4 space-y-2">
          {ungroupedRoutes.map(({ path, title }) => (
            <li key={path}>
              <NavLink to={path} className={linkClass}>
                {title}
              </NavLink>
            </li>
          ))}

          {/* 
            Here we renderize each group of elements (Used when we want to make more dropdowns beside the "event" ones.),
            calling the component RouteGroupMenu.
          */}
          {scenarioLoaded && sidebarGroups.map(({ group, title }) => (
            <li key={group}>
              <RouteGroupMenu group={group} title={title} />
            </li>
          ))}
        </ul>

        {/* 
          Stress mode button
        */}

        {scenarioLoaded && (<div className="p-4 border-t border-white/20 space-y-6">
          <AdvanceClock />
          {
            /* Label that contains that shows "Deshacer" and button type input */
          }
          <button
            type="button"
            onClick={() => void undoLastAction()}
            disabled={undoPending}
            className="w-full flex items-center justify-between gap-2 p-2 rounded-lg hover:bg-white/20 transition-colors cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
            title="Deshacer última acción"
            aria-label="Deshacer última acción"
          >
            <span>Deshacer</span>
            <Undo2 size={16} aria-hidden="true" />
          </button>
          {undoMessage && <p className="px-2 pt-1 text-xs text-blue-100">{undoMessage}</p>}
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
                checked={modeState.mode === "stress"}
                disabled={busy}
                onChange={(e) => modeService.request(e.target.checked ? "stress" : "normal")}
                className="sr-only peer"
              />
              <div className="w-10 h-5 bg-white/20 rounded-full peer-checked:bg-emerald-500 transition-colors"></div>
              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
            </div>
          </label>
          {modeMessage && <p className="px-2 pt-1 text-xs text-amber-300">{modeMessage}</p>}
        </div>)}
      </nav>
    </aside>
  );
};

export default Sidebar;
