import { useIsMobile } from "@/hooks/use-mobile";
import { useEffect, useState } from "react";
import { v4 as uuidv4 } from 'uuid';
import ChatContainer from "./components/ChatContainer";
import Dashboard from "./components/Dashboard";
import Sidebar from "./components/Sidebar";
import { ThemeProvider } from "./components/theme-provider";
import { ThemeToggle } from "./components/theme-toggle";
import { Chat, Message } from "./types";

export default function App() {
  const isMobile = useIsMobile();
  const [activeSection, setActiveSection] = useState<'dashboard' | 'chat' | 'files' | 'links' | 'settings'>('chat');
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<Array<{
    id: string;
    name: string;
    content: string;
    type: string;
    selected?: boolean;
  }>>([]);
  const [links, setLinks] = useState<Array<{
    id: string;
    url: string;
    title: string;
    description?: string;
    content?: string;
    selected?: boolean;
  }>>([]);

  // Load chats from localStorage on initial render
  useEffect(() => {
    const savedChats = localStorage.getItem('chats');
    if (savedChats) {
      const parsedChats = JSON.parse(savedChats);
      setChats(parsedChats);
      if (parsedChats.length > 0) {
        setCurrentChatId(parsedChats[0].id);
      }
    }
  }, []);

  // Save chats to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chats', JSON.stringify(chats));
  }, [chats]);

  const handleDeleteDocument = (id: string) => {
    setDocuments(documents.filter(doc => doc.id !== id));
  };

  const handleDeleteLink = (id: string) => {
    setLinks(links.filter(link => link.id !== id));
  };

  const handleSelectDocument = (id: string, selected: boolean) => {
    setDocuments(documents.map(doc => 
      doc.id === id ? { ...doc, selected } : doc
    ));
  };

  const handleSelectLink = (id: string, selected: boolean) => {
    setLinks(links.map(link => 
      link.id === id ? { ...link, selected } : link
    ));
  };

  const createNewChat = () => {
    const newChat: Chat = {
      id: uuidv4(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    setActiveSection('chat');
  };

  const updateChat = (chatId: string, updates: Partial<Chat>) => {
    setChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, ...updates, updatedAt: new Date().toISOString() }
        : chat
    ));
  };

  const deleteChat = (chatId: string) => {
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    if (currentChatId === chatId) {
      setCurrentChatId(chats.length > 1 ? chats[0].id : null);
    }
  };

  const handleSendMessage = (message: Message) => {
    if (!currentChatId) return;

    setChats(prevChats => {
      return prevChats.map(chat => {
        if (chat.id === currentChatId) {
          const updatedMessages = [...chat.messages, message];
          return {
            ...chat,
            messages: updatedMessages,
            updatedAt: new Date().toISOString(),
            title: chat.title === 'New Chat' && updatedMessages.length === 1
              ? message.content.slice(0, 30) + (message.content.length > 30 ? "..." : "")
              : chat.title
          };
        }
        return chat;
      });
    });
  };

  // Get selected documents and links
  const selectedDocuments = documents.filter(doc => doc.selected);
  const selectedLinks = links.filter(link => link.selected);

  const currentChat = chats.find(chat => chat.id === currentChatId);

  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <div className="min-h-screen bg-background">
        <div className="flex h-screen">
          <Sidebar
            isMobile={isMobile}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
            documents={documents}
            links={links}
            onDeleteDocument={handleDeleteDocument}
            onDeleteLink={handleDeleteLink}
            onSelectDocument={handleSelectDocument}
            onSelectLink={handleSelectLink}
            chats={chats}
            currentChatId={currentChatId}
            onChatSelect={setCurrentChatId}
            onCreateNewChat={createNewChat}
            onDeleteChat={deleteChat}
          />
          <main className="flex-1 flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <h1 className="text-lg font-semibold">
                {activeSection === 'chat' ? (currentChat?.title || 'New Chat') : 'Dashboard'}
              </h1>
              <ThemeToggle />
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden">
              {activeSection === 'dashboard' && (
                <Dashboard documents={documents} links={links} />
              )}
              {activeSection === 'chat' && currentChat && (
                <ChatContainer
                  chatTitle={currentChat.title}
                  setChatTitle={(title) => updateChat(currentChatId!, { title })}
                  selectedDocuments={selectedDocuments}
                  selectedLinks={selectedLinks}
                  messages={currentChat.messages}
                  onSendMessage={handleSendMessage}
                />
              )}
            </div>
          </main>
        </div>
      </div>
    </ThemeProvider>
  );
}
