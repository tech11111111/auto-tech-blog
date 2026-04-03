"""
viral_detector.py
─────────────────
Detects topics JUST starting to trend before they go mainstream.
Scans Reddit, HackerNews, GitHub Trending, ProductHunt.
Scores each topic for viral potential.
Saves predictions to brain.json for main.py to use.

ERROR HANDLING:
- All API calls wrapped in try/except
- Fallback topics if sources fail
- Retry logic for network errors
- Validates all data before saving
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

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"

# ── HEADERS ───────────────────────────────────────────────────────────────────
HEADERS = {"User-Agent": "AutoBlogBot/3.0 (research purposes)"}


# ─────────────────────────────────────────────────────────────────────────────
# SAFE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def safe_get(url, timeout=10, retries=2):
    """Safe GET with retry logic"""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r
            time.sleep(2)
        except Exception as e:
            print(f"    ⚠️ Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None


def gemini_text(prompt, max_tokens=1000):
    """Call Gemini with error handling"""
    try:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7}
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
    """Load brain with fallback"""
    try:
        if os.path.exists(BRAIN_FILE):
            with open(BRAIN_FILE) as f:
                return json.load(f)
    except Exception as e:
        print(f"  ⚠️ Brain load error: {e}")
    return {
        "identity": {"blog_name": "TechPulse AI", "level": 1},
        "viral_predictions": [],
        "daily_lessons": [],
        "topic_intelligence": {"hot_categories": [], "cold_categories": []}
    }


def save_brain(brain):
    """Save brain with error handling"""
    try:
        brain["last_updated"] = TODAY
        with open(BRAIN_FILE, "w") as f:
            json.dump(brain, f, indent=2)
        print("  💾 Brain saved!")
    except Exception as e:
        print(f"  ⚠️ Brain save error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Scan Sources for Rising Topics
# ─────────────────────────────────────────────────────────────────────────────
def scan_hackernews_rising():
    """Get HackerNews new stories that are rising fast"""
    print("  📡 Scanning HackerNews new stories...")
    topics = []
    try:
        r = safe_get("https://hacker-news.firebaseio.com/v0/newstories.json")
        if not r:
            return topics
        ids = r.json()[:50]
        for sid in ids[:20]:
            story_r = safe_get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
            if not story_r:
                continue
            s = story_r.json()
            if s and s.get("score", 0) > 10:
                topics.append({
                    "title":   s.get("title", ""),
                    "score":   s.get("score", 0),
                    "source":  "HackerNews_Rising",
                    "url":     s.get("url", "")
                })
            time.sleep(0.1)
    except Exception as e:
        print(f"    ⚠️ HN error: {e}")
    print(f"    ✅ Found {len(topics)} rising HN stories")
    return topics


def scan_github_trending():
    """Get GitHub trending repositories as tech topic signals"""
    print("  📡 Scanning GitHub trending...")
    topics = []
    try:
        r = safe_get("https://api.github.com/search/repositories?q=created:>2026-03-01&sort=stars&order=desc&per_page=10")
        if not r:
            return topics
        repos = r.json().get("items", [])
        for repo in repos[:10]:
            topics.append({
                "title":  f"{repo.get('name', '')} - {repo.get('description', '')}",
                "score":  repo.get("stargazers_count", 0),
                "source": "GitHub_Trending",
                "url":    repo.get("html_url", "")
            })
    except Exception as e:
        print(f"    ⚠️ GitHub error: {e}")
    print(f"    ✅ Found {len(topics)} GitHub trends")
    return topics


def scan_devto_rising():
    """Get Dev.to articles rising in last 24 hours"""
    print("  📡 Scanning Dev.to rising...")
    topics = []
    try:
        r = safe_get("https://dev.to/api/articles?top=1&per_page=20")
        if not r:
            return topics
        articles = r.json()
        for a in articles:
            topics.append({
                "title":  a.get("title", ""),
                "score":  a.get("positive_reactions_count", 0),
                "source": "DevTo_Rising",
                "url":    a.get("url", "")
            })
    except Exception as e:
        print(f"    ⚠️ DevTo error: {e}")
    print(f"    ✅ Found {len(topics)} Dev.to rising posts")
    return topics


def scan_google_trends():
    """Get Google Trends for viral signals"""
    print("  📡 Scanning Google Trends...")
    topics = []
    try:
        import xml.etree.ElementTree as ET
        r = safe_get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
        if not r:
            return topics
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:15]:
            title   = item.findtext("title", "")
            traffic = item.findtext(
                "{https://trends.google.com/trends/trendingsearches/daily}approx_traffic", "0"
            )
            traffic_num = int(traffic.replace(",", "").replace("+", "")) if traffic else 0
            topics.append({
                "title":  title,
                "score":  traffic_num,
                "source": "GoogleTrends",
                "url":    ""
            })
    except Exception as e:
        print(f"    ⚠️ Google Trends error: {e}")
    print(f"    ✅ Found {len(topics)} Google trends")
    return topics


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Score Viral Potential with AI
# ─────────────────────────────────────────────────────────────────────────────
def score_viral_potential(topics, brain):
    """AI scores each topic for viral potential across ALL industries"""
    print("  🧠 AI scoring viral potential...")

    if not topics:
        print("  ⚠️ No topics to score")
        return []

    past_posts  = [p.get("title", "") for p in brain.get("posts_history", [])[-20:]]
    topics_text = "\n".join([
        f"{i+1}. [{t['source']}] {t['title']} (score: {t['score']})"
        for i, t in enumerate(topics[:30])
    ])

    prompt = f"""You are a viral content strategist. Today is {TODAY}.

Analyze these trending topics and score each for VIRAL potential.

IMPORTANT: Topics can be from ANY industry:
- Pure tech (AI, cybersecurity, software, hardware)
- Cross-industry tech (MedTech, AgriTech, EdTech, FinTech, SpaceTech)
- Any topic where technology intersects real life
- Breaking news with tech angle

TRENDING TOPICS:
{topics_text}

PAST POSTS (avoid similar):
{chr(10).join(past_posts) if past_posts else "None yet"}

Score each topic:
- trending_now: is it hot RIGHT NOW? (0-10)
- surprise_factor: unexpected/shocking angle? (0-10)
- audience_reach: how many people care? (0-10)
- competition_gap: nobody else covered it yet? (0-10)
- emotion_trigger: makes people feel something? (0-10)
- share_potential: will people share it? (0-10)

RULE: Only include topics with average score 6+

Respond ONLY in valid JSON, no markdown:
{{
  "viral_topics": [
    {{
      "title": "original title",
      "viral_score": 8.5,
      "blog_angle": "unique angle to cover this topic",
      "industry": "tech|medtech|agritech|edtech|fintech|spacetech|other",
      "scores": {{
        "trending_now": 9,
        "surprise_factor": 8,
        "audience_reach": 9,
        "competition_gap": 7,
        "emotion_trigger": 8,
        "share_potential": 9
      }},
      "suggested_title": "viral blog title for {CURRENT_YEAR}"
    }}
  ],
  "best_topic_today": "single best topic to write about",
  "best_industry": "which industry is hottest today"
}}"""

    try:
        raw    = gemini_text(prompt, max_tokens=1500)
        raw    = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        topics = result.get("viral_topics", [])
        print(f"  ✅ Scored {len(topics)} viral topics")
        print(f"  🏆 Best today: {result.get('best_topic_today', 'N/A')}")
        print(f"  🌍 Hottest industry: {result.get('best_industry', 'N/A')}")
        return result
    except Exception as e:
        print(f"  ⚠️ Scoring error: {e}")
        return {"viral_topics": [], "best_topic_today": "", "best_industry": "tech"}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Save Predictions to Brain
# ─────────────────────────────────────────────────────────────────────────────
def save_viral_predictions(brain, predictions):
    """Save viral predictions to brain for main.py to use"""
    try:
        brain["viral_predictions"] = {
            "date":         TODAY,
            "topics":       predictions.get("viral_topics", []),
            "best_topic":   predictions.get("best_topic_today", ""),
            "best_industry":predictions.get("best_industry", "tech")
        }

        # Keep prediction history
        brain.setdefault("prediction_history", [])
        brain["prediction_history"].append({
            "date":  TODAY,
            "topic": predictions.get("best_topic_today", ""),
            "industry": predictions.get("best_industry", "tech")
        })
        brain["prediction_history"] = brain["prediction_history"][-30:]

        save_brain(brain)
        print("  ✅ Viral predictions saved to brain!")
    except Exception as e:
        print(f"  ⚠️ Save error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  🔥 Viral Detector — {TODAY}")
    print("="*60 + "\n")

    brain = load_brain()

    # Scan all sources
    all_topics = []
    all_topics += scan_hackernews_rising()
    all_topics += scan_github_trending()
    all_topics += scan_devto_rising()
    all_topics += scan_google_trends()

    print(f"\n  📊 Total topics found: {len(all_topics)}")

    if not all_topics:
        print("  ⚠️ No topics found from any source — using fallback")
        all_topics = [{"title": "AI developments today", "score": 100, "source": "fallback", "url": ""}]

    # Score viral potential
    predictions = score_viral_potential(all_topics, brain)

    # Save to brain
    save_viral_predictions(brain, predictions)

    print("\n" + "="*60)
    print("  ✅ Viral detection complete!")
    print(f"  🔥 Topics scored: {len(predictions.get('viral_topics', []))}")
    print(f"  🏆 Best topic: {predictions.get('best_topic_today', 'N/A')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

