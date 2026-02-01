import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MessagesSquare, PlusCircle, FileText, ChevronDown, ChevronUp, Trash2 } from 'lucide-react';
import './Sidebar.css';
import { getSessions, deleteSession, ChatSession } from '../utils/sessionStorage';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onClearChat: () => void;
  onStartNewChat: () => void;
  onLoadSession: (sessionId: string) => void;
  currentSessionId: string | null;
}

interface DocumentInfo {
  id: number;
  title: string;
  status: string;
  page_count?: number;
  article_count?: number;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  onClearChat,
  onStartNewChat,
  onLoadSession,
  currentSessionId
}) => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [totalDocuments, setTotalDocuments] = useState<number>(0);
  const [showDocuments, setShowDocuments] = useState(false);  // Default collapsed
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (isOpen) {
      fetchDocuments();
      loadSessions();
    }
  }, [isOpen, refreshKey]);

  const loadSessions = () => {
    const allSessions = getSessions();
    setSessions(allSessions);
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/documents/?limit=10`);
      setDocuments(response.data.documents);
      setTotalDocuments(response.data.total);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  };

  if (!isOpen) return null;

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    deleteSession(sessionId);
    if (sessionId === currentSessionId) {
      onStartNewChat();
    }
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2><MessagesSquare size={20} /> Sohbetler</h2>
        <button 
          className="new-chat-button"
          onClick={onStartNewChat}
          title="Yeni Sohbet"
        >
          <PlusCircle size={18} /> Yeni
        </button>
      </div>

      {/* Chat History */}
      <div className="sidebar-section">
        <h3>Geçmiş Sohbetler</h3>
        <div className="sessions-list">
          {sessions.length === 0 ? (
            <p className="empty-message">Henüz sohbet geçmişi yok</p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                onClick={() => onLoadSession(session.id)}
              >
                <div className="session-content">
                  <div className="session-title">{session.title}</div>
                  <div className="session-date">
                    {new Date(session.updatedAt).toLocaleDateString('tr-TR', {
                      day: 'numeric',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
                <button
                  className="delete-session-button"
                  onClick={(e) => handleDeleteSession(session.id, e)}
                  title="Sil"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Documents */}
      <div className="sidebar-section">
        <div className="section-header">
          <h3>Mevzuatlar</h3>
          <button 
            className="expand-button"
            onClick={() => setShowDocuments(!showDocuments)}
          >
            {showDocuments ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>
        <div className="document-count">
          {totalDocuments} doküman yüklü
        </div>
        
        {showDocuments && (
          <div className="documents-list">
            {documents.slice(0, 5).map((doc) => (
              <div key={doc.id} className="document-item">
                <div className="document-title" title={doc.title}>
                  <FileText size={16} /> {doc.title.substring(0, 40)}...
                </div>
                <div className="document-meta">
                  {doc.page_count && <span>{doc.page_count} sayfa</span>}
                  {doc.article_count && <span> • {doc.article_count} madde</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="sidebar-section">
        <button className="action-button clear-button" onClick={onClearChat}>
          🗑️ Sohbeti Temizle
        </button>
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="version-info">
          <small>SUBU Chatbot v2.0</small>
          <small>Powered by OpenAI GPT</small>
          <small className="creator-info">
            Created by <a href="https://www.linkedin.com/in/behlulalar/" target="_blank" rel="noopener noreferrer">BehlulAlar</a>
          </small>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
