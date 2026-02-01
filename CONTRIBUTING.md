# Katkıda Bulunma Rehberi

SUBU Mevzuat Chatbot projesine katkıda bulunmak istediğiniz için teşekkürler! 🎉

## 🚀 Başlamadan Önce

1. Projeyi fork edin
2. Local'inize klonlayın
3. Development branch oluşturun
4. Değişikliklerinizi yapın
5. Test edin
6. Pull request gönderin

## 📝 Kod Standartları

### Python (Backend)

- **Style Guide**: PEP 8
- **Type Hints**: Kullanın
- **Docstrings**: Google style
- **Linting**: Black formatter

```bash
# Format kodu
black app/

# Type check
mypy app/

# Tests
pytest
```

### TypeScript/React (Frontend)

- **Style Guide**: Airbnb React/JSX
- **Components**: Functional components + hooks
- **TypeScript**: Strict mode
- **Naming**: PascalCase for components, camelCase for functions

```bash
# Lint
npm run lint

# Format
npm run format

# Build test
npm run build
```

## 🧪 Test Yazma

### Backend
```python
# tests/test_myfeature.py
def test_my_feature():
    """Test that my feature works."""
    result = my_feature("input")
    assert result == "expected"
```

### Frontend
```typescript
// MyComponent.test.tsx
import { render, screen } from '@testing-library/react';

test('renders component', () => {
  render(<MyComponent />);
  expect(screen.getByText('Hello')).toBeInTheDocument();
});
```

## 📋 Commit Mesajları

Conventional Commits kullanın:

```
feat: Yeni özellik ekle
fix: Bug düzelt
docs: Dokümantasyon güncelle
style: Kod formatı (logic değişmez)
refactor: Kod yeniden yapılandırma
test: Test ekle/düzelt
chore: Build/config değişiklikleri
```

**Örnekler:**
```
feat: Add chat history export feature
fix: Fix Turkish character normalization in search
docs: Update deployment guide for Ubuntu 22.04
test: Add unit tests for response generator
```

## 🔀 Pull Request Süreci

1. **Branch oluştur**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Değişiklikleri commit et**
   ```bash
   git add .
   git commit -m "feat: Add my feature"
   ```

3. **Push et**
   ```bash
   git push origin feature/my-feature
   ```

4. **PR aç** (GitHub'da)
   - Açıklayıcı başlık
   - Ne değiştirdiğinizi açıklayın
   - Screenshots (UI değişiklikleri için)
   - Issue numarası (varsa)

5. **Code review** bekle

6. **Değişiklik isterlerse** uygula

7. **Merge** edilmesini bekle

## 🐛 Bug Bildirimi

GitHub Issues kullanın:

**Template:**
```markdown
## Bug Açıklaması
[Açık ve net açıklama]

## Reproduce Adımları
1. '...' adımını uygula
2. '...' tıkla
3. '...' aşağı kaydır
4. Hatayı gör

## Beklenen Davranış
[Ne olmasını bekliyordunuz]

## Screenshots
[Varsa ekleyin]

## Ortam
- OS: [örn. Ubuntu 22.04]
- Browser: [örn. Chrome 120]
- Python version: [örn. 3.11]
- Node version: [örn. 18.x]

## Ek Bilgi
[Başka bir şey]
```

## ✨ Feature Request

**Template:**
```markdown
## Özellik Açıklaması
[Net açıklama]

## Motivasyon
[Neden gerekli]

## Önerilen Çözüm
[Nasıl yapılabilir]

## Alternatifler
[Düşündüğünüz diğer yollar]

## Ek Bilgi
[Screenshots, mockups, vb.]
```

## 🏗️ Proje Yapısı

```
backend/
├── app/
│   ├── api/          # API endpoints
│   ├── llm/          # LLM integration
│   ├── rag/          # RAG pipeline
│   ├── scraper/      # Web scraping
│   └── ...
└── tests/            # Unit tests

frontend/
├── src/
│   ├── components/   # React components
│   └── utils/        # Utilities
└── public/           # Static files
```

## 📚 Öğrenme Kaynakları

### RAG & LLM
- [LangChain Docs](https://python.langchain.com/)
- [OpenAI Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)

### FastAPI
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### React
- [React Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## 🤝 İletişim

- GitHub Issues: Teknik konular
- Pull Requests: Kod değişiklikleri
- Discussions: Genel tartışmalar

## ⚖️ Lisans

Bu projeye katkıda bulunarak, katkılarınızın MIT lisansı altında lisanslanacağını kabul etmiş olursunuz.

---

**Teşekkürler!** ❤️
