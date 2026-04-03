"""
industry_scanner.py
───────────────────
Scans ALL industries for tech crossover opportunities.
Medical+AI, Farming+Robots, Education+Tech, Finance+Crypto etc.
Finds viral opportunities BEFORE competitors.
Saves intelligence to brain.json.

ERROR HANDLING:
- Safe API calls with retries
- Fallback data if sources fail
- JSON validation before saving
- Graceful degradation
"""

import os
import re
import json
import time
import requests
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
BRAIN_FILE     = "brain.json"
TODAY          = datetime.now().strftime("%B %d, %Y")
CURRENT_YEAR   = datetime.now().strftime("%Y")
CURRENT_MONTH  = datetime.now().strftime("%B %Y")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"

HEADERS = {"User-Agent": "AutoBlogBot/3.0"}

# ── ALL INDUSTRIES TO SCAN ────────────────────────────────────────────────────
INDUSTRIES = {
    "MedTech":     ["health AI", "medical devices", "digital health", "biotech", "telemedicine"],
    "AgriTech":    ["farming robots", "precision agriculture", "crop AI", "smart farming"],
    "EdTech":      ["education AI", "online learning", "AI tutoring", "classroom tech"],
    "FinTech":     ["crypto", "digital banking", "payment tech", "DeFi", "financial AI"],
    "LegalTech":   ["legal AI", "law automation", "contract AI", "legal software"],
    "SpaceTech":   ["space technology", "satellite AI", "rocket tech", "space exploration"],
    "CleanTech":   ["green energy AI", "solar tech", "EV technology", "climate tech"],
    "RetailTech":  ["retail AI", "ecommerce tech", "supply chain AI", "shopping tech"],
    "SportsTech":  ["sports AI", "wearable tech", "athlete tracking", "sports analytics"],
    "GovTech":     ["government AI", "smart city", "public sector tech", "civic tech"],
    "CoreTech":    ["artificial intelligence", "cybersecurity", "software", "hardware", "chips"]
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def safe_get(url, timeout=10, retries=2):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r
            time.sleep(1)
        except Exception as e:
            print(f"    ⚠️ Request failed: {e}")
            time.sleep(2)
    return None


def gemini_text(prompt, max_tokens=1500):
    try:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.6}
        }
        r = requests.post(GEMINI_URL, json=body, timeout=60)
        r.raise_for_status()
        candidates = r.json().get("candidates", [])
        if candidates:
            return candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"    ⚠️ Gemini error: {e}")
    return ""


def load_brain():
    try:
        if os.path.exists(BRAIN_FILE):
            with open(BRAIN_FILE) as f:
                return json.load(f)
    except Exception as e:
        print(f"  ⚠️ Brain load error: {e}")
    return {}


def save_brain(brain):
    try:
        brain["last_updated"] = TODAY
        with open(BRAIN_FILE, "w") as f:
            json.dump(brain, f, indent=2)
    except Exception as e:
        print(f"  ⚠️ Brain save error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Scan Each Industry
# ─────────────────────────────────────────────────────────────────────────────
def scan_industry_news():
    """Scan HackerNews and Dev.to for cross-industry tech stories"""
    print("  🌍 Scanning all industries...")

    industry_signals = {}

    # HackerNews top stories
    hn_stories = []
    try:
        r = safe_get("https://hacker-news.firebaseio.com/v0/topstories.json")
        if r:
            ids = r.json()[:40]
            for sid in ids[:20]:
                story_r = safe_get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                if story_r:
                    s = story_r.json()
                    if s and s.get("title"):
                        hn_stories.append({
                            "title": s.get("title", ""),
                            "score": s.get("score", 0),
                            "source": "HackerNews"
                        })
                time.sleep(0.1)
    except Exception as e:
        print(f"    ⚠️ HN scan error: {e}")

    # Dev.to trending
    devto_stories = []
    try:
        r = safe_get("https://dev.to/api/articles?top=7&per_page=20")
        if r:
            for a in r.json():
                devto_stories.append({
                    "title": a.get("title", ""),
                    "score": a.get("positive_reactions_count", 0),
                    "source": "DevTo"
                })
    except Exception as e:
        print(f"    ⚠️ DevTo scan error: {e}")

    all_stories = hn_stories + devto_stories

    # Categorize by industry
    for industry, keywords in INDUSTRIES.items():
        matching = []
        for story in all_stories:
            title_lower = story["title"].lower()
            if any(kw.lower() in title_lower for kw in keywords):
                matching.append(story)
        if matching:
            industry_signals[industry] = matching
            print(f"    ✅ {industry}: {len(matching)} signals")

    return industry_signals, all_stories


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — AI Finds Cross-Industry Opportunities
# ─────────────────────────────────────────────────────────────────────────────
def find_crossindustry_opportunities(industry_signals, all_stories, brain):
    """AI analyzes signals to find viral cross-industry opportunities"""
    print("  🧠 AI finding cross-industry opportunities...")

    past_posts = [p.get("title", "") for p in brain.get("posts_history", [])[-20:]]

    signals_text = ""
    for industry, stories in industry_signals.items():
        signals_text += f"\n{industry}:\n"
        for s in stories[:3]:
            signals_text += f"  - {s['title']} (score: {s['score']})\n"

    all_text = "\n".join([f"- {s['title']}" for s in all_stories[:20]])

    prompt = f"""You are a viral content strategist analyzing tech trends across ALL industries. Today is {TODAY}.

INDUSTRY SIGNALS DETECTED:
{signals_text if signals_text else "General tech trends only"}

ALL TRENDING STORIES:
{all_text}

PAST POSTS (avoid repeating):
{chr(10).join(past_posts) if past_posts else "None yet"}

Your job: Find the BEST cross-industry tech opportunities for viral blog posts.

Think creatively:
- Where is technology disrupting unexpected industries?
- What tech trend affects the most people's daily lives?
- What would shock or surprise readers?
- What is nobody else writing about yet?

Respond ONLY in valid JSON, no markdown:
{{
  "opportunities": [
    {{
      "industry": "MedTech|AgriTech|EdTech|FinTech|CoreTech|etc",
      "topic": "specific topic to write about",
      "angle": "unique viral angle",
      "why_viral": "why this will spread",
      "suggested_title": "catchy title with {CURRENT_YEAR}",
      "viral_score": 8.5,
      "target_audience": "who will read and share this"
    }}
  ],
  "hottest_industry_today": "industry name",
  "best_opportunity": "single best topic to write about today",
  "trend_summary": "2 sentence summary of today's tech landscape"
}}"""

    try:
        raw    = gemini_text(prompt, max_tokens=1500)
        raw    = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        print(f"  ✅ Found {len(result.get('opportunities', []))} opportunities")
        print(f"  🌍 Hottest industry: {result.get('hottest_industry_today', 'N/A')}")
        return result
    except Exception as e:
        print(f"  ⚠️ Opportunity finding error: {e}")
        return {
            "opportunities": [],
            "hottest_industry_today": "CoreTech",
            "best_opportunity": "Latest AI developments",
            "trend_summary": "Tech continues advancing rapidly."
        }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Update Brain with Industry Intelligence
# ─────────────────────────────────────────────────────────────────────────────
def update_brain_with_industry_intel(brain, opportunities, industry_signals):
    """Save industry intelligence to brain"""
    try:
        brain["industry_intelligence"] = {
            "date":               TODAY,
            "opportunities":      opportunities.get("opportunities", []),
            "hottest_industry":   opportunities.get("hottest_industry_today", "CoreTech"),
            "best_opportunity":   opportunities.get("best_opportunity", ""),
            "trend_summary":      opportunities.get("trend_summary", ""),
            "active_industries":  list(industry_signals.keys())
        }

        # Update hot categories based on today's signals
        hot = list(industry_signals.keys())[:5]
        brain.setdefault("topic_intelligence", {})
        brain["topic_intelligence"]["hot_industries"] = hot
        brain["topic_intelligence"]["last_scan"]      = TODAY

        save_brain(brain)
        print("  ✅ Industry intelligence saved to brain!")
    except Exception as e:
        print(f"  ⚠️ Update error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  🌍 Industry Scanner — {TODAY}")
    print("="*60 + "\n")

    brain = load_brain()

    # Scan all industries
    industry_signals, all_stories = scan_industry_news()
    print(f"\n  📊 Industries with signals: {len(industry_signals)}")
    print(f"  📰 Total stories found: {len(all_stories)}\n")

    # Find opportunities
    opportunities = find_crossindustry_opportunities(
        industry_signals, all_stories, brain
    )

    # Update brain
    update_brain_with_industry_intel(brain, opportunities, industry_signals)

    print("\n" + "="*60)
    print("  ✅ Industry scan complete!")
    print(f"  🌍 Hottest: {opportunities.get('hottest_industry_today', 'N/A')}")
    print(f"  🎯 Best opportunity: {opportunities.get('best_opportunity', 'N/A')}")
    print(f"  📝 {opportunities.get('trend_summary', '')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
          
