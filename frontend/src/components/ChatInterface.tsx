import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { BookOpen, Send, Menu, Hand, Trophy, Clock, Beaker, Hourglass } from 'lucide-react';
import ChatMessage from './ChatMessage';
import Sidebar from './Sidebar';
import './ChatInterface.css';
import {
  ChatSession,
  saveSession,
  generateSessionId,
  generateSessionTitle,
  getSession
} from '../utils/sessionStorage';

const API_BASE_URL = (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim() !== '') ? process.env.REACT_APP_API_URL : (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000');

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  metadata?: Metadata;
  timestamp: Date;
}

interface Source {
  title: string;
  article_number: string;
  article_title?: string;
  relevance_score: number;
  preview: string;
}

interface Metadata {
  retrieved_docs: number;
  tokens: number;
  cost: number;
  response_time: number;
  model: string;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [totalCost, setTotalCost] = useState(0); // Used in session storage, not displayed in UI
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessionRefreshTrigger, setSessionRefreshTrigger] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    // Create new session if this is the first message
    let sessionId = currentSessionId;
    if (!sessionId) {
      sessionId = generateSessionId();
      setCurrentSessionId(sessionId);
    }

    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputValue('');
    setIsLoading(true);

    try {
      // Build conversation history (last 10 messages for context)
      const conversationHistory = messages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await axios.post(`${API_BASE_URL}/api/chat/`, {
        question: inputValue,
        conversation_history: conversationHistory,
        include_sources: true
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        metadata: response.data.metadata,
        timestamp: new Date()
      };

      const finalMessages = [...newMessages, assistantMessage];
      setMessages(finalMessages);
      setTotalCost(prev => prev + response.data.metadata.cost);

      const session: ChatSession = {
        id: sessionId,
        title: messages.length === 0 ? generateSessionTitle(inputValue) : (getSession(sessionId)?.title || generateSessionTitle(inputValue)),
        messages: finalMessages,
        createdAt: getSession(sessionId)?.createdAt || new Date(),
        updatedAt: new Date()
      };
      saveSession(session);
      setSessionRefreshTrigger(prev => prev + 1);

    } catch (error: unknown) {
      console.error('Error:', error);
      const isNetworkError = axios.isAxiosError(error) && (error.code === 'ERR_NETWORK' || !error.response);
      const content = isNetworkError
        ? 'Sunucuya bağlanılamıyor. İnternet bağlantınızı veya sunucu erişimini kontrol edin; bağlantı kurulunca tekrar deneyin.'
        : 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.';
      const errorMessage: Message = {
        role: 'assistant',
        content,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setTotalCost(0);
    setCurrentSessionId(null);
  };

  const startNewChat = () => {
    setMessages([]);
    setTotalCost(0);
    setCurrentSessionId(null);
  };

  const loadSession = (sessionId: string) => {
    const session = getSession(sessionId);
    if (session) {
      setMessages(session.messages);
      setCurrentSessionId(session.id);
      // Calculate total cost from metadata
      const cost = session.messages.reduce((total, msg) => {
        return total + (msg.metadata?.cost || 0);
      }, 0);
      setTotalCost(cost);
    }
  };

  return (
    <div className="chat-container">
      {/* Mobilde sidebar açıkken overlay - dışarı tıklanınca kapat */}
      {sidebarOpen && (
        <div 
          className="sidebar-overlay" 
          onClick={() => setSidebarOpen(false)}
          onKeyDown={(e) => e.key === 'Escape' && setSidebarOpen(false)}
          role="button"
          tabIndex={0}
          aria-label="Sidebar kapat"
        />
      )}
      <Sidebar 
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onClearChat={clearChat}
        onStartNewChat={startNewChat}
        onLoadSession={loadSession}
        currentSessionId={currentSessionId}
        sessionRefreshTrigger={sessionRefreshTrigger}
      />
      
      <div className={`main-content ${!sidebarOpen ? 'sidebar-closed' : ''}`}>
        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <button 
              className="sidebar-toggle"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <Menu size={24} />
            </button>
            <div className="header-title">
              <h1><BookOpen size={24} /> SUBU Mevzuat Asistanı</h1>
              <p>Sakarya Uygulamalı Bilimler Üniversitesi</p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-content">
                <h2><Hand size={28} /> Hoş Geldiniz!</h2>
                <p>Üniversite mevzuatları hakkında sorular sorabilirsiniz.</p>
                <div className="example-questions">
                  <h3>Örnek Sorular:</h3>
                  <div className="example-card" onClick={() => setInputValue('Akademik personele ödül nasıl verilir?')}>
                    <span className="example-icon"><Trophy size={20} /></span>
                    <span>Akademik personele ödül nasıl verilir?</span>
                  </div>
                  <div className="example-card" onClick={() => setInputValue('Lisansüstü öğrencilerin azami süreleri nedir?')}>
                    <span className="example-icon"><Clock size={20} /></span>
                    <span>Lisansüstü öğrencilerin azami süreleri nedir?</span>
                  </div>
                  <div className="example-card" onClick={() => setInputValue('Bilimsel araştırma projesi başvurusu nasıl yapılır?')}>
                    <span className="example-icon"><Beaker size={20} /></span>
                    <span>Bilimsel araştırma projesi başvurusu nasıl yapılır?</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message, index) => (
                <ChatMessage key={index} message={message} />
              ))}
              {isLoading && (
                <div className="loading-indicator">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <p>Düşünüyorum...</p>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Sorunuzu yazın..."
              disabled={isLoading}
              rows={1}
            />
            <button 
              onClick={handleSendMessage}
              disabled={isLoading || !inputValue.trim()}
              className="send-button"
            >
              {isLoading ? <Hourglass size={20} /> : <Send size={20} />}
            </button>
          </div>
          <div className="input-hint">
            <small>Enter ile gönder • Shift+Enter ile yeni satır</small>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
