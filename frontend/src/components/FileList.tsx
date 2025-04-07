import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Eye, FileText, Trash2 } from "lucide-react";
import { useState } from "react";

interface File {
  id: string;
  name: string;
  content: string;
  type: string;
  selected?: boolean;
}

interface FileListProps {
  documents: File[];
  onDelete: (id: string) => void;
  onSelect: (id: string, selected: boolean) => void;
}

export function FileList({ documents, onDelete, onSelect }: FileListProps) {
  const [previewFile, setPreviewFile] = useState<File | null>(null);

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {documents.map((file) => (
            <div
              key={file.id}
              className="flex items-center justify-between p-2 rounded-md hover:bg-sidebar-accent/50 group"
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <Checkbox
                  checked={file.selected}
                  onCheckedChange={(checked) => onSelect(file.id, checked as boolean)}
                  className="shrink-0"
                />
                <div className="flex items-center gap-2 min-w-0">
                  <FileText className="h-4 w-4 text-sidebar-foreground shrink-0" />
                  <span className="text-sm text-sidebar-foreground truncate">{file.name}</span>
                </div>
              </div>
              
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setPreviewFile(file)}
                >
                  <Eye className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive"
                  onClick={() => onDelete(file.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <Dialog open={!!previewFile} onOpenChange={() => setPreviewFile(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>{previewFile?.name}</DialogTitle>
          </DialogHeader>
          <ScrollArea className="mt-4">
            <div className="p-4 bg-muted rounded-md">
              <pre className="whitespace-pre-wrap text-sm">
                {previewFile?.content}
              </pre>
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
} 