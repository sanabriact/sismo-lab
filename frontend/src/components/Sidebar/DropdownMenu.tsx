import { ChevronDown } from "lucide-react";
import { useState } from "react";
import type { DropdownMenuProps } from "../../models/interfaces/sidebar/DropdownMenuProps";
import { NavLink } from "react-router-dom";

/* 
    Component to generate a custom dropdown menu depending on a title and a group of items.
*/
const DropdownMenu = ({ title, items} : DropdownMenuProps) => {
    /* 
        Here we manage and save the state of the chevron rotation depending if is open or closed.
    */
    const [isOpen, setIsOpen ] = useState(false);

    return (
        <div>
            {/* 
                We generate the chevron button that will open or close the dropdown.
                The state of isOpen will change when the user clicks on the button, and will asign the contrary value that
                isOpen have.
            */}
            <button 
                onClick={() => setIsOpen(!isOpen)} 
                className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-white/10" 
                aria-expanded={isOpen}
            >
                {/* 
                    If isOpen is true, then it will rotate 180 degrees via Tailwind.
                    If not, then it will stay down.
                */}
                <span>{title}</span>
                <ChevronDown size={20} className={isOpen? "rotate-180" : ""} />
            </button>
            
            {/* 
                Here this part will be renderized only if isOpen is true.
            */}
            {isOpen && (
                <ul className="mt-1 ml-4 space-y-1">
                    {items.map((item) => (
                        <li key={item.path}>
                            <NavLink to={item.path} className="block p-2 rounded-lg hover:bg-white/10">
                            {item.label}
                            </NavLink>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default DropdownMenu;