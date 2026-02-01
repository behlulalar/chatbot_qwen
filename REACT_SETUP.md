# ⚛️ React Frontend Kurulum ve Çalıştırma

## 🎯 Hızlı Başlangıç

### 1. İlk Kurulum

```bash
cd frontend

# Dependencies yükle
npm install

# Environment dosyası oluştur
cp .env.example .env.development

# Geliştirme sunucusunu başlat
npm start
```

✅ Tarayıcı otomatik açılacak: http://localhost:3000

### 2. Backend'i Başlat

Başka bir terminal:

```bash
cd backend
source venv/bin/activate
python run_server.py
```

✅ Backend API: http://localhost:8000

---

## 📦 npm Komutları

```bash
# Geliştirme sunucusu (hot reload)
npm start

# Production build oluştur
npm run build

# Production build'i test et
npm run serve

# Test çalıştır
npm test

# Docker image oluştur
npm run docker:build

# Docker container çalıştır
npm run docker:run
```

---

## 🔧 Sorun Giderme

### npm install hatası

```bash
# Node versiyonunu kontrol et (18+ gerekli)
node --version

# node_modules temizle
rm -rf node_modules package-lock.json

# Tekrar yükle
npm install
```

### Port 3000 kullanımda

```bash
# Farklı port kullan
PORT=3001 npm start

# veya .env dosyasına ekle:
PORT=3001
```

### Backend'e bağlanamıyor

```bash
# .env.development dosyasını kontrol et
cat .env.development

# Backend'in çalıştığını doğrula
curl http://localhost:8000/health

# CORS hatası varsa backend'in CORS ayarlarını kontrol et
```

### TypeScript hatası

```bash
# Type kontrollerini geçici devre dışı bırak
SKIP_PREFLIGHT_CHECK=true npm start

# Tam hata detayını gör
npm start --verbose
```

### Build hatası

```bash
# Cache temizle
rm -rf node_modules/.cache

# Tekrar build et
npm run build
```

---

## 🚀 Production Deployment

### Option 1: Static Build + Nginx

```bash
# Build oluştur
npm run build

# Build klasörünü sunucuya kopyala
scp -r build/* user@server:/var/www/html/

# Nginx config
server {
    listen 80;
    root /var/www/html;
    
    location / {
        try_files $uri /index.html;
    }
}
```

### Option 2: Docker

```bash
# Dockerfile zaten hazır
docker build -t subu-frontend .
docker run -p 80:80 subu-frontend
```

### Option 3: Docker Compose

```bash
# docker-compose.yml zaten hazır
docker-compose up -d frontend
```

---

## 🎨 Özelleştirme

### API URL Değiştirme

`.env.development`:
```env
REACT_APP_API_URL=http://localhost:8000
```

`.env.production`:
```env
REACT_APP_API_URL=https://your-server.com
```

### Renk Teması

`src/App.css`:
```css
background: linear-gradient(135deg, #YOUR_COLOR_1, #YOUR_COLOR_2);
```

### Logo Ekleme

1. Logo dosyasını `public/` klasörüne koy
2. `src/components/ChatInterface.tsx`:
```tsx
<img src="/logo.png" alt="SUBU" style={{width: '40px'}} />
```

---

## 📊 Performans

### Bundle Size

```bash
# Build sonrası analiz
npm run build
npm install -g source-map-explorer
source-map-explorer 'build/static/js/*.js'
```

### Lighthouse Score

1. Production build oluştur: `npm run build`
2. Serve et: `npm run serve`
3. Chrome DevTools → Lighthouse → Run

Hedef:
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+

---

## 🧪 Test

```bash
# Unit tests
npm test

# Coverage raporu
npm test -- --coverage

# E2E tests (gelecek)
# npm run test:e2e
```

---

## 📱 Responsive Test

### Browser DevTools

1. F12 → Toggle device toolbar
2. Test boyutları:
   - Mobile: 375x667 (iPhone SE)
   - Tablet: 768x1024 (iPad)
   - Desktop: 1920x1080

### Gerçek Cihazlar

```bash
# Local network'te aç
npm start

# Mobil cihazdan eriş:
# http://YOUR_LOCAL_IP:3000
```

---

## 🔒 Güvenlik

### Environment Variables

```bash
# .env dosyalarını .gitignore'a ekle
echo ".env*" >> .gitignore

# API keys asla commit etme!
```

### Content Security Policy

`public/index.html`:
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               connect-src 'self' http://localhost:8000">
```

---

## 🐛 Debug

### React DevTools

1. Chrome Extension yükle: [React DevTools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
2. F12 → Components/Profiler tabs

### Console Logging

```tsx
// Component içinde
console.log('State:', messages);
console.log('API Response:', response.data);
```

### Network Monitoring

1. F12 → Network tab
2. XHR filter
3. API calls'ları incele

---

## 💡 Geliştirme İpuçları

### Hot Reload

- Kod değişiklikleri otomatik yansır
- State korunur (çoğu durumda)
- `Ctrl+R` ile manuel refresh

### Component Structure

```
src/
├── components/
│   ├── ChatInterface.tsx    # Main container
│   ├── ChatMessage.tsx       # Message component
│   └── Sidebar.tsx           # Side panel
├── types/                    # TypeScript types (future)
├── utils/                    # Helper functions (future)
└── hooks/                    # Custom hooks (future)
```

### State Management

- Şu anda: React useState
- Gelecek: Redux/Zustand (büyük projeler için)

### API Calls

```tsx
// Axios kullan
import axios from 'axios';

const response = await axios.post(`${API_URL}/api/chat/`, {
  question: 'test'
});
```

---

## 📚 Kaynaklar

- [React Docs](https://react.dev)
- [TypeScript Docs](https://www.typescriptlang.org/docs/)
- [Create React App Docs](https://create-react-app.dev/)
- [Axios Docs](https://axios-http.com/docs/intro)

---

## 🎓 Öğrenme Yolu

1. ✅ React basics (components, props, state)
2. ✅ TypeScript fundamentals
3. ✅ Hooks (useState, useEffect, useRef)
4. ✅ API integration (axios)
5. ✅ CSS styling
6. ⏳ Context API (state management)
7. ⏳ Custom hooks
8. ⏳ Performance optimization

---

## ✅ Checklist

Deployment öncesi kontrol listesi:

- [ ] `npm run build` başarılı
- [ ] Tüm env variables set
- [ ] API URL production'a ayarlı
- [ ] Console error'ları temiz
- [ ] Mobile responsive test edildi
- [ ] Cross-browser test edildi
- [ ] Performance test edildi
- [ ] Security headers eklendi

---

**Sorularınız mı var?** [DEVELOPMENT.md](DEVELOPMENT.md) dosyasına bakın!
