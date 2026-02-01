/**
 * Chat Session Storage Utilities
 * Manages chat sessions in localStorage
 */

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  metadata?: any;
  timestamp: Date;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

const STORAGE_KEY = 'subu_chat_sessions';
const MAX_SESSIONS = 50; // Keep last 50 sessions

/**
 * Get all chat sessions from localStorage
 */
export const getSessions = (): ChatSession[] => {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) return [];
    
    const sessions = JSON.parse(data);
    // Convert date strings back to Date objects
    return sessions.map((s: any) => ({
      ...s,
      createdAt: new Date(s.createdAt),
      updatedAt: new Date(s.updatedAt),
      messages: s.messages.map((m: any) => ({
        ...m,
        timestamp: new Date(m.timestamp)
      }))
    }));
  } catch (error) {
    console.error('Error loading sessions:', error);
    return [];
  }
};

/**
 * Save a chat session
 */
export const saveSession = (session: ChatSession): void => {
  try {
    const sessions = getSessions();
    
    // Find existing session or add new one
    const existingIndex = sessions.findIndex(s => s.id === session.id);
    
    if (existingIndex >= 0) {
      sessions[existingIndex] = session;
    } else {
      sessions.unshift(session); // Add to beginning
    }
    
    // Keep only MAX_SESSIONS most recent
    const trimmedSessions = sessions.slice(0, MAX_SESSIONS);
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmedSessions));
  } catch (error) {
    console.error('Error saving session:', error);
  }
};

/**
 * Delete a chat session
 */
export const deleteSession = (sessionId: string): void => {
  try {
    const sessions = getSessions();
    const filtered = sessions.filter(s => s.id !== sessionId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.error('Error deleting session:', error);
  }
};

/**
 * Get a single session by ID
 */
export const getSession = (sessionId: string): ChatSession | null => {
  const sessions = getSessions();
  return sessions.find(s => s.id === sessionId) || null;
};

/**
 * Generate a title from the first user message
 */
export const generateSessionTitle = (firstMessage: string): string => {
  // Take first 40 characters
  const title = firstMessage.substring(0, 40);
  return title.length < firstMessage.length ? title + '...' : title;
};

/**
 * Generate a unique session ID
 */
export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Clear all sessions
 */
export const clearAllSessions = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Error clearing sessions:', error);
  }
};
