import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoginPage from './LoginPage';
import AdminLayout from './AdminLayout';
import AdminDashboard from './AdminDashboard';
import AdminFeedback from './AdminFeedback';
import AdminDocuments from './AdminDocuments';

const AdminPage: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <Routes>
      <Route element={<AdminLayout />}>
        <Route index element={<AdminDashboard />} />
        <Route path="feedback" element={<AdminFeedback />} />
        <Route path="documents" element={<AdminDocuments />} />
        <Route path="dashboard" element={<AdminDashboard />} />
      </Route>
    </Routes>
  );
};

export default AdminPage;
