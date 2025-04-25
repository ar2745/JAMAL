import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { AlertCircle, Brain, Search } from "lucide-react";
import React, { useEffect, useState } from 'react';

interface MemoryEntry {
  id: string;
  conversation_id: string;
  type: string;
  timestamp: string;
  text: string;
}

interface MemoryViewerResponse {
  entries: MemoryEntry[];
  total: number;
  page: number;
  page_size: number;
}

const MemoryViewer: React.FC = () => {
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [conversationId, setConversationId] = useState('');
  const [type, setType] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEntries = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        ...(conversationId && { conversation_id: conversationId }),
        ...(type !== 'all' && { type })
      });

      const response = await fetch(`http://localhost:5000/memory_viewer?${params}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch memory entries');
      }

      const data: MemoryViewerResponse = await response.json();
      
      if (!data || !Array.isArray(data.entries)) {
        throw new Error('Invalid response format');
      }

      setEntries(data.entries);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Error fetching memory entries:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while fetching memory entries');
      setEntries([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, [page, pageSize, conversationId, type]);

  const handlePageChange = (value: number) => {
    setPage(value);
  };

  const handlePageSizeChange = (value: string) => {
    setPageSize(Number(value));
    setPage(1);
  };

  const handleConversationIdChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setConversationId(event.target.value);
    setPage(1);
  };

  const handleTypeChange = (value: string) => {
    setType(value);
    setPage(1);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Brain className="h-4 w-4 animate-spin" />
          <span>Loading memories...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full p-4 space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by conversation ID..."
            value={conversationId}
            onChange={handleConversationIdChange}
            className="pl-8"
          />
        </div>
        <Select value={type} onValueChange={handleTypeChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="user_message">User Message</SelectItem>
            <SelectItem value="bot_message">Bot Message</SelectItem>
            <SelectItem value="document">Document</SelectItem>
            <SelectItem value="link">Link</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Memory Entries */}
      <ScrollArea className="flex-1 rounded-md border">
        <div className="p-4">
          {entries.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-muted-foreground">
              No memory entries found
            </div>
          ) : (
            entries.map((entry) => (
              <div
                key={entry.id}
                className="group flex flex-col gap-2 p-4 rounded-lg border bg-card hover:bg-accent/5 transition-colors mb-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium capitalize">{entry.type.replace('_', ' ')}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(entry.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="text-sm text-card-foreground">
                  {entry.text}
                </div>
                <div className="text-xs text-muted-foreground">
                  Conversation ID: {entry.conversation_id}
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Pagination */}
      {total > 0 && (
        <div className="flex items-center justify-between">
          <Select value={pageSize.toString()} onValueChange={handlePageSizeChange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Items per page" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10 per page</SelectItem>
              <SelectItem value="25">25 per page</SelectItem>
              <SelectItem value="50">50 per page</SelectItem>
              <SelectItem value="100">100 per page</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            {Array.from({ length: Math.ceil(total / pageSize) }, (_, i) => i + 1).map((pageNum) => (
              <Button
                key={pageNum}
                variant={page === pageNum ? "default" : "ghost"}
                size="sm"
                onClick={() => handlePageChange(pageNum)}
              >
                {pageNum}
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoryViewer; 