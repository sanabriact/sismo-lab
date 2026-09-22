import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar/Sidebar";

const DefaultLayout = () => {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 ml-64">
         {/* Outlet sirve para indicarle a react que renderice cada página */}
        <Outlet />
      </main>
    </div>
  );
}
export default DefaultLayout;