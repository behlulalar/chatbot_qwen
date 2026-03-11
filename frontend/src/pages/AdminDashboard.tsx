import React from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, FileText } from 'lucide-react';
import './AdminDashboard.css';

const AdminDashboard: React.FC = () => {
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
