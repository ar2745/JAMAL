import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Message } from "@/types";
import { Globe, Lightbulb, Link, Search, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import LinkInputDialog from "./LinkInputDialog";

// Use NEXT_PUBLIC_ prefix for client-side environment variables
const API_URL = typeof window !== 'undefined' 
  ? (window as any).ENV?.API_URL || 'http://localhost:5000'
  : 'http://localhost:5000';

const generateUniqueId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

interface UserInputProps {
  onSendMessage: (message: Message) => void;
  onFileUpload?: (file: File) => void;
  isLoading?: boolean;
}

export default function UserInput({ 
  onSendMessage, 
  onFileUpload,
  isLoading = false 
}: UserInputProps) {
  const [message, setMessage] = useState("");
  const [isLinkDialogOpen, setIsLinkDialogOpen] = useState(false);
  const [isWebSearchMode, setIsWebSearchMode] = useState(false);
  const [isReasoningMode, setIsReasoningMode] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize input - only grow if content is larger than container
  useEffect(() => {
    if (inputRef.current) {
      const containerWidth = inputRef.current.parentElement?.clientWidth || 0;
      inputRef.current.style.width = "100%";
      const contentWidth = inputRef.current.scrollWidth;
      
      // Only set a larger width if the content is wider than the container
      if (contentWidth > containerWidth) {
        inputRef.current.style.width = `${contentWidth}px`;
      }
    }
  }, [message]);

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return;

    const processedMessage = message.trim();
    setMessage("");

    // Create the message object with mode flags
    const textMessage: Message = {
      id: generateUniqueId(),
      content: processedMessage,
      role: 'user',
      type: isWebSearchMode ? 'web_search' : 'text',
      timestamp: new Date().toISOString(),
      metadata: {
        isWebSearch: isWebSearchMode,
        isReasoningMode: isReasoningMode
      }
    };

    onSendMessage(textMessage);
  };

  const handleLinkDialogSubmit = async (url: string) => {
    try {
      console.log('Submitting link:', url);
      
      // First, upload the link to get metadata
      const uploadResponse = await fetch(`${API_URL}/link_upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json();
        console.error('Link upload failed:', errorData);
        throw new Error(errorData.error || 'Failed to process link');
      }

      const uploadData = await uploadResponse.json();
      console.log('Link upload response:', uploadData);
      
      // Construct the link message directly from the upload response
      const linkMessage: Message = {
        id: generateUniqueId(),
        content: url,
        role: 'user',
        type: 'link',
        metadata: {
          url: url,
          title: uploadData.link.title || 'Visit Link',
          description: uploadData.link.description,
          image: uploadData.link.image
        },
        timestamp: new Date().toISOString()
      };

      console.log('Created link message:', linkMessage);
      
      // Add the link message to the chat
      onSendMessage(linkMessage);
    } catch (error) {
      console.error('Error processing link:', error);
      // Show error to user
      alert(error instanceof Error ? error.message : 'Failed to process link');
    }
  };

  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:5000/document_upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Upload failed:', errorText);
        throw new Error(`Failed to upload file: ${errorText}`);
      }

      const data = await response.json();
      console.log('Upload response:', data);
      
      // Create a file message with metadata
      const fileMessage: Message = {
        id: generateUniqueId(),
        content: file.name,
        role: 'user',
        type: 'file',
        metadata: {
          fileName: file.name,
          fileType: file.type,
          fileSize: file.size,
          content: data.content || '' // Use content from response if available
        },
        timestamp: new Date().toISOString()
      };

      onSendMessage(fileMessage);
    } catch (error) {
      console.error('Error uploading file:', error);
      // Fallback to basic file message if upload fails
      const fileMessage: Message = {
        id: generateUniqueId(),
        content: file.name,
        role: 'user',
        type: 'file',
        metadata: {
          fileName: file.name,
          fileType: file.type,
          fileSize: file.size
        },
        timestamp: new Date().toISOString()
      };
      onSendMessage(fileMessage);
    }
  };

  return (
    <div className={`flex items-center gap-2 p-4 border-t ${isWebSearchMode ? 'bg-blue-50 dark:bg-blue-950/20' : ''}`}>
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        onChange={handleFileChange}
      />
      <Button
        variant="outline"
        size="icon"
        onClick={handleFileUpload}
        disabled={isLoading}
      >
        <Upload className="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => setIsLinkDialogOpen(true)}
        disabled={isLoading}
      >
        <Link className="h-4 w-4" />
      </Button>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant={isWebSearchMode ? "default" : "outline"}
              size="icon"
              onClick={() => setIsWebSearchMode(!isWebSearchMode)}
              disabled={isLoading}
              className={`relative ${isWebSearchMode ? 'bg-blue-500 hover:bg-blue-600 text-white' : ''}`}
            >
              <Globe className="h-4 w-4" />
              {isWebSearchMode && (
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {isWebSearchMode ? "Web Search Mode Active - Click to disable" : "Enable Web Search Mode"}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      <Button
        variant={isReasoningMode ? "default" : "outline"}
        size="icon"
        onClick={() => setIsReasoningMode(!isReasoningMode)}
        disabled={isLoading}
        className="relative"
        title={isReasoningMode ? "Reasoning Mode Active" : "Enable Reasoning Mode"}
      >
        <Lightbulb className="h-4 w-4" />
        {isReasoningMode && (
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-500 rounded-full" />
        )}
      </Button>
      
      <div className={`flex-1 relative ${isWebSearchMode ? 'ring-2 ring-blue-500 rounded-md' : ''}`}>
        <Input
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={isWebSearchMode ? "Search the web..." : "Type a message..."}
          className={`w-full ${isWebSearchMode ? 'pl-10' : ''}`}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
          disabled={isLoading}
        />
        {isWebSearchMode && (
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-blue-500" />
        )}
      </div>
      
      <Button 
        onClick={handleSendMessage} 
        disabled={isLoading}
        className={isWebSearchMode ? 'bg-blue-500 hover:bg-blue-600 text-white' : ''}
      >
        {isWebSearchMode ? "Search" : "Send"}
      </Button>
      
      <LinkInputDialog
        isOpen={isLinkDialogOpen}
        onClose={() => setIsLinkDialogOpen(false)}
        onSubmit={handleLinkDialogSubmit}
      />
    </div>
  );
}
