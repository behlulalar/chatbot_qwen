import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { MessageCircle, LogOut, LayoutDashboard, Menu, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './AdminLayout.css';

const AdminLayout: React.FC = () => {
  const { logout, username } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/admin', { replace: true });
    setSidebarOpen(false);
  };

  return (
    <div className="admin-layout">
      <aside className={`admin-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="admin-sidebar-header">
          <h2>Admin Paneli</h2>
          <button type="button" className="admin-sidebar-close" onClick={() => setSidebarOpen(false)} aria-label="Menüyü kapat">
            <X size={20} />
          </button>
        </div>
        <nav className="admin-nav">
          <NavLink
            to="/admin"
            end
            className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
          >
            <LayoutDashboard size={18} /> Ana Sayfa
          </NavLink>
          <NavLink
            to="/admin/feedback"
            className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
          >
            <MessageCircle size={18} /> Geri Bildirimler
          </NavLink>
        </nav>
        <div className="admin-sidebar-footer">
          <div className="admin-user">{username || 'Admin'}</div>
          <button type="button" className="admin-logout" onClick={handleLogout}>
            <LogOut size={18} /> Çıkış
          </button>
        </div>
      </aside>
      {sidebarOpen && <div className="admin-sidebar-overlay" onClick={() => setSidebarOpen(false)} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Escape' && setSidebarOpen(false)} aria-label="Menüyü kapat" />}
      <main className="admin-main">
        <button type="button" className="admin-menu-toggle" onClick={() => setSidebarOpen(true)} aria-label="Menüyü aç">
          <Menu size={24} />
        </button>
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
