
import MainLayout from "@/layouts/MainLayout";
import ChatInterface from "@/components/ChatInterface";
import { useEffect } from "react";
import { toast } from "@/hooks/use-toast";

const Index = () => {
  // Show welcome toast on first load
  useEffect(() => {
    const hasSeenWelcome = localStorage.getItem('hasSeenWelcome');
    
    if (!hasSeenWelcome) {
      setTimeout(() => {
        toast({
          title: "Welcome to Chatbot UI",
          description: "Ask questions, upload documents, or crawl links to get started.",
        });
        localStorage.setItem('hasSeenWelcome', 'true');
      }, 1000);
    }
  }, []);

  return (
    <MainLayout>
      <ChatInterface />
    </MainLayout>
  );
};

export default Index;
