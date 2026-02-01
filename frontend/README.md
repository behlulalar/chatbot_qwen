# 🎨 SUBU Mevzuat Chatbot - Frontend

Modern, özelleştirilmiş React + TypeScript web arayüzü.

## ✨ Özellikler

- ⚛️ **React 18** + TypeScript
- 🎨 **Custom Modern UI** - Gradient design
- 💬 **Real-time Chat** - Smooth messaging
- 📚 **Source Display** - Collapsible source cards
- 📊 **Statistics Panel** - Cost tracking & metrics
- 🔄 **Live System Status** - Health monitoring
- 📱 **Responsive** - Mobile friendly
- 🚀 **Production Ready** - Docker + Nginx

## 🚀 Hızlı Başlangıç

### Geliştirme Modu

```bash
# Dependencies yükle
npm install

# Geliştirme sunucusunu başlat
npm start
```

✅ UI: http://localhost:3000

### Production Build

```bash
# Build oluştur
npm run build

# Build'i serve et
npx serve -s build
```

### Docker ile Çalıştırma

```bash
# Build image
docker build -t subu-frontend .

# Run container
docker run -p 80:80 subu-frontend
```

## 📁 Proje Yapısı

```
src/
├── components/
│   ├── ChatInterface.tsx       # Ana chat container
│   ├── ChatInterface.css       # Chat styling
│   ├── ChatMessage.tsx         # Message component
│   ├── ChatMessage.css         # Message styling
│   ├── Sidebar.tsx             # Side panel
│   └── Sidebar.css             # Sidebar styling
├── App.tsx                     # Root component
└── App.css                     # Global styles
```

## ⚙️ Konfigürasyon

### Environment Variables

`.env.development`:
```env
REACT_APP_API_URL=http://localhost:8000
```

`.env.production`:
```env
REACT_APP_API_URL=https://your-server.com
```

## 🎨 UI Özellikleri

### Ana Ekran
- Gradient arka plan
- Hoş geldin mesajı
- Örnek sorular (tıklanabilir)

### Chat Arayüzü
- User/Assistant message bubbles
- Avatar'lar
- Zaman damgaları
- Typing indicator

### Kaynak Gösterimi
- Collapsible source cards
- Relevance scores
- Article numbers
- Preview text

### Sidebar
- Sistem durumu (API, DB, Vector Store)
- İstatistikler (mesaj sayısı, maliyet)
- Doküman listesi
- Sohbet temizleme

## 📊 API Entegrasyonu

### Chat Endpoint

```typescript
POST /api/chat/
{
  "question": "string",
  "include_sources": true
}
```

Response:
```typescript
{
  "answer": "string",
  "sources": [
    {
      "title": "string",
      "article_number": "string",
      "relevance_score": number,
      "preview": "string"
    }
  ],
  "metadata": {
    "tokens": number,
    "cost": number,
    "response_time": number,
    "model": "string"
  }
}
```

## 🎯 Özelleştirme

### Renk Değiştirme

`App.css`:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Logo Ekleme

`ChatInterface.tsx`:
```tsx
<img src="/logo.png" alt="SUBU Logo" />
```

## 🐛 Sorun Giderme

### API bağlanamıyor

```bash
# .env dosyasını kontrol et
cat .env.development

# Backend'in çalıştığını kontrol et
curl http://localhost:8000/health
```

### Build hatası

```bash
# Cache temizle
rm -rf node_modules package-lock.json
npm install
```

## 📱 Responsive Design

- Desktop: 1600px+ (Full sidebar)
- Tablet: 768px-1600px (Collapsible sidebar)
- Mobile: <768px (Overlay sidebar)

## 🚀 Deployment

### Windows Server (IIS)

1. Build oluştur: `npm run build`
2. `build/` klasörünü sunucuya kopyala
3. IIS'te static site olarak configure et

### Docker

```bash
docker-compose up -d
```

### Nginx

```bash
# Build'i nginx root'a kopyala
cp -r build/* /var/www/html/

# Nginx'i restart et
sudo systemctl restart nginx
```

## 💡 Geliştirme İpuçları

- **Hot Reload**: `npm start` ile otomatik yenileme
- **TypeScript**: Type safety için
- **React DevTools**: Browser extension kullan
- **Console**: `F12` ile debug

## 🎓 Teknoloji Stack

- React 18.2
- TypeScript 4.9
- Axios (HTTP client)
- React Markdown (Message formatting)
- CSS3 (Custom styling)
- Nginx (Production serving)

## 📝 Lisans

SUBU Mevzuat Chatbot - Eğitim amaçlı proje
