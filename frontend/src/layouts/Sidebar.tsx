import { NavLink } from "react-router-dom";
import {
  Banknote,
  FileText,
  Upload,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Coins,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/vouchers", label: "Vouchers", icon: FileText },
  { to: "/vouchers/upload", label: "Upload", icon: Upload },
  { to: "/physical-cash", label: "Physical cash", icon: Coins },
  { to: "/distributor", label: "Distribute cash", icon: Banknote },
];

export function Sidebar() {
  const collapsed = useAppStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 flex flex-col border-r border-border bg-slate-900 text-slate-100 transition-all duration-200",
        collapsed ? "w-[72px]" : "w-56",
      )}
    >
      <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-sm font-bold">
          PC
        </div>
        {!collapsed ? (
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">Petty Cash</div>
            <div className="truncate text-[11px] text-slate-400">Cashier desk</div>
          </div>
        ) : null}
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            title={item.label}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-white",
                isActive && "bg-primary/20 text-teal-200",
                collapsed && "justify-center px-2",
              )
            }
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed ? <span className="truncate">{item.label}</span> : null}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-800 p-3">
        <Button
          variant="ghost"
          size={collapsed ? "icon" : "sm"}
          className="w-full text-slate-300 hover:bg-slate-800 hover:text-white"
          onClick={toggleSidebar}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" /> Collapse
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}
