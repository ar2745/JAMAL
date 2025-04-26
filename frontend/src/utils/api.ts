const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Error handling helper
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'API request failed');
  }
  return response.json();
};

// Memory API calls
export const retrieveMemory = async (query: string) => {
  const response = await fetch(`${API_BASE_URL}/retrieve_memory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  
  return handleResponse(response);
};

export const storeMemory = async (memory: string) => {
  const response = await fetch(`${API_BASE_URL}/store_memory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ memory }),
  });
  
  return handleResponse(response);
};

// Chat API calls
export const sendMessage = async (message: string, conversationId?: string) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      message, 
      conversation_id: conversationId 
    }),
  });
  
  return handleResponse(response);
};

export const getConversations = async () => {
  const response = await fetch(`${API_BASE_URL}/conversations`);
  return handleResponse(response);
};

export const getConversation = async (id: string) => {
  const response = await fetch(`${API_BASE_URL}/conversations/${id}`);
  return handleResponse(response);
};

export const deleteConversation = async (id: string) => {
  const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
    method: 'DELETE',
  });
  
  return handleResponse(response);
};

// Document API calls
export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/document_upload`, {
    method: 'POST',
    body: formData,
  });
  
  return handleResponse(response);
};

export const getDocuments = async () => {
  const response = await fetch(`${API_BASE_URL}/documents`);
  return handleResponse(response);
};

export const deleteDocument = async (id: string) => {
  const response = await fetch(`${API_BASE_URL}/document_delete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(id)
  });
  
  return handleResponse(response);
};

// Link API calls
export const crawlLink = async (url: string) => {
  const response = await fetch(`${API_BASE_URL}/crawl_link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  
  return handleResponse(response);
};

export const getLinks = async () => {
  const response = await fetch(`${API_BASE_URL}/links`);
  return handleResponse(response);
};

export const deleteLink = async (id: string) => {
  const response = await fetch(`${API_BASE_URL}/link_delete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ filename: id })
  });
  
  return handleResponse(response);
};
