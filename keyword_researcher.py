"""
keyword_researcher.py
─────────────────────
Runs every day before posting.
Finds low competition keywords that can rank on Google fast.
Saves best keywords to brain.json for main.py to use.
"""

import os
import re
import json
import requests
from datetime import datetime

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
BRAIN_FILE     = "brain.json"
CURRENT_YEAR   = datetime.now().strftime("%Y")
TODAY          = datetime.now().strftime("%B %d, %Y")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def gemini_text(prompt, max_tokens=1000):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.5}
    }
    r = requests.post(GEMINI_URL, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def load_brain():
    if os.path.exists(BRAIN_FILE):
        with open(BRAIN_FILE) as f:
            return json.load(f)
    return {}


def save_brain(brain):
    with open(BRAIN_FILE, "w") as f:
        json.dump(brain, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Fetch What People Are Searching (Free Sources)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_trending_searches():
    """Get trending searches from free sources"""
    print("  🔍 Fetching trending searches...")
    searches = []

    # Source 1 — Dev.to trending tags
    try:
        r    = requests.get("https://dev.to/api/tags?per_page=20", timeout=10)
        tags = r.json()
        for tag in tags:
            searches.append({
                "term":   tag.get("name", ""),
                "source": "DevTo",
                "count":  tag.get("taggings_count", 0)
            })
    except Exception as e:
        print(f"    ⚠️ DevTo tags error: {e}")

    # Source 2 — Hacker News top stories titles as keyword hints
    try:
        ids     = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10
        ).json()[:20]
        for sid in ids[:10]:
            s = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                timeout=10
            ).json()
            if s and s.get("title"):
                searches.append({
                    "term":   s.get("title", ""),
                    "source": "HackerNews",
                    "count":  s.get("score", 0)
                })
    except Exception as e:
        print(f"    ⚠️ HackerNews error: {e}")

    print(f"  ✅ Found {len(searches)} search signals")
    return searches


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — AI Generates Low Competition Keywords
# ─────────────────────────────────────────────────────────────────────────────
def generate_low_competition_keywords(searches, brain):
    """
    AI analyzes trending searches and generates low competition
    long-tail keywords that can rank on Google fast.
    """
    print("  🧠 AI generating low competition keywords...")

    past_posts   = [p.get("title", "") for p in brain.get("posts_history", [])]
    hot_cats     = brain.get("topic_intelligence", {}).get("hot_categories", [])
    search_text  = "\n".join([
        f"- {s['term']} (source: {s['source']}, popularity: {s['count']})"
        for s in searches[:30]
    ])

    prompt = f"""You are an expert SEO keyword researcher. Today is {TODAY}.

Your job: Find LOW COMPETITION keywords that a new blog can rank for on Google FAST.

TRENDING SIGNALS RIGHT NOW:
{search_text}

OUR BLOG NICHES: AI, Cybersecurity, Software, Hardware
HOT CATEGORIES PERFORMING WELL: {hot_cats}

PAST POST TITLES (avoid similar keywords):
{chr(10).join(past_posts[-10:]) if past_posts else "None yet"}

RULES FOR LOW COMPETITION KEYWORDS:
- Must be 4-8 words long (long-tail = less competition)
- Must include {CURRENT_YEAR} where relevant
- Must be something real people search on Google
- Avoid very broad terms like "AI" or "cybersecurity" alone
- Focus on specific questions, comparisons, or how-to topics
- Target keywords with clear search intent

Respond ONLY in valid JSON, no markdown:
{{
  "primary_keywords": [
    {{
      "keyword": "exact low competition keyword phrase",
      "search_intent": "informational|comparison|how-to|what-is",
      "competition": "very-low|low|medium",
      "monthly_searches": "estimated searches per month",
      "blog_title_idea": "catchy blog title using this keyword"
    }}
  ],
  "secondary_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "question_keywords": [
    "what is X in {CURRENT_YEAR}?",
    "how to X without Y?",
    "why is X better than Y in {CURRENT_YEAR}?",
    "is X safe to use in {CURRENT_YEAR}?"
  ],
  "best_keyword_today": "the single best keyword to target today",
  "reasoning": "why these keywords have low competition"
}}"""

    try:
        raw     = gemini_text(prompt, max_tokens=1000)
        raw     = re.sub(r"```json|```", "", raw).strip()
        result  = json.loads(raw)
        print(f"  ✅ Generated {len(result.get('primary_keywords', []))} keywords")
        print(f"  🎯 Best keyword today: {result.get('best_keyword_today', '')}")
        return result
    except Exception as e:
        print(f"  ⚠️ Keyword generation error: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Save Keywords to Brain
# ─────────────────────────────────────────────────────────────────────────────
def save_keywords_to_brain(brain, keywords):
    """Save today's keywords to brain.json for main.py to use"""

    brain.setdefault("keyword_research", {})
    brain["keyword_research"] = {
        "last_updated":      TODAY,
        "primary_keywords":  keywords.get("primary_keywords", []),
        "secondary_keywords":keywords.get("secondary_keywords", []),
        "question_keywords": keywords.get("question_keywords", []),
        "best_keyword_today":keywords.get("best_keyword_today", ""),
        "reasoning":         keywords.get("reasoning", "")
    }

    # Keep history of past keywords
    brain.setdefault("keyword_history", [])
    brain["keyword_history"].append({
        "date":    TODAY,
        "keyword": keywords.get("best_keyword_today", "")
    })
    brain["keyword_history"] = brain["keyword_history"][-30:]

    save_brain(brain)
    print("  💾 Keywords saved to brain.json")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  🔍 Keyword Researcher — {TODAY}")
    print("="*60 + "\n")

    brain    = load_brain()
    searches = fetch_trending_searches()
    keywords = generate_low_competition_keywords(searches, brain)

    if keywords:
        save_keywords_to_brain(brain, keywords)

    print("\n" + "="*60)
    print("  ✅ Keyword research complete!")
    print(f"  🎯 Best keyword: {keywords.get('best_keyword_today', 'N/A')}")
    print(f"  📊 Total keywords: {len(keywords.get('primary_keywords', []))}")
    print("="*60 + "\n")

    return keywords


if __name__ == "__main__":
    main()
      
