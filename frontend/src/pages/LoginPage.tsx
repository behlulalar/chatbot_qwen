import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

const API_BASE_URL = (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim() !== '') ? process.env.REACT_APP_API_URL : (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000');

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/admin/auth/login`, {
        username,
        password,
      });
      login(res.data.access_token, res.data.username);
      navigate('/admin', { replace: true });
    } catch (err: unknown) {
      const msg = axios.isAxiosError(err) && err.response?.data?.detail
        ? (typeof err.response.data.detail === 'string' ? err.response.data.detail : 'Giriş başarısız')
        : 'Giriş yapılamadı. Bağlantıyı kontrol edin.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-icon"><Lock size={32} /></div>
          <h1>Admin Paneli</h1>
          <p>Devam etmek için giriş yapın</p>
        </div>
        <form onSubmit={handleSubmit} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSubmit(e as unknown as React.FormEvent); } }} className="login-form">
          {error && <div className="login-error">{error}</div>}
          <div className="login-field">
            <label htmlFor="username">Kullanıcı adı</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              autoComplete="username"
              required
            />
          </div>
          <div className="login-field">
            <label htmlFor="password">Şifre</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </div>
          <button type="submit" className="login-submit" disabled={loading}>
            {loading ? 'Giriş yapılıyor...' : 'Giriş'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
