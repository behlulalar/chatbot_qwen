# Sunucuda Node.js 18 kurulumu (Ubuntu)

Frontend build için **Node 14+** (tercihen **18 LTS**) gerekir. Sunucuda Node 12 varsa aşağıyı uygula.

## Tek seferlik kurulum

Sunucuda (behlulalar@10.80.0.175) çalıştır:

```bash
# NodeSource ile Node 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Kontrol
node -v   # v18.x.x olmalı
npm -v
```

Sonra projede:

```bash
cd ~/behlul/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
npx serve -s build -l 3000
```

Tarayıcıdan: http://10.80.0.175:3000

---

**Alternatif (nvm ile):**

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
node -v
```
