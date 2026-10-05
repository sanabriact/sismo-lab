// ------------------------------------------------------------------
// D ef au lt La yo ut
// ------------------------------------------------------------------

import { Outlet } from "react-router-dom";
import Sidebar from "../components/sidebar/Sidebar";

const DefaultLayout = () => {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 ml-64">
         {/* Outlet for indicating React for renderize each page */}
        <Outlet />
      </main>
    </div>
  );
}
export default DefaultLayout;