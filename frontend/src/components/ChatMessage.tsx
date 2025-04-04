import { cn } from "@/lib/utils";
import { Message } from "@/types";
import { Bot, FileText, Link, User } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

interface ChatMessageProps {
  message: Message;
  isLast?: boolean;
}

export default function ChatMessage({ message, isLast = false }: ChatMessageProps) {
  const [isVisible, setIsVisible] = useState(false);
  
  // Animation effect when message appears
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  const renderMessageContent = () => {
    switch (message.type) {
      case 'file':
        return (
          <div className="flex items-center gap-2 p-2 bg-muted rounded-lg">
            <FileText className="w-5 h-5 text-muted-foreground" />
            <div className="flex flex-col">
              <span className="font-medium">{message.metadata?.fileName}</span>
              <span className="text-xs text-muted-foreground">
                {message.metadata?.fileType} • {(message.metadata?.fileSize || 0) / 1024} KB
              </span>
            </div>
          </div>
        );
      
      case 'link':
        return (
          <div className="flex flex-col gap-2 p-3 bg-muted rounded-lg">
            <div className="flex items-center gap-2">
              <Link className="w-5 h-5 text-muted-foreground" />
              <div className="flex flex-col">
                <a 
                  href={message.metadata?.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="font-medium hover:underline text-primary"
                >
                  {message.metadata?.title || message.metadata?.url}
                </a>
                {message.metadata?.description && (
                  <span className="text-sm text-muted-foreground line-clamp-2">
                    {message.metadata.description}
                  </span>
                )}
              </div>
            </div>
            {message.metadata?.image && (
              <div className="mt-2 rounded-md overflow-hidden">
                <img 
                  src={message.metadata.image} 
                  alt={message.metadata.title || "Link preview"} 
                  className="w-full h-32 object-cover"
                />
              </div>
            )}
            <div className="text-xs text-muted-foreground mt-1">
              {new URL(message.metadata?.url || '').hostname}
            </div>
          </div>
        );
      
      case 'text':
      default:
        return message.role === "assistant" ? (
          <div className="markdown-content prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown>
              {message.content}
            </ReactMarkdown>
          </div>
        ) : (
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        );
    }
  };

  return (
    <div 
      className={cn(
        "py-4 px-4 md:px-8 flex gap-4 transition-all duration-300",
        "message-appear",
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
        message.role === "assistant" ? "bg-muted/50" : "",
        isLast ? "pb-8" : ""
      )}
    >
      {/* Avatar */}
      <div className="flex-shrink-0 mt-1">
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center",
          message.role === "assistant" 
            ? "bg-accent/10 text-accent" 
            : "bg-primary/10 text-primary"
        )}>
          {message.role === "assistant" ? <Bot size={18} /> : <User size={18} />}
        </div>
      </div>
      
      {/* Message content */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium mb-1 text-muted-foreground">
          {message.role === "assistant" ? "Chatbot" : "You"}
        </div>
        
        <div className={cn(
          "rounded-lg px-4 py-2",
          message.role === "assistant" 
            ? "bg-muted text-foreground" 
            : "bg-primary text-primary-foreground"
        )}>
          {renderMessageContent()}
        </div>

        {/* Timestamp */}
        <div className="text-xs text-muted-foreground mt-1">
          {new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
}
