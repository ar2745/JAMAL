export interface FileMetadata {
  fileName: string;
  fileType: string;
  fileSize: number;
  content?: string;
}

export interface LinkMetadata {
  url: string;
  title?: string;
  description?: string;
  image?: string;
}

export interface WebSearchMetadata {
  isWebSearch: boolean;
  searchResults?: Array<{
    title: string;
    url: string;
    snippet: string;
  }>;
}

export interface SearchResult {
  title: string;
  content: string;
  source: string;
  relevance?: number;
}

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  type: 'text' | 'file' | 'link' | 'web_search';
  timestamp: string;
  metadata?: FileMetadata | LinkMetadata | WebSearchMetadata;
  searchResults?: SearchResult[];
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  selectedDocuments?: string[];
  selectedLinks?: string[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  createdAt: Date;
}

export interface Link {
  id: string;
  url: string;
  title: string;
  description: string;
  createdAt: Date;
}

export interface SettingsType {
  apiEndpoint: string;
  theme: 'light' | 'dark' | 'system';
  messageDisplayCount: number;
}

export type FileType = 
  | 'pdf'
  | 'docx'
  | 'txt'
  | 'html'
  | 'csv'
  | 'json'
  | 'md'
  | 'rtf'
  | 'xlsx'
  | 'pptx';

export const SUPPORTED_FILE_TYPES: Record<FileType, string[]> = {
  pdf: ['application/pdf'],
  docx: ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  txt: ['text/plain'],
  html: ['text/html'],
  csv: ['text/csv'],
  json: ['application/json'],
  md: ['text/markdown'],
  rtf: ['application/rtf'],
  xlsx: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
  pptx: ['application/vnd.openxmlformats-officedocument.presentationml.presentation']
};
