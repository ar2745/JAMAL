import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { Message, SUPPORTED_FILE_TYPES } from "@/types";
import { FileUp, SendHorizontal } from "lucide-react";
import { ChangeEvent, useEffect, useRef, useState } from "react";

const generateUniqueId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

interface UserInputProps {
  onSendMessage: (message: Message) => void;
  isLoading?: boolean;
}

export default function UserInput({ 
  onSendMessage, 
  isLoading = false 
}: UserInputProps) {
  const [message, setMessage] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 200)}px`;
    }
  }, [message]);

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    // Process any URLs in the message
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const urls = message.match(urlRegex);
    let processedMessage = message;

    if (urls) {
        for (const url of urls) {
            // Create a link message
            const linkMessage: Message = {
                id: generateUniqueId(),
                content: url,
                role: 'user',
                type: 'link',
                metadata: {
                    url: url
                },
                timestamp: new Date().toISOString()
            };
            onSendMessage(linkMessage);
            processedMessage = processedMessage.replace(url, '').trim();
        }
    }

    // Send the processed message if it's not empty
    if (processedMessage.trim()) {
        onSendMessage({
            id: generateUniqueId(),
            content: processedMessage,
            role: 'user',
            type: 'text',
            timestamp: new Date().toISOString()
        });
    }

    setMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileUpload = async (file: File) => {
    // Validate file type
    const fileType = file.type;
    const isSupported = Object.values(SUPPORTED_FILE_TYPES).some(types => 
      types.includes(fileType)
    );

    if (!isSupported) {
      toast({
        title: "Unsupported File Type",
        description: "Please upload a supported file type (PDF, DOCX, TXT, etc.)",
        variant: "destructive",
      });
      return;
    }

    // Upload file to backend
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('http://localhost:5000/document_upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to upload file');
      }

      const data = await response.json();
      
      // Create file message with the extracted content
      const fileMessage: Message = {
        id: generateUniqueId(),
        content: file.name,
        role: 'user',
        type: 'file',
        metadata: {
          fileName: file.name,
          fileType: file.type,
          fileSize: file.size,
          content: data.content
        },
        timestamp: new Date().toISOString()
      };
      onSendMessage(fileMessage);

      toast({
        title: "File Uploaded",
        description: `${file.name} has been uploaded successfully.`,
      });

    } catch (error) {
      console.error('Error uploading file:', error);
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "There was an error uploading your file.",
        variant: "destructive",
      });
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  return (
    <div className="relative flex items-center gap-2 p-4 border-t">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept={Object.values(SUPPORTED_FILE_TYPES).flat().join(',')}
      />
      <div
        className={cn(
          "flex-1 min-h-[44px] max-h-[200px] rounded-md border bg-background px-3 py-2 relative",
          isDragging && "border-primary"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message or drag & drop a file..."
          className="w-full resize-none bg-transparent outline-none pr-8"
          rows={1}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-accent/50 text-muted-foreground hover:text-accent-foreground transition-colors"
          aria-label="Upload file"
        >
          <FileUp className="h-4 w-4" />
        </button>
      </div>
      <button
        onClick={handleSendMessage}
        disabled={isLoading || !message.trim()}
        className={cn(
          "p-2 rounded-md transition-colors",
          isLoading || !message.trim()
            ? "text-muted-foreground"
            : "text-primary hover:bg-accent"
        )}
        aria-label="Send message"
      >
        <SendHorizontal className="h-5 w-5" />
      </button>
    </div>
  );
}
