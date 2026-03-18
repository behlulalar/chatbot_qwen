import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, FileText } from 'lucide-react';
import axios from 'axios';
import './AdminDashboard.css';

const API_BASE_URL =
  process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim() !== ''
    ? process.env.REACT_APP_API_URL
    : process.env.NODE_ENV === 'production'
      ? ''
      : 'http://localhost:8000';

const AdminDashboard: React.FC = () => {
  const [totalDocuments, setTotalDocuments] = useState<number | null>(null);
  const [activeDocuments, setActiveDocuments] = useState<number | null>(null);

  useEffect(() => {
    const fetchDocCount = async () => {
      try {
        const [totalRes, activeRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/api/documents/?limit=1`),
          axios.get(`${API_BASE_URL}/api/documents/?status=processed&limit=1`),
        ]);
        setTotalDocuments(typeof totalRes.data?.total === 'number' ? totalRes.data.total : null);
        setActiveDocuments(typeof activeRes.data?.total === 'number' ? activeRes.data.total : null);
      } catch {
        setTotalDocuments(null);
        setActiveDocuments(null);
      }
    };
    fetchDocCount();
  }, []);

  return (
    <div className="admin-dashboard">
      <div className="admin-dashboard-header">
        <h1>Ana Sayfa</h1>
        <p>Yönetim işlemlerini aşağıdan veya sol menüden seçebilirsiniz.</p>
      </div>
      <div className="admin-dashboard-cards">
        <Link to="/admin/feedback" className="admin-card">
          <div className="admin-card-icon feedback">
            <MessageCircle size={26} />
          </div>
          <h3>Geri Bildirimler</h3>
          <p>Kullanıcıların bıraktığı geri bildirimleri inceleyin, soru ve cevapları detaylı görüntüleyin.</p>
        </Link>
        <Link to="/admin/documents" className="admin-card admin-card-doc">
          <div className="admin-card-icon doc">
            <FileText size={26} />
          </div>
          {typeof activeDocuments === 'number' && (
            <div className="admin-card-badge" title="Aktif doküman sayısı">
              {activeDocuments}
            </div>
          )}
          <h3>Aktif Dokümanlar</h3>
          <p>Yüklenmiş PDF mevzuat listesini görüntüleyin ve takip edin.</p>
        </Link>
        <div className="admin-card disabled">
          <div className="admin-card-icon doc">
            <FileText size={26} />
          </div>
          <h3>Doküman Yönetimi</h3>
          <p>Yakında: Manuel doküman ekleme ve vektör veritabanını yeniden oluşturma.</p>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
