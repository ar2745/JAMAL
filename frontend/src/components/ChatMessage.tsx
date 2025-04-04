import { cn } from "@/lib/utils";
import { FileMetadata, LinkMetadata, Message } from "@/types";
import { Bot, FileText, Link, User } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

interface ChatMessageProps {
  message: Message;
  isLast?: boolean;
}

function isFileMetadata(metadata: any): metadata is FileMetadata {
  return metadata && 'fileName' in metadata;
}

function isLinkMetadata(metadata: any): metadata is LinkMetadata {
  return metadata && 'url' in metadata;
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

  const renderFileMessage = (metadata: FileMetadata) => {
    return (
      <div className="flex items-center gap-2 p-2 bg-muted rounded-lg">
        <FileText className="w-5 h-5 text-muted-foreground" />
        <div className="flex flex-col">
          <span className="font-medium">{metadata.fileName}</span>
          <span className="text-xs text-muted-foreground">
            {metadata.fileType} • {metadata.fileSize / 1024} KB
          </span>
        </div>
      </div>
    );
  };

  const renderLinkMessage = (metadata: LinkMetadata) => {
    return (
      <div className="w-full max-w-lg">
        <a 
          href={metadata.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="block border rounded-lg overflow-hidden bg-card hover:bg-accent/5 transition-colors"
        >
          {/* Optional Image - Only shown if available and loads successfully */}
          {metadata.image && (
            <div className="h-32 relative bg-muted">
              <img 
                src={metadata.image} 
                alt=""
                className="w-full h-full object-cover"
                onError={(e) => {
                  const parent = e.currentTarget.parentElement;
                  if (parent) {
                    parent.style.display = 'none';
                  }
                }}
              />
            </div>
          )}
          
          {/* Content Section */}
          <div className="p-3 space-y-2">
            {/* Title */}
            <h3 className="font-medium text-sm text-card-foreground line-clamp-2">
              {metadata.title || 'Visit Link'}
            </h3>
            
            {/* Description - Only shown if available */}
            {metadata.description && (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {metadata.description}
              </p>
            )}
            
            {/* URL Display */}
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Link className="w-3 h-3" />
              <span className="truncate">
                {new URL(metadata.url).hostname}
              </span>
            </div>
          </div>
        </a>
      </div>
    );
  };

  const renderMessageContent = () => {
    console.log('Rendering message:', message);
    
    if (!message.metadata) {
      console.log('No metadata, rendering as plain text');
      return <p className="whitespace-pre-wrap break-words">{message.content}</p>;
    }

    switch (message.type) {
      case 'file':
        if (!isFileMetadata(message.metadata)) {
          console.log('Invalid file metadata, rendering as plain text');
          return <p className="whitespace-pre-wrap break-words">{message.content}</p>;
        }
        console.log('Rendering file message');
        return renderFileMessage(message.metadata);
      
      case 'link':
        if (!isLinkMetadata(message.metadata)) {
          console.log('Invalid link metadata, rendering as plain text');
          return <p className="whitespace-pre-wrap break-words">{message.content}</p>;
        }
        console.log('Rendering link message with metadata:', message.metadata);
        return renderLinkMessage(message.metadata);
      
      case 'text':
      default:
        console.log('Rendering text message');
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
        "py-4 px-4 md:px-8 flex gap-4",
        "message-appear",
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
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
        
        {message.type === 'link' ? (
          renderMessageContent()
        ) : (
          <div className={cn(
            "rounded-lg px-4 py-2",
            message.role === "assistant" 
              ? "bg-muted text-foreground" 
              : "bg-primary text-primary-foreground"
          )}>
            {renderMessageContent()}
          </div>
        )}

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
