# 🤖 AutoBlog AI — Self-Evolving Tech Blog System

A fully autonomous tech blog that posts every day, learns from performance,
and gets smarter automatically. No human input needed after setup.

---

## 🧠 How It Evolves Daily

```
9:00 AM  → Posts today's blog (uses yesterday's lessons)
6:00 PM  → Analyzes performance, updates brain.json
9:00 AM  → Posts smarter blog (uses today's lessons)
          → Repeats forever, getting better every day 📈
```

---

## 📁 File Structure

```
autoblog/
├── .github/workflows/
│   ├── daily_post.yml    ← 9AM: finds topic, writes & posts blog
│   └── daily_learn.yml   ← 6PM: analyzes performance, evolves brain
├── main.py               ← daily posting pipeline
├── learner.py            ← self-improvement engine
├── competitor.py         ← watches rival blogs for gaps
├── brain.json            ← AI memory (grows smarter daily)
├── memory.json           ← all post history & stats
├── requirements.txt
└── README.md
```

---

## 🚀 Setup Guide

### 1️⃣ Get API Keys (Both Free)

**Gemini API Key**
- Go to: aistudio.google.com
- Sign in with Google account
- Click "Get API Key" → "Create API Key"
- Copy it ✅

**Dev.to API Key**
- Go to: dev.to → Sign up free
- Settings → Extensions
- Generate API Key → Copy it ✅

---

### 2️⃣ Create GitHub Repository
- Go to github.com
- Click "+" → "New repository"
- Name: `autoblog`
- Set to Private
- Click "Create repository"

---

### 3️⃣ Upload All 9 Files
Upload these files to your repo:
```
main.py
learner.py
competitor.py
brain.json
memory.json
requirements.txt
README.md
.github/workflows/daily_post.yml
.github/workflows/daily_learn.yml
```

For the workflow files, create them as:
`.github/workflows/daily_post.yml`
`.github/workflows/daily_learn.yml`

---

### 4️⃣ Add API Keys as Secrets
Repo → Settings → Secrets and variables → Actions → New repository secret

| Secret Name | Value |
|---|---|
| `GEMINI_API_KEY` | your Gemini key |
| `DEVTO_API_KEY` | your Dev.to key |

---

### 5️⃣ Add Your Affiliate Links (💰 Earn Money)
Open `main.py` → find `AFFILIATE_LINKS` section → replace with your real links:

```python
AFFILIATE_LINKS = {
    "amazon":    "https://amzn.to/YOUR_ID",
    "coursera":  "https://www.coursera.org/?ref=YOUR_ID",
    "nordvpn":   "https://nordvpn.com/?ref=YOUR_ID",
}
```

Get affiliate links from:
- Amazon: affiliate-program.amazon.com
- NordVPN: nordvpn.com/affiliate
- Coursera: coursera.org/affiliate

---

### 6️⃣ Enable GitHub Actions
- Click "Actions" tab in your repo
- Click "Enable workflows"

---

### 7️⃣ Test It Now
- Actions tab → "AutoBlog Daily Post" → "Run workflow"
- Wait 2-3 minutes
- Check your Dev.to profile for the new post! ✅

---

## 📈 Self-Evolution Timeline

```
Day 1      → First post, brain starts learning
Week 1     → Identifies what topics get views
Week 2     → Improves title formulas automatically
Month 1    → Finds competitor content gaps
Month 2    → Dominates specific tech niches
Month 3    → 10,000+ monthly views
Month 6    → 50,000+ monthly views 💰
```

---

## 💰 Earning Potential

| Method | When | Estimate |
|---|---|---|
| Affiliate links | From day 1 | $10-100/month |
| Dev.to Listings | After 100 followers | $50-200/month |
| Google AdSense | After 20+ posts | $100-500/month |
| Sponsored posts | After 500 followers | $200-1000/post |

---

## 🧠 How brain.json Evolves

The brain file starts simple and grows smarter every day:

```
Level 1  → Basic posting
Level 2  → Learns best topics
Level 3  → Optimizes titles
Level 4  → Exploits content gaps
Level 5  → Dominates niches
...
Level 10 → Expert blogger 🏆
```

---

## ❓ Troubleshooting

Check the **Actions** tab — each step shows exactly what happened.
Red ❌ = error message shown → fix and re-run.
