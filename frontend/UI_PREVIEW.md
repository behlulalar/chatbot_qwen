# 🎨 SUBU Mevzuat Chatbot - UI Önizleme

## 🌈 Tasarım Özellikleri

### Renk Paleti

**Ana Renkler:**
- Primary Gradient: `#667eea` → `#764ba2` (Mor-Mavi)
- Secondary Gradient: `#f093fb` → `#f5576c` (Pembe-Kırmızı)
- Background: Gradient overlay
- Text: `#333` (Koyu) / `white` (Açık)

**Durum Renkleri:**
- Success: `#2ecc71` (Yeşil)
- Warning: `#f39c12` (Turuncu)
- Error: `#e74c3c` (Kırmızı)
- Info: `#667eea` (Mavi-Mor)

### Tipografi

- Font Family: `Segoe UI, Tahoma, Geneva, Verdana, sans-serif`
- Header: 24px-32px (Bold)
- Body: 14px-16px (Regular)
- Caption: 11px-13px (Light)

### Bileşenler

#### 1. Header (Üst Bar)
```
┌─────────────────────────────────────────────────┐
│ ☰  📚 SUBU Mevzuat Asistanı                    │
│     Sakarya Uygulamalı Bilimler Üniversitesi   │
└─────────────────────────────────────────────────┘
```
- Gradient background
- Sidebar toggle button
- Başlık ve alt başlık

#### 2. Sidebar (Sol Panel)
```
┌──────────────────┐
│ 📊 Panel         │
├──────────────────┤
│ Sistem Durumu    │
│ ● API: healthy   │
│ ● DB: healthy    │
│ ● Vector: healthy│
├──────────────────┤
│ İstatistikler    │
│ [5] Mesaj        │
│ [$0.01] Maliyet  │
├──────────────────┤
│ Mevzuatlar [+]   │
│ 77 doküman       │
├──────────────────┤
│ 🗑️ Temizle       │
└──────────────────┘
```
- Koyu tema (#2c3e50)
- Collapsible sections
- Real-time stats
- Health indicators

#### 3. Welcome Screen (İlk Ekran)
```
┌───────────────────────────────────┐
│         👋 Hoş Geldiniz!         │
│  Üniversite mevzuatları hakkında │
│      sorular sorabilirsiniz      │
│                                   │
│      Örnek Sorular:              │
│   ┌─────────────────────────┐   │
│   │ 🏆 Akademik personele    │   │
│   │    ödül nasıl verilir?   │   │
│   └─────────────────────────┘   │
│   ┌─────────────────────────┐   │
│   │ ⏰ Lisansüstü azami      │   │
│   │    süreleri nedir?       │   │
│   └─────────────────────────┘   │
│   ┌─────────────────────────┐   │
│   │ 🔬 BAP başvurusu        │   │
│   │    nasıl yapılır?        │   │
│   └─────────────────────────┘   │
└───────────────────────────────────┘
```
- Centered layout
- Clickable example cards
- Hover effects

#### 4. Chat Messages

**User Message:**
```
┌─────────────────────────────┐ 👤
│ Akademik personele ödül     │
│ nasıl verilir?              │
│                     16:45   │
└─────────────────────────────┘
```
- Gradient background (Primary)
- White text
- Right-aligned
- Timestamp

**Assistant Message:**
```
🤖 ┌─────────────────────────────┐
   │ Akademik personele ödül     │
   │ verilmesi...                │
   │                             │
   │ 📚 Kaynaklar (3) ▼          │
   │ ┌─────────────────────────┐ │
   │ │ Akademik Ödül Yönergesi │ │
   │ │ Madde 5: ...            │ │
   │ │ 95% uygun               │ │
   │ └─────────────────────────┘ │
   │                             │
   │ 📊 Detaylar ▼               │
   │                             │
   │                     16:45   │
   └─────────────────────────────┘
```
- White background
- Dark text
- Left-aligned
- Collapsible sources
- Metadata toggle

#### 5. Source Cards
```
┌──────────────────────────────────┐
│ Akademik ve İdari Personel Ödül │
│ Yönergesi              [95% uygun]│
├──────────────────────────────────┤
│ Madde 5: Ödül Verilmesi          │
├──────────────────────────────────┤
│ │ Ödüllendirme yıllık olarak    │
│ │ yapılır ve ...                 │
└──────────────────────────────────┘
```
- Light background (#f8f9fa)
- Border on hover (Primary color)
- Relevance score badge
- Preview text

#### 6. Loading Indicator
```
   ● ● ●  Düşünüyorum...
```
- Animated dots
- Typing animation
- Subtle movement

#### 7. Input Box
```
┌─────────────────────────────────────────┬────┐
│ Sorunuzu yazın...                       │ ➤  │
└─────────────────────────────────────────┴────┘
      Enter ile gönder • Shift+Enter yeni satır
```
- Rounded corners (15px)
- Border focus effect
- Send button with gradient
- Helper text

### Animasyonlar

1. **Message Fade In**
   - Duration: 0.3s
   - Transform: translateY(10px) → translateY(0)
   - Opacity: 0 → 1

2. **Typing Dots**
   - Duration: 1.4s infinite
   - Transform: translateY(0) → translateY(-10px) → translateY(0)

3. **Button Hover**
   - Scale: 1.05
   - Box-shadow: 0 4px 12px rgba(...)

4. **Card Hover**
   - Transform: translateX(5px)
   - Border-color change
   - Box-shadow addition

### Responsive Breakpoints

**Desktop (1600px+):**
- Sidebar: 300px fixed
- Chat: Flex grow
- Max width: 1600px

**Tablet (768px-1600px):**
- Sidebar: Collapsible
- Font sizes: Adjusted
- Padding: Reduced

**Mobile (<768px):**
- Sidebar: Overlay
- Chat: Full width
- Input: Simplified
- Border-radius: 0 (full screen)

### Accessibility

- ✅ Keyboard navigation
- ✅ Focus indicators
- ✅ ARIA labels (future)
- ✅ Color contrast (WCAG AA)
- ✅ Screen reader friendly (future)

### Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🎯 Kullanıcı Deneyimi (UX)

### Akış

1. **Açılış:** Welcome screen + example questions
2. **Soru:** Click example veya type
3. **Loading:** Typing indicator
4. **Cevap:** Smooth fade-in
5. **Kaynaklar:** Collapsible sources
6. **Tekrar:** Input ready

### Feedback

- Hover states on all clickables
- Button disabled states
- Loading indicators
- Error messages (red toast)
- Success confirmations

### Performance

- Lazy loading for images
- Virtual scrolling (future)
- Debounced input (future)
- Optimistic UI updates

## 🛠️ Özelleştirme

### Renk Değiştirme

`App.css`:
```css
/* Ana gradient */
background: linear-gradient(135deg, #YOUR_COLOR_1, #YOUR_COLOR_2);

/* Buton gradient */
.send-button {
  background: linear-gradient(135deg, #YOUR_COLOR_1, #YOUR_COLOR_2);
}
```

### Logo Ekleme

`ChatInterface.tsx`:
```tsx
<div className="header-title">
  <img src="/logo.png" alt="SUBU" className="logo" />
  <div>
    <h1>SUBU Mevzuat Asistanı</h1>
    <p>Sakarya Uygulamalı Bilimler Üniversitesi</p>
  </div>
</div>
```

### Font Değiştirme

`public/index.html`:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
```

`App.css`:
```css
body {
  font-family: 'Inter', sans-serif;
}
```

## 📱 Mobil Optimizasyonu

- Touch-friendly buttons (44px min)
- No hover effects on mobile
- Swipe gestures (future)
- Bottom navigation (future)

## 🎨 Tasarım Sistemi

Proje tutarlı bir tasarım sistemi kullanır:
- Spacing: 4px grid (8, 12, 16, 20, 24px)
- Border-radius: 8, 10, 12, 15px
- Shadows: 0 2px 8px, 0 4px 12px, 0 20px 60px
- Transitions: 0.3s ease

## 💡 Gelecek İyileştirmeler

- [ ] Dark mode toggle
- [ ] Theme customizer
- [ ] Avatar customization
- [ ] Message reactions
- [ ] Chat export (PDF)
- [ ] Voice input
- [ ] Multi-language UI
- [ ] Emoji picker
- [ ] File upload
- [ ] Image responses

---

**Tasarım Prensibi:** Modern, temiz, profesyonel ve kullanıcı dostu.
