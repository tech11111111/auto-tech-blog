"""
seo_optimizer.py
────────────────
Finds what competitors rank for on Google.
Identifies content gaps they are missing.
Generates SEO strategy to beat them.
Updates brain.json with winning SEO tactics.

ERROR HANDLING:
- Safe requests with timeouts
- Fallback SEO data
- JSON validation
"""

import os
import re
import json
import time
import requests
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DEVTO_API_KEY  = os.environ.get("DEVTO_API_KEY", "")
BRAIN_FILE     = "brain.json"
TODAY          = datetime.now().strftime("%B %d, %Y")
CURRENT_YEAR   = datetime.now().strftime("%Y")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
HEADERS    = {"User-Agent": "AutoBlogBot/3.0", "api-key": DEVTO_API_KEY}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def safe_get(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r
    except Exception as e:
        print(f"    ⚠️ Request error: {e}")
    return None


def gemini_text(prompt, max_tokens=1000):
    try:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.5}
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
    except Exception:
        pass
    return {}


def save_brain(brain):
    try:
        brain["last_updated"] = TODAY
        with open(BRAIN_FILE, "w") as f:
            json.dump(brain, f, indent=2)
    except Exception as e:
        print(f"  ⚠️ Save error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Fetch Top Competitor Articles
# ─────────────────────────────────────────────────────────────────────────────
def fetch_competitor_articles():
    """Get top performing articles from competitors on Dev.to"""
    print("  🕵️ Fetching competitor articles...")

    competitors = []
    try:
        # Get top articles
        r = safe_get("https://dev.to/api/articles?top=30&per_page=30")
        if r:
            for a in r.json():
                competitors.append({
                    "title":      a.get("title", ""),
                    "tags":       a.get("tag_list", []),
                    "views":      a.get("page_views_count", 0),
                    "likes":      a.get("positive_reactions_count", 0),
                    "comments":   a.get("comments_count", 0),
                    "author":     a.get("user", {}).get("username", ""),
                    "url":        a.get("url", ""),
                    "published":  a.get("published_at", "")
                })
    except Exception as e:
        print(f"    ⚠️ Competitor fetch error: {e}")

    print(f"    ✅ Found {len(competitors)} competitor articles")
    return competitors


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — AI Analyzes SEO Gaps
# ─────────────────────────────────────────────────────────────────────────────
def analyze_seo_gaps(competitors, brain):
    """AI finds what competitors rank for and what gaps exist"""
    print("  🧠 AI analyzing SEO gaps...")

    our_posts   = [p.get("title", "") for p in brain.get("posts_history", [])[-20:]]
    comp_text   = "\n".join([
        f"- [{', '.join(a['tags'][:3])}] {a['title']} (views:{a['views']}, likes:{a['likes']})"
        for a in competitors[:20]
    ])

    prompt = f"""You are an expert SEO analyst. Today is {TODAY}.

Analyze these top performing competitor articles on Dev.to:

TOP COMPETITOR ARTICLES:
{comp_text}

OUR PAST POSTS:
{chr(10).join(our_posts) if our_posts else "None yet"}

Find:
1. What topics/keywords competitors are NOT covering (gaps)
2. What title patterns get most views
3. What tags get most traction
4. What content formats perform best
5. Long-tail keywords we can rank for easily

Respond ONLY in valid JSON, no markdown:
{{
  "seo_gaps": [
    {{
      "gap": "topic nobody is covering",
      "keyword": "exact keyword to target",
      "competition": "low|medium|high",
      "opportunity_score": 8
    }}
  ],
  "winning_title_patterns": ["pattern1", "pattern2", "pattern3"],
  "best_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "best_content_format": "how-to|listicle|deep-dive|news|opinion",
  "long_tail_keywords": [
    "4-6 word keyword phrase 1",
    "4-6 word keyword phrase 2",
    "4-6 word keyword phrase 3"
  ],
  "competitor_weakness": "what competitors are doing poorly",
  "our_advantage": "how we can beat them",
  "recommended_post_frequency": "once daily is optimal",
  "seo_summary": "2 sentence SEO strategy for today"
}}"""

    try:
        raw    = gemini_text(prompt, max_tokens=1200)
        raw    = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        print(f"  ✅ Found {len(result.get('seo_gaps', []))} SEO gaps")
        print(f"  🎯 Best tags: {result.get('best_tags', [])[:3]}")
        return result
    except Exception as e:
        print(f"  ⚠️ SEO analysis error: {e}")
        return {
            "seo_gaps": [],
            "winning_title_patterns": ["How to", "Why", "What is"],
            "best_tags": ["ai", "webdev", "programming", "tech", "security"],
            "best_content_format": "how-to",
            "long_tail_keywords": [],
            "seo_summary": "Focus on long-tail keywords with low competition."
        }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Generate SEO Optimized Meta
# ─────────────────────────────────────────────────────────────────────────────
def generate_seo_meta(title, content_preview, focus_keyword):
    """Generate SEO metadata for a blog post"""
    prompt = f"""Generate SEO metadata for this blog post. Today: {TODAY}.

Title: {title}
Focus keyword: {focus_keyword}
Content preview: {content_preview[:300]}

Respond ONLY in valid JSON, no markdown:
{{
  "meta_title": "SEO optimized title under 60 chars",
  "meta_description": "compelling description under 155 chars with keyword",
  "slug": "url-friendly-slug",
  "focus_keyword": "{focus_keyword}",
  "secondary_keywords": ["kw1", "kw2", "kw3"],
  "schema_type": "Article|HowTo|NewsArticle|BlogPosting",
  "estimated_read_time": "5 min read"
}}"""

    try:
        raw    = gemini_text(prompt, max_tokens=400)
        raw    = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"  ⚠️ Meta generation error: {e}")
        return {
            "meta_title":        title[:60],
            "meta_description":  f"Learn about {focus_keyword} in {CURRENT_YEAR}",
            "slug":              title.lower().replace(" ", "-")[:50],
            "focus_keyword":     focus_keyword,
            "secondary_keywords":[],
            "schema_type":       "BlogPosting",
            "estimated_read_time":"5 min read"
        }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Update Brain
# ─────────────────────────────────────────────────────────────────────────────
def update_brain_seo(brain, seo_analysis):
    """Update brain with SEO intelligence"""
    try:
        brain["seo_intelligence"] = {
            "date":                TODAY,
            "gaps":                seo_analysis.get("seo_gaps", []),
            "winning_patterns":    seo_analysis.get("winning_title_patterns", []),
            "best_tags":           seo_analysis.get("best_tags", []),
            "long_tail_keywords":  seo_analysis.get("long_tail_keywords", []),
            "competitor_weakness": seo_analysis.get("competitor_weakness", ""),
            "our_advantage":       seo_analysis.get("our_advantage", ""),
            "seo_summary":         seo_analysis.get("seo_summary", "")
        }

        # Update topic intelligence
        brain.setdefault("topic_intelligence", {})
        brain["topic_intelligence"]["best_tags"]          = seo_analysis.get("best_tags", [])
        brain["topic_intelligence"]["trending_keywords"]  = seo_analysis.get("long_tail_keywords", [])
        brain["topic_intelligence"]["competitor_gaps"]    = [
            g.get("gap", "") for g in seo_analysis.get("seo_gaps", [])
        ]

        save_brain(brain)
        print("  ✅ SEO intelligence saved!")
    except Exception as e:
        print(f"  ⚠️ Brain update error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  🔎 SEO Optimizer — {TODAY}")
    print("="*60 + "\n")

    brain       = load_brain()
    competitors = fetch_competitor_articles()
    seo_analysis= analyze_seo_gaps(competitors, brain)
    update_brain_seo(brain, seo_analysis)

    print("\n" + "="*60)
    print("  ✅ SEO optimization complete!")
    print(f"  📊 SEO gaps found: {len(seo_analysis.get('seo_gaps', []))}")
    print(f"  🏷️  Best tags: {seo_analysis.get('best_tags', [])[:5]}")
    print(f"  💡 {seo_analysis.get('seo_summary', '')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
  
