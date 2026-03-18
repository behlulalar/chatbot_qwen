import React, { useState, useEffect } from 'react';
import { MessagesSquare, PlusCircle, Trash2, X } from 'lucide-react';
import './Sidebar.css';
import { getSessions, deleteSession, ChatSession } from '../utils/sessionStorage';

const API_BASE_URL = (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim() !== '') ? process.env.REACT_APP_API_URL : (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000');

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onClearChat: () => void;
  onStartNewChat: () => void;
  onLoadSession: (sessionId: string) => void;
  currentSessionId: string | null;
  sessionRefreshTrigger?: number;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  onToggle,
  onClearChat,
  onStartNewChat,
  onLoadSession,
  currentSessionId,
  sessionRefreshTrigger = 0
}) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    loadSessions();
  }, [isOpen, refreshKey, sessionRefreshTrigger]);

  const loadSessions = () => {
    const allSessions = getSessions();
    setSessions(allSessions);
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
        <div className="sidebar-header-actions">
          <button 
            className="new-chat-button"
            onClick={onStartNewChat}
            title="Yeni Sohbet"
          >
            <PlusCircle size={18} /> Yeni
          </button>
          <button 
            className="sidebar-close-button"
            onClick={onToggle}
            title="Kapat"
            aria-label="Sidebar kapat"
          >
            <X size={20} />
          </button>
        </div>
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

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="version-info">
          <small>SUBU Chatbot v2.0</small>
          <small className="creator-info">Created by SUBU BİDB</small>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
