# 🤖 AutoBlog AI — Full Autopilot Tech Blog System

Posts a new SEO-optimized tech blog to Dev.to every day automatically.
Learns from performance and improves itself daily. 100% Free.

---

## ✅ What This System Does Every Day

1. 🔍 Finds viral topics (Hacker News + Google Trends + Dev.to)
2. 🧠 AI picks the best topic (avoids repeats, uses past lessons)
3. ✍️  Writes full blog with Google SEO + AI SEO + FAQ section
4. 🧑 Humanizes content (removes AI tone)
5. 🖼️  Generates a cover image with Gemini AI
6. 🚀 Auto-posts to Dev.to
7. 📊 Tracks views, likes, earnings estimate
8. 🎓 Learns pros/cons and improves next day's post

---

## 📁 Files

```
autoblog/
├── .github/workflows/
│   └── daily_post.yml   ← runs daily on GitHub cloud
├── main.py              ← full pipeline
├── memory.json          ← stores history & lessons
├── requirements.txt     ← Python libraries
└── README.md
```

---

## 🚀 Setup Guide (One Time Only)

### 1️⃣ Get Your API Keys

**Gemini API Key (Free)**
- Go to: aistudio.google.com
- Sign in with Google
- Click "Get API Key" → "Create API Key"
- Copy it ✅

**Dev.to API Key (Free)**
- Go to: dev.to → Sign up
- Settings → Extensions
- Under "DEV Community API Keys" → Generate API Key
- Copy it ✅

---

### 2️⃣ Create GitHub Repository
- Go to github.com → Sign up free
- Click "+" → "New repository"
- Name: `autoblog`
- Set to Private
- Click "Create repository"

---

### 3️⃣ Upload These 5 Files
Upload all files to your repo:
- `main.py`
- `requirements.txt`
- `memory.json`
- `README.md`
- `.github/workflows/daily_post.yml`

---

### 4️⃣ Add API Keys as GitHub Secrets
- Repo → Settings → Secrets and variables → Actions
- Click "New repository secret" — add these 2:

| Secret Name | Value |
|---|---|
| `GEMINI_API_KEY` | your Gemini key |
| `DEVTO_API_KEY` | your Dev.to key |

---

### 5️⃣ Add Your Affiliate Links (optional but recommended 💰)
Open `main.py` and find this section near the top:

```python
AFFILIATE_LINKS = {
    "amazon":    "https://amzn.to/YOUR_AFFILIATE_ID",
    "hostinger": "https://www.hostinger.com/?ref=YOUR_ID",
    "coursera":  "https://www.coursera.org/?ref=YOUR_ID",
    "udemy":     "https://www.udemy.com/?ref=YOUR_ID",
    "nordvpn":   "https://nordvpn.com/?ref=YOUR_ID",
}
```

Replace with your own affiliate links.

---

### 6️⃣ Enable GitHub Actions
- Click "Actions" tab in your repo
- Click "Enable workflows"

---

### 7️⃣ Test It Now (Manual Run)
- Actions tab → "AutoBlog Daily Post"
- Click "Run workflow" → "Run workflow"
- Watch it run! Takes about 2-3 minutes ✅

---

## ⏰ Schedule
Runs automatically every day at 9:00 AM UTC.

---

## 💰 How to Earn Money

| Method | How | When |
|---|---|---|
| Affiliate links | Auto-added in posts | From day 1 |
| Dev.to Listings | Apply at dev.to/listings | After 100 followers |
| Google AdSense | Apply at adsense.google.com | After 20+ posts |
| Sponsored posts | Brands contact you | After 500+ followers |

---

## 💰 Cost Breakdown

| Service | Cost |
|---|---|
| GitHub Actions | ✅ Free |
| Gemini API | ✅ Free (500 images/day) |
| Dev.to | ✅ Free |
| Hacker News API | ✅ Free |
| Google Trends | ✅ Free |
| **Total** | **$0/month** |

---

## 📊 Tracking Performance
Every post's views, likes, and comments are saved in `memory.json`.
The AI reads this file daily and improves the next post automatically.

---

## ❓ Problems?
Check the Actions tab — it shows exactly what happened step by step.
