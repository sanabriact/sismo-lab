import { ChevronDown } from "lucide-react";
import { useState } from "react";
import type { DropdownMenuItems } from "../../models/types/DropdownMenuItems";

interface DropdownMenuProps {
    title: string;
    items: DropdownMenuItems[]
}

const DropdownMenu = ({ title, items} : DropdownMenuProps) => {
    const [isOpen, setIsOpen ] = useState(false);

    return (
        <div>
            <button onClick={() => setIsOpen(!isOpen)} className="w-full flex items-center justify-between p-2 rounded-lg hover: bg-white/10" aria-expanded={isOpen}>
                <span>{title}</span>
                <ChevronDown size={20} className={isOpen? "rotate-180" : ""} />
            </button>

            {isOpen && (
                <ul className="mt-1 ml-4 space-y-1">
                    {items.map((item) => (
                        <li>
                            <a href={item.href} className="block p-2 rounded-lg hover:bg-white/10">{item.label}</a>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default DropdownMenu;