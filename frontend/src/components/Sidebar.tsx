import { cn } from "@/lib/utils";
import { Chat, Message } from "@/types";
import {
    Activity,
    Brain,
    Cpu,
    FileText,
    Link as LinkIcon,
    MessageSquare,
    PlusCircle,
    Settings,
    Trash2
} from "lucide-react";
import { ReactNode } from "react";
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

type ActiveSection = 'dashboard' | 'chat' | 'files' | 'links' | 'memory' | 'settings';

interface SidebarProps {
  isMobile: boolean;
  activeSection: ActiveSection;
  setActiveSection: (section: ActiveSection) => void;
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
  chats: Chat[];
  currentChatId: string | null;
  onChatSelect: (chatId: string) => void;
  onCreateNewChat: () => void;
  onDeleteChat: (chatId: string) => void;
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
  onSelectLink,
  chats,
  currentChatId,
  onChatSelect,
  onCreateNewChat,
  onDeleteChat
}: SidebarProps) {
  const getLastMessagePreview = (messages: Message[]) => {
    if (messages.length === 0) return 'No messages yet';
    const lastMessage = messages[messages.length - 1];
    return lastMessage.content.slice(0, 30) + (lastMessage.content.length > 30 ? "..." : "");
  };

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
        <Button className="w-full gap-2" onClick={onCreateNewChat}>
          <PlusCircle size={18} />
          <span>New Chat</span>
        </Button>
      </div>

      {/* Chat History */}
      <ScrollArea className="flex-1">
        <div className="space-y-1 px-2">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className={cn(
                "group flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-accent/10",
                currentChatId === chat.id && "bg-accent/10"
              )}
              onClick={() => {
                onChatSelect(chat.id);
                setActiveSection('chat');
              }}
            >
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{chat.title}</p>
                <p className="text-xs text-muted-foreground truncate">
                  {getLastMessagePreview(chat.messages)}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteChat(chat.id);
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Navigation */}
      <div className="p-2 border-t border-sidebar-border">
        <Button
          variant="ghost"
          className={cn(
            "w-full justify-start gap-2",
            activeSection === 'dashboard' && "bg-accent/10"
          )}
          onClick={() => setActiveSection('dashboard')}
        >
          <Activity className="h-4 w-4" />
          <span>Dashboard</span>
        </Button>
        <Button
          variant="ghost"
          className={cn(
            "w-full justify-start gap-2",
            activeSection === 'files' && "bg-accent/10"
          )}
          onClick={() => setActiveSection('files')}
        >
          <FileText className="h-4 w-4" />
          <span>Files</span>
        </Button>
        <Button
          variant="ghost"
          className={cn(
            "w-full justify-start gap-2",
            activeSection === 'links' && "bg-accent/10"
          )}
          onClick={() => setActiveSection('links')}
        >
          <LinkIcon className="h-4 w-4" />
          <span>Links</span>
        </Button>
        <Button
          variant="ghost"
          className={cn(
            "w-full justify-start gap-2",
            activeSection === 'memory' && "bg-accent/10"
          )}
          onClick={() => setActiveSection('memory')}
        >
          <Brain className="h-4 w-4" />
          <span>Memory</span>
        </Button>
        <Button
          variant="ghost"
          className={cn(
            "w-full justify-start gap-2",
            activeSection === 'settings' && "bg-accent/10"
          )}
          onClick={() => setActiveSection('settings')}
        >
          <Settings className="h-4 w-4" />
          <span>Settings</span>
        </Button>
      </div>
    </div>
  );
} 