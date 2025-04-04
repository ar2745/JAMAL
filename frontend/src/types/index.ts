export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  type: 'text' | 'file' | 'link';
  metadata?: {
    fileName?: string;
    fileType?: string;
    fileSize?: number;
    url?: string;
    title?: string;
    description?: string;
    image?: string;
    content?: string;
  };
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
