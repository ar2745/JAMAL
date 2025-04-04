import { cn } from "@/lib/utils";
import {
    Cpu,
    FileText,
    Home,
    Link as LinkIcon,
    MessageSquare,
    PlusCircle,
    Settings
} from "lucide-react";
import { ReactNode } from "react";
import { FileList } from "./FileList";
import { LinkList } from "./LinkList";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";

interface SidebarItemProps {
  icon: ReactNode;
  label: string;
  active?: boolean;
  onClick?: () => void;
}

function SidebarItem({ icon, label, active, onClick }: SidebarItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm transition-colors",
        active
          ? "bg-accent text-accent-foreground"
          : "text-sidebar-foreground hover:bg-sidebar-accent/50"
      )}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

interface SidebarProps {
  isMobile: boolean;
  activeSection: 'dashboard' | 'chat' | 'files' | 'links' | 'settings';
  setActiveSection: (section: 'dashboard' | 'chat' | 'files' | 'links' | 'settings') => void;
  documents: Array<{
    id: string;
    name: string;
    content: string;
    type: string;
    selected?: boolean;
  }>;
  links: Array<{
    id: string;
    url: string;
    title: string;
    description?: string;
    content?: string;
    selected?: boolean;
  }>;
  onDeleteDocument: (id: string) => void;
  onDeleteLink: (id: string) => void;
  onSelectDocument: (id: string, selected: boolean) => void;
  onSelectLink: (id: string, selected: boolean) => void;
}

export default function Sidebar({
  isMobile,
  activeSection,
  setActiveSection,
  documents,
  links,
  onDeleteDocument,
  onDeleteLink,
  onSelectDocument,
  onSelectLink
}: SidebarProps) {
  return (
    <div className="flex flex-col h-full bg-sidebar w-72 border-r border-sidebar-border">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <Cpu className="h-6 w-6 text-accent" />
            <h1 className="font-semibold text-sidebar-foreground">JAMAL</h1>
          </div>
          <p className="text-xs text-sidebar-foreground/70">Just Another Machine Assisted Learner</p>
        </div>
      </div>

      {/* New Chat button */}
      <div className="px-3 py-4">
        <Button className="w-full gap-2">
          <PlusCircle size={18} />
          <span>New Chat</span>
        </Button>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3 py-2">
        <div className="space-y-1">
          <SidebarItem 
            icon={<Home size={18} />} 
            label="Dashboard" 
            active={activeSection === 'dashboard'} 
            onClick={() => setActiveSection('dashboard')}
          />
          <SidebarItem 
            icon={<MessageSquare size={18} />} 
            label="Chat" 
            active={activeSection === 'chat'} 
            onClick={() => setActiveSection('chat')}
          />
          <SidebarItem 
            icon={<FileText size={18} />} 
            label="Files" 
            active={activeSection === 'files'} 
            onClick={() => setActiveSection('files')}
          />
          <SidebarItem 
            icon={<LinkIcon size={18} />} 
            label="Links" 
            active={activeSection === 'links'} 
            onClick={() => setActiveSection('links')}
          />
          <SidebarItem 
            icon={<Settings size={18} />} 
            label="Settings" 
            active={activeSection === 'settings'} 
            onClick={() => setActiveSection('settings')}
          />
        </div>
      </ScrollArea>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden border-t border-sidebar-border">
        {activeSection === 'files' && (
          <FileList
            documents={documents}
            onDelete={onDeleteDocument}
            onSelect={onSelectDocument}
          />
        )}
        {activeSection === 'links' && (
          <LinkList
            links={links}
            onDelete={onDeleteLink}
            onSelect={onSelectLink}
          />
        )}
      </div>
    </div>
  );
} 