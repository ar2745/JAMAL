import { useIsMobile } from "@/hooks/use-mobile";
import { useState } from "react";
import ChatContainer from "./components/ChatContainer";
import Sidebar from "./components/Sidebar";
import { ThemeProvider } from "./components/theme-provider";
import { ThemeToggle } from "./components/theme-toggle";

export default function App() {
  const isMobile = useIsMobile();
  const [activeSection, setActiveSection] = useState<'dashboard' | 'chat' | 'files' | 'links' | 'settings'>('chat');
  const [chatTitle, setChatTitle] = useState('New Chat');
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

  return (
    <ThemeProvider defaultTheme="dark" storageKey="chatbot-theme">
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
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          <div className="flex items-center justify-between p-4 border-b">
            <h1 className="text-lg font-semibold">{chatTitle}</h1>
            <ThemeToggle />
          </div>
          <ChatContainer
            selectedDocuments={documents.filter(doc => doc.selected)}
            selectedLinks={links.filter(link => link.selected)}
            chatTitle={chatTitle}
            setChatTitle={setChatTitle}
          />
        </div>
      </div>
    </ThemeProvider>
  );
}
