// Sidebar item type definition
export interface SidebarItem {
  id: string;
  label: string;
  icon: string;
  path: string;
}

// Module type definition
export interface Module {
  id: string;
  label: string;
  icon: string;
  sections: SidebarItem[];
}
