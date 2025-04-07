import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Eye, Link as LinkIcon, Trash2 } from "lucide-react";
import { useState } from "react";

interface Link {
  id: string;
  url: string;
  title?: string;
  description?: string;
  content?: string;
  selected?: boolean;
}

interface LinkListProps {
  links: Link[];
  onDelete: (id: string) => void;
  onSelect: (id: string, selected: boolean) => void;
}

export function LinkList({ links, onDelete, onSelect }: LinkListProps) {
  const [previewLink, setPreviewLink] = useState<Link | null>(null);

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {links.map((link) => (
            <div
              key={link.id}
              className="flex items-center justify-between p-2 rounded-md hover:bg-sidebar-accent/50 group"
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <Checkbox
                  checked={link.selected}
                  onCheckedChange={(checked) => onSelect(link.id, checked as boolean)}
                  className="shrink-0"
                />
                <div className="flex items-center gap-2 min-w-0">
                  <LinkIcon className="h-4 w-4 text-sidebar-foreground shrink-0" />
                  <span className="text-sm text-sidebar-foreground truncate">{link.title || link.url}</span>
                </div>
              </div>
              
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setPreviewLink(link)}
                >
                  <Eye className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive"
                  onClick={() => onDelete(link.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <Dialog open={!!previewLink} onOpenChange={() => setPreviewLink(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>{previewLink?.title || previewLink?.url}</DialogTitle>
          </DialogHeader>
          <ScrollArea className="mt-4">
            <div className="p-4 bg-muted rounded-md">
              {previewLink?.description && (
                <p className="text-sm mb-4">{previewLink.description}</p>
              )}
              {previewLink?.content && (
                <pre className="whitespace-pre-wrap text-sm">
                  {previewLink.content}
                </pre>
              )}
              <a 
                href={previewLink?.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline"
              >
                Open in new tab
              </a>
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
} 