# 🎨 Frontend - React UI

Modern React + TypeScript web arayüzü.

## 🚀 Başlangıç

```bash
# Dependencies
npm install

# Development
npm start
# → http://localhost:3000

# Production Build
npm run build
```

## ⚙️ Konfigürasyon

`.env.development`:
```env
REACT_APP_API_URL=http://localhost:8000
```

`.env.production`:
```env
REACT_APP_API_URL=https://your-server.com
```

## 📁 Yapı

```
src/
├── components/
│   ├── ChatInterface.tsx    # Ana chat
│   ├── ChatMessage.tsx      # Mesaj komponenti
│   ├── Sidebar.tsx          # Yan panel
│   └── ErrorBoundary.tsx    # Hata yakalama
├── utils/
│   └── sessionStorage.ts    # Session yönetimi
└── App.tsx                  # Root
```

## ✨ Özellikler

- ⚛️ React 18 + TypeScript
- 💬 Real-time chat
- 📚 Source citations
- 📊 Statistics
- 📱 Responsive
- 🎨 Modern UI

## 🐛 Sorun Giderme

```bash
# Backend kontrolü
curl http://localhost:8000/health

# Cache temizle
rm -rf node_modules
npm install
```

## 🚀 Deployment

Docker ile (önerilen):
```bash
docker-compose up -d
```

Manuel:
```bash
npm run build
npx serve -s build
```
