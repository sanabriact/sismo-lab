import DropdownMenu from "../DropdownMenu";
import { getRoutesByGroup } from "../../../routes/selector";

interface RouteGroupMenuProps {
  group: string;
  title: string;
}

const RouteGroupMenu = ({ group, title }: RouteGroupMenuProps) => {
  const items = getRoutesByGroup(group).map(({ title, path }) => ({
    label: title,
    path,
  }));

  return <DropdownMenu title={title} items={items} />;
};

export default RouteGroupMenu;