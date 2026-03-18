import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FileText } from 'lucide-react';
import './AdminDocuments.css';

const API_BASE_URL =
  process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim() !== ''
    ? process.env.REACT_APP_API_URL
    : process.env.NODE_ENV === 'production'
      ? ''
      : 'http://localhost:8000';

interface DocumentItem {
  id: number;
  title: string;
  status: string;
  page_count: number | null;
  article_count: number | null;
  processed_at: string | null;
}

const AdminDocuments: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(`${API_BASE_URL}/api/documents/`, {
          params: { status: 'processed', limit: 500 },
        });
        setDocuments(res.data.documents || []);
        setTotal(typeof res.data.total === 'number' ? res.data.total : 0);
      } catch (err) {
        console.error('Doküman listesi yüklenemedi:', err);
        setError('Doküman listesi yüklenirken bir hata oluştu.');
        setDocuments([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    };
    fetchDocuments();
  }, []);

  const formatDate = (iso: string | null) => {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  const statusLabel: Record<string, string> = {
    processed: 'İşlendi',
    downloaded: 'İndirildi',
    processing: 'İşleniyor',
    failed: 'Hata',
    archived: 'Arşiv',
  };

  return (
    <div className="admin-documents">
      <div className="admin-documents-header">
        <h1>
          <FileText size={24} />
          Aktif Dokümanlar
        </h1>
        <p>Yüklenmiş ve işlenmiş PDF mevzuat listesi. Takip için bu sayfayı kullanabilirsiniz.</p>
      </div>

      {loading && (
        <div className="admin-documents-loading">
          <span className="admin-documents-spinner" aria-hidden />
          Liste yükleniyor…
        </div>
      )}

      {error && (
        <div className="admin-documents-error" role="alert">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="admin-documents-summary">
          Toplam <strong>{total}</strong> aktif doküman
        </div>
      )}

      {!loading && !error && documents.length === 0 && total === 0 && (
        <div className="admin-documents-empty">
          Henüz işlenmiş doküman bulunmuyor.
        </div>
      )}

      {!loading && !error && (documents.length > 0 || total > 0) && (
        <div className="admin-documents-table-wrap">
          <table className="admin-documents-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Başlık</th>
                <th>Durum</th>
                <th>Sayfa</th>
                <th>Madde</th>
                <th>İşlenme Tarihi</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="admin-documents-empty-cell">
                    Veritabanında kayıt yok; toplam sayı yedek kaynaktan alındı.
                  </td>
                </tr>
              ) : (
                documents.map((doc, index) => (
                  <tr key={doc.id}>
                    <td>{index + 1}</td>
                    <td className="admin-documents-title" title={doc.title}>
                      {doc.title}
                    </td>
                    <td>
                      <span className={`admin-documents-status admin-documents-status-${doc.status}`}>
                        {statusLabel[doc.status] || doc.status}
                      </span>
                    </td>
                    <td>{doc.page_count != null ? doc.page_count : '—'}</td>
                    <td>{doc.article_count != null ? doc.article_count : '—'}</td>
                    <td>{formatDate(doc.processed_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {!loading && total > documents.length && documents.length > 0 && (
        <div className="admin-documents-note">
          Tabloda ilk {documents.length} kayıt gösteriliyor (toplam {total}).
        </div>
      )}
    </div>
  );
};

export default AdminDocuments;
