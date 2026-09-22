import { ChevronDown } from "lucide-react";
import { useState } from "react";
import type { DropdownMenuProps } from "../../models/interfaces/sidebar/DropdownMenuProps";
import { NavLink } from "react-router-dom";

const DropdownMenu = ({ title, items} : DropdownMenuProps) => {
    const [isOpen, setIsOpen ] = useState(false);

    return (
        <div>
            <button 
                onClick={() => setIsOpen(!isOpen)} 
                className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-white/10" 
                aria-expanded={isOpen}
            >
                <span>{title}</span>
                <ChevronDown size={20} className={isOpen? "rotate-180" : ""} />
            </button>

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