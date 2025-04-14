import { cn } from "@/lib/utils";
import { FileMetadata, LinkMetadata, Message, SearchResult, WebSearchMetadata } from "@/types";
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

function SearchResults({ results }: { results: SearchResult[] }) {
  return (
    <div className="mt-2 space-y-2">
      {results.map((result, index) => (
        <div key={index} className="bg-muted/50 rounded-lg p-3">
          <h4 className="font-medium text-sm">{result.title}</h4>
          <p className="text-sm text-muted-foreground mt-1">{result.content}</p>
          <span className="text-xs text-muted-foreground mt-1 block">Source: {result.source}</span>
        </div>
      ))}
    </div>
  );
}

function WebSearchResults({ results }: { results: Array<{ title: string, url: string, snippet: string }> }) {
  return (
    <div className="mt-4 space-y-3">
      {results.map((result, index) => (
        <a
          key={index}
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
        >
          <h4 className="font-medium text-sm text-primary">{result.title}</h4>
          <p className="text-sm text-muted-foreground mt-1">{result.snippet}</p>
          <span className="text-xs text-muted-foreground mt-1 block">{result.url}</span>
        </a>
      ))}
    </div>
  );
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
    // Get file extension from fileName
    const fileExt = metadata.fileName.split('.').pop()?.toLowerCase() || '';
    
    // Determine file type icon color based on extension
    const getFileColor = () => {
      switch (fileExt) {
        case 'pdf': return 'text-red-500';
        case 'doc':
        case 'docx': return 'text-blue-500';
        case 'xls':
        case 'xlsx': return 'text-green-500';
        case 'txt': return 'text-gray-500';
        default: return 'text-muted-foreground';
      }
    };

    // Format file size
    const formatFileSize = (bytes: number) => {
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
      <div className="w-full max-w-sm">
        <div className="border rounded-lg overflow-hidden bg-card hover:bg-accent/5 transition-colors">
          {/* File Preview Header */}
          <div className="p-4 flex items-start gap-3">
            <div className={cn(
              "p-2 rounded-lg bg-background",
              message.role === "assistant" ? "bg-accent/10" : "bg-primary/10"
            )}>
              <FileText className={cn("w-6 h-6", getFileColor())} />
            </div>
            
            <div className="flex-1 min-w-0">
              {/* Filename */}
              <h3 className="font-medium text-sm text-card-foreground truncate">
                {metadata.fileName}
              </h3>
              
              {/* File Info */}
              <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                <span className="uppercase">{fileExt}</span>
                <span>•</span>
                <span>{formatFileSize(metadata.fileSize)}</span>
              </div>
            </div>
          </div>

          {/* Preview Content */}
          <div className="border-t px-4 py-2">
            {metadata.content ? (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {metadata.content}
              </p>
            ) : (
              <p className="text-xs text-muted-foreground italic">
                No preview available
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="border-t px-4 py-2 flex justify-end">
            <button
              onClick={() => {
                // Here you would typically trigger a download
                // For now, we'll just log
                console.log('Download requested for:', metadata.fileName);
              }}
              className="text-xs text-primary hover:text-primary/80 transition-colors"
            >
              Download
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderLinkMessage = (metadata: LinkMetadata) => {
    console.log('Rendering link message with metadata:', metadata);
    
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
            <div className="h-48 relative bg-muted">
              <img 
                src={metadata.image} 
                alt={metadata.title || 'Link preview'}
                className="w-full h-full object-cover"
                onError={(e) => {
                  console.log('Image failed to load:', metadata.image);
                  const parent = e.currentTarget.parentElement;
                  if (parent) {
                    parent.style.display = 'none';
                  }
                }}
              />
            </div>
          )}
          
          {/* Content Section */}
          <div className="p-4 space-y-2">
            {/* Title */}
            <h3 className="font-medium text-sm text-card-foreground line-clamp-2">
              {metadata.title || metadata.url}
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
      
      case 'web_search':
        const metadata = message.metadata as WebSearchMetadata;
        return (
          <div>
            <div className="markdown-content prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
            {metadata.searchResults && <WebSearchResults results={metadata.searchResults} />}
          </div>
        );
      
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
        message.role === "user" ? "justify-end" : "justify-start",
        "message-appear",
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
        isLast ? "pb-8" : ""
      )}
    >
      {/* Avatar - Only show for assistant messages */}
      {message.role === "assistant" && (
        <div className="flex-shrink-0 mt-1">
          <div className="w-8 h-8 rounded-full flex items-center justify-center bg-accent/10 text-accent">
            <Bot size={18} />
          </div>
        </div>
      )}
      
      {/* Message content */}
      <div className={cn(
        "min-w-0",
        message.role === "user" ? "flex flex-col items-end" : ""
      )}>
        <div className="flex items-center gap-2 mb-1">
          <div className="text-sm font-medium text-muted-foreground">
            {message.role === "assistant" ? "JAMAL" : "You"}
          </div>
          <div className="text-xs text-muted-foreground">
            {new Date(message.timestamp).toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        </div>
        
        {message.type === 'link' ? (
          renderMessageContent()
        ) : (
          <div className={cn(
            "rounded-lg px-4 py-2 inline-block max-w-full",
            message.role === "assistant" 
              ? "bg-muted text-foreground" 
              : "bg-primary text-primary-foreground"
          )}>
            {renderMessageContent()}
          </div>
        )}
      </div>

      {/* Avatar - Only show for user messages */}
      {message.role === "user" && (
        <div className="flex-shrink-0 mt-1">
          <div className="w-8 h-8 rounded-full flex items-center justify-center bg-primary/10 text-primary">
            <User size={18} />
          </div>
        </div>
      )}
    </div>
  );
}
