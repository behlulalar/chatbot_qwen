import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowLeft, ThumbsUp, ThumbsDown, MessageCircle } from 'lucide-react';
import { NEGATIVE_REASONS } from './FeedbackModal';
import { useAuth } from '../context/AuthContext';
import './FeedbackPanel.css';

const API_BASE_URL = (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim() !== '') ? process.env.REACT_APP_API_URL : (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000');

interface FeedbackItem {
  id: number;
  question: string;
  answer: string;
  rating: string;
  reason: string | null;
  comment: string | null;
  created_at: string;
}

interface FeedbackPanelProps {
  onBack?: () => void;
}

const FeedbackPanel: React.FC<FeedbackPanelProps> = ({ onBack }) => {
  const { token } = useAuth();
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [ratingFilter, setRatingFilter] = useState<'all' | 'positive' | 'negative'>('all');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<FeedbackItem | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchList = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { limit: 50 };
      if (ratingFilter !== 'all') params.rating = ratingFilter;
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get(`${API_BASE_URL}/api/feedback/`, { params, headers });
      setItems(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Geri bildirimler yüklenemedi:', err);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [ratingFilter, token]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  const openDetail = async (id: number) => {
    setSelectedId(id);
    setDetail(null);
    setDetailLoading(true);
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get(`${API_BASE_URL}/api/feedback/${id}`, { headers });
      setDetail(res.data);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setSelectedId(null);
    setDetail(null);
  };

  const getReasonLabel = (reasonId: string | null) => {
    if (!reasonId) return '-';
    const found = NEGATIVE_REASONS.find((r) => r.id === reasonId);
    return found ? found.label : reasonId;
  };

  const formatDate = (iso: string) => {
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleString('tr-TR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTitle = (item: FeedbackItem) => {
    const q = item.question || '';
    return q.length > 80 ? q.slice(0, 80) + '...' : q || 'Başlık yok';
  };

  return (
    <div className="feedback-panel">
      <div className="feedback-panel-header">
        {onBack && (
          <button type="button" className="back-btn" onClick={onBack}>
            <ArrowLeft size={20} /> Sohbete Dön
          </button>
        )}
        <h1>Geri Bildirimler</h1>
        <p className="feedback-panel-subtitle">
          Kullanıcı geri bildirimlerini inceleyin, soru ve cevapları detaylı görüntüleyin. Toplam: {total} geri bildirim
        </p>
      </div>

      <div className="feedback-filters">
        <button
          type="button"
          className={ratingFilter === 'all' ? 'active' : ''}
          onClick={() => setRatingFilter('all')}
        >
          Tümü
        </button>
        <button
          type="button"
          className={ratingFilter === 'positive' ? 'active' : ''}
          onClick={() => setRatingFilter('positive')}
        >
          <ThumbsUp size={14} /> Olumlu
        </button>
        <button
          type="button"
          className={ratingFilter === 'negative' ? 'active' : ''}
          onClick={() => setRatingFilter('negative')}
        >
          <ThumbsDown size={14} /> Olumsuz
        </button>
      </div>

      <div className="feedback-panel-content">
        <div className="feedback-list">
          {loading ? (
            <p className="feedback-loading">Yükleniyor...</p>
          ) : items.length === 0 ? (
            <p className="feedback-empty">Henüz geri bildirim yok.</p>
          ) : (
            <ul className="feedback-items">
              {items.map((item) => (
                <li key={item.id} className="feedback-item">
                  <div className="feedback-item-header">
                    <span className={`feedback-badge ${item.rating}`}>
                      {item.rating === 'positive' ? (
                        <ThumbsUp size={12} />
                      ) : (
                        <ThumbsDown size={12} />
                      )}
                      {item.rating === 'positive' ? 'Olumlu' : 'Olumsuz'}
                    </span>
                    <span className="feedback-date">{formatDate(item.created_at)}</span>
                  </div>
                  <div className="feedback-item-title" title={item.question}>
                    {getTitle(item)}
                  </div>
                  {item.reason && (
                    <div className="feedback-item-reason">
                      Sebep: {getReasonLabel(item.reason)}
                    </div>
                  )}
                  <button
                    type="button"
                    className="feedback-detail-btn"
                    onClick={() => openDetail(item.id)}
                  >
                    Detaylar
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {selectedId && (
          <div className="feedback-detail-panel">
            <div className="feedback-detail-header">
              <h3>Detay</h3>
              <button type="button" className="close-detail-btn" onClick={closeDetail}>
                ×
              </button>
            </div>
            {detailLoading ? (
              <p className="feedback-loading">Yükleniyor...</p>
            ) : detail ? (
              <div className="feedback-detail-body">
                <div className="detail-section">
                  <h4>
                    <MessageCircle size={16} /> Kullanıcı sorusu
                  </h4>
                  <div className="detail-question">{detail.question}</div>
                </div>
                <div className="detail-section">
                  <h4>Bot cevabı</h4>
                  <div className="detail-answer">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{detail.answer}</ReactMarkdown>
                  </div>
                </div>
                <div className="detail-meta">
                  <div className="detail-meta-row">
                    <span className="label">Tarih:</span>
                    <span>{formatDate(detail.created_at)}</span>
                  </div>
                  <div className="detail-meta-row">
                    <span className="label">Puan:</span>
                    <span className={detail.rating}>{detail.rating === 'positive' ? 'Olumlu' : 'Olumsuz'}</span>
                  </div>
                  {detail.reason && (
                    <div className="detail-meta-row">
                      <span className="label">Sebep:</span>
                      <span>{getReasonLabel(detail.reason)}</span>
                    </div>
                  )}
                  {detail.comment && (
                    <div className="detail-meta-row">
                      <span className="label">Yorum:</span>
                      <span>{detail.comment}</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="feedback-error">Detay yüklenemedi.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FeedbackPanel;
