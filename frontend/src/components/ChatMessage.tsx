import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, MessageCircle, BookOpen, ChevronDown, ChevronUp, BarChart3 } from 'lucide-react';
import './ChatMessage.css';

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

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  metadata?: Metadata;
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false);
  const [showMetadata, setShowMetadata] = useState(false);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('tr-TR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (message.role === 'user') {
    return (
      <div className="message-wrapper user-message-wrapper">
        <div className="message user-message">
          <div className="message-content">
            <p>{message.content}</p>
          </div>
          <div className="message-time">{formatTime(message.timestamp)}</div>
        </div>
        <div className="message-avatar user-avatar">
          <User size={20} />
        </div>
      </div>
    );
  }

  return (
    <div className="message-wrapper assistant-message-wrapper">
      <div className="message-avatar assistant-avatar">
        <MessageCircle size={18} />
      </div>
      <div className="message assistant-message">
        <div className="message-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="sources-section">
            <button 
              className="sources-toggle"
              onClick={() => setShowSources(!showSources)}
            >
              <BookOpen size={16} /> Kaynaklar ({message.sources.length})
              {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
            
            {showSources && (
              <div className="sources-list">
                {message.sources.map((source, idx) => (
                  <div key={idx} className="source-card">
                    <div className="source-header">
                      <span className="source-title">{source.title}</span>
                      <span className="source-score">
                        {(source.relevance_score * 100).toFixed(0)}% uygun
                      </span>
                    </div>
                    <div className="source-details">
                      <span className="source-article">
                        Madde {source.article_number}
                        {source.article_title && `: ${source.article_title}`}
                      </span>
                    </div>
                    <div className="source-preview">
                      {source.preview}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Metadata */}
        {message.metadata && (
          <div className="metadata-section">
            <button 
              className="metadata-toggle"
              onClick={() => setShowMetadata(!showMetadata)}
            >
              <BarChart3 size={16} /> Detaylar
              {showMetadata ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
            
            {showMetadata && (
              <div className="metadata-details">
                <div className="metadata-item">
                  <span className="metadata-label">Model:</span>
                  <span className="metadata-value">{message.metadata.model}</span>
                </div>
                <div className="metadata-item">
                  <span className="metadata-label">Tokens:</span>
                  <span className="metadata-value">{message.metadata.tokens.toLocaleString()}</span>
                </div>
                <div className="metadata-item">
                  <span className="metadata-label">Maliyet:</span>
                  <span className="metadata-value">${message.metadata.cost.toFixed(4)}</span>
                </div>
                <div className="metadata-item">
                  <span className="metadata-label">Süre:</span>
                  <span className="metadata-value">{message.metadata.response_time.toFixed(2)}s</span>
                </div>
                <div className="metadata-item">
                  <span className="metadata-label">Bulunan Kaynak:</span>
                  <span className="metadata-value">{message.metadata.retrieved_docs}</span>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="message-time">{formatTime(message.timestamp)}</div>
      </div>
    </div>
  );
};

export default ChatMessage;
