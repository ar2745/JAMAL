import { ScrollArea } from "@/components/ui/scroll-area";
import { Message } from "@/types";
import { useEffect, useRef, useState } from "react";
import UserInput from "./UserInput";

interface ChatContainerProps {
  selectedDocuments: Array<{
    id: string;
    name: string;
    content: string;
    type: string;
    selected?: boolean;
  }>;
  selectedLinks: Array<{
    id: string;
    url: string;
    title: string;
    description?: string;
    content?: string;
    selected?: boolean;
  }>;
  chatTitle: string;
  setChatTitle: (title: string) => void;
}

export default function ChatContainer({
  selectedDocuments,
  selectedLinks,
  chatTitle,
  setChatTitle
}: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (message: Message) => {
    setMessages((prev) => [...prev, message]);
    setIsLoading(true);

    try {
      // Prepare context from selected documents and links
      const context = [
        ...selectedDocuments.map(doc => `Document: ${doc.name}\n${doc.content}`),
        ...selectedLinks.map(link => `Link: ${link.title}\n${link.content || link.description || ''}`)
      ].join('\n\n');

      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message.content,
          type: message.type,
          metadata: message.metadata || {},
          context: context || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const data = await response.json();
      const assistantMessage: Message = {
        id: generateUniqueId(),
        role: "assistant",
        content: data.response,
        type: "text",
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      
      // Update chat title based on first message if it's still "New Chat"
      if (chatTitle === "New Chat" && messages.length === 0) {
        setChatTitle(message.content.slice(0, 30) + (message.content.length > 30 ? "..." : ""));
      }
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        id: generateUniqueId(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        type: "text",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateUniqueId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === "user"
                    ? "bg-accent text-accent-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                <span className="text-xs opacity-70 mt-1 block">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg p-3">
                <p>Thinking...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Form */}
      <UserInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
} 