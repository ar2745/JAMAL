
import { useState, useRef, useEffect } from "react";
import ChatMessage from "./ChatMessage";
import UserInput from "./UserInput";
import { Message } from "@/types";
import { sendMessage, uploadDocument, crawlLink } from "@/utils/api";
import { toast } from "@/hooks/use-toast";
import { v4 as uuidv4 } from 'uuid';

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hello! I'm your AI assistant. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      role: "user",
      content,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Placeholder for bot typing indicator
      const placeholderId = uuidv4();
      setMessages((prev) => [
        ...prev,
        {
          id: placeholderId,
          role: "assistant",
          content: "...",
          timestamp: new Date(),
        },
      ]);

      // Send to API
      const response = await sendMessage(content);
      
      // Remove placeholder and add actual response
      setMessages((prev) => 
        prev.filter(msg => msg.id !== placeholderId).concat({
          id: uuidv4(),
          role: "assistant",
          content: response.message || "Sorry, I couldn't process that request.",
          timestamp: new Date(),
        })
      );
    } catch (error) {
      console.error("Error sending message:", error);
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });
      
      // Remove loading message if exists
      setMessages((prev) => prev.filter(msg => msg.content !== "..."));
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    const userMessage: Message = {
      id: uuidv4(),
      role: "user",
      content: `Uploaded document: ${file.name}`,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await uploadDocument(file);
      
      const assistantMessage: Message = {
        id: uuidv4(),
        role: "assistant",
        content: `Document ${file.name} has been successfully uploaded and processed. You can now ask questions about it!`,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
      
      toast({
        title: "Upload Successful",
        description: `${file.name} has been uploaded and processed.`,
      });
    } catch (error) {
      console.error("Error uploading document:", error);
      
      const errorMessage: Message = {
        id: uuidv4(),
        role: "assistant",
        content: "Sorry, there was an error uploading your document. Please try again.",
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, errorMessage]);
      
      toast({
        title: "Upload Failed",
        description: "There was an error uploading your document.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLinkCrawl = async (url: string) => {
    const userMessage: Message = {
      id: uuidv4(),
      role: "user",
      content: `Crawled link: ${url}`,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await crawlLink(url);
      
      const assistantMessage: Message = {
        id: uuidv4(),
        role: "assistant",
        content: `The link ${url} has been successfully crawled and its content has been processed. You can now ask questions about it!`,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
      
      toast({
        title: "Link Processed",
        description: `${url} has been crawled and indexed.`,
      });
    } catch (error) {
      console.error("Error crawling link:", error);
      
      const errorMessage: Message = {
        id: uuidv4(),
        role: "assistant",
        content: "Sorry, there was an error processing your link. Please check that it's valid and try again.",
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, errorMessage]);
      
      toast({
        title: "Link Processing Failed",
        description: "There was an error crawling the provided link.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Chat messages area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto">
          {messages.map((message, index) => (
            <ChatMessage 
              key={message.id} 
              message={message} 
              isLast={index === messages.length - 1} 
            />
          ))}
          
          {/* Typing indicator when loading */}
          {isLoading && !messages.some(msg => msg.content === "...") && (
            <div className="py-4 px-8 flex items-center gap-2">
              <div className="flex gap-1 items-end h-6">
                <div className="w-2 h-2 bg-accent rounded-full typing-dot"></div>
                <div className="w-2 h-2 bg-accent rounded-full typing-dot"></div>
                <div className="w-2 h-2 bg-accent rounded-full typing-dot"></div>
              </div>
              <span className="text-sm text-muted-foreground">AI is thinking...</span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      {/* Input area */}
      <UserInput 
        onSendMessage={handleSendMessage} 
        onFileUpload={handleFileUpload}
        onLinkCrawl={handleLinkCrawl}
        isLoading={isLoading}
      />
    </div>
  );
};

export default ChatInterface;
