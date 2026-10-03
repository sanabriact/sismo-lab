import DropdownMenu from "../DropdownMenu";
import { getRoutesByGroup } from "../../../routes/selector";
import type { RouteGroupMenuProps } from "../../../models/interfaces/appRoute/RouteGroupMenuProps";

/* 
  Here we define a component that will renderize (via DropdownMenu component) two things:
  1. Group of common elements (ex. elements about events)
  2. Title that will be shown on screen.

  Accepts as parameters a group and a title.
*/
const RouteGroupMenu = ({ group, title }: RouteGroupMenuProps) => {
  /* 
    Here we transverse the routes sent by the function "getRoutesByGroup" and we generate a label and a path that will
    be sent to the component DropdownMenu.
  */
  const items = getRoutesByGroup(group).filter((route) => !route.hideInSidebar).map(({ title, path }) => ({
    label: title,
    path,   
  }));
  console.log(items)

  return <DropdownMenu title={title} items={items} />;
};

export default RouteGroupMenu;