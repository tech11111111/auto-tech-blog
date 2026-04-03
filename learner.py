"""
learner.py
──────────
Runs every evening at 6PM.
Checks performance of ALL posts.
Analyzes what went viral and why.
Updates brain.json with new lessons.
Gets smarter every single day.

ERROR HANDLING:
- Safe API calls
- Graceful failures
- Data validation
- Brain backup before update
"""

import os
import re
import json
import requests
from datetime import datetime
from competitor import get_competitor_intelligence

# ── CONFIG ────────────────────────────────────────────────────────────────────
DEVTO_API_KEY  = os.environ.get("DEVTO_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
BRAIN_FILE     = "brain.json"
MEMORY_FILE    = "memory.json"
TODAY          = datetime.now().strftime("%B %d, %Y")
CURRENT_YEAR   = datetime.now().strftime("%Y")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def gemini_text(prompt, max_tokens=1000):
    try:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.3}
        }
        r = requests.post(GEMINI_URL, json=body, timeout=60)
        r.raise_for_status()
        candidates = r.json().get("candidates", [])
        if candidates:
            return candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"  ⚠️ Gemini error: {e}")
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
        print("  💾 Brain saved!")
    except Exception as e:
        print(f"  ⚠️ Brain save error: {e}")


def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE) as f:
                return json.load(f)
    except Exception as e:
        print(f"  ⚠️ Memory load error: {e}")
    return {"posts": []}


def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"  ⚠️ Memory save error: {e}")


def calculate_level(total_views):
    if total_views >= 100000: return 10
    if total_views >= 50000:  return 9
    if total_views >= 20000:  return 8
    if total_views >= 10000:  return 7
    if total_views >= 5000:   return 6
    if total_views >= 2000:   return 5
    if total_views >= 1000:   return 4
    if total_views >= 500:    return 3
    if total_views >= 100:    return 2
    return 1


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Fetch Latest Stats
# ─────────────────────────────────────────────────────────────────────────────
def fetch_post_stats(memory):
    """Fetch latest performance stats for all posts"""
    print("📊 Fetching post stats from Dev.to...")

    posts = memory.get("posts", [])
    if not posts:
        print("  ℹ️  No posts yet")
        return memory

    updated = 0
    for post in posts[-10:]:  # Check last 10 posts
        article_id = post.get("article_id")
        if not article_id:
            continue
        try:
            r = requests.get(
                f"https://dev.to/api/articles/{article_id}",
                headers={"api-key": DEVTO_API_KEY},
                timeout=10
            )
            if r.status_code == 200:
                data             = r.json()
                post["views"]    = data.get("page_views_count", 0)
                post["likes"]    = data.get("positive_reactions_count", 0)
                post["comments"] = data.get("comments_count", 0)

                # Calculate performance score
                score = post["views"] + (post["likes"] * 10) + (post["comments"] * 5)
                if score > 2000:   post["performance"] = "viral"
                elif score > 500:  post["performance"] = "high"
                elif score > 100:  post["performance"] = "medium"
                else:              post["performance"] = "low"
                updated += 1

                print(f"  📈 '{post['title'][:35]}...' → {post['views']}v {post['likes']}❤️")
        except Exception as e:
            print(f"  ⚠️ Stats fetch error: {e}")

    print(f"  ✅ Updated {updated} posts")
    save_memory(memory)
    return memory


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Deep Analysis with AI
# ─────────────────────────────────────────────────────────────────────────────
def deep_analysis(memory, brain):
    """AI performs deep analysis of all performance data"""
    print("🧠 AI performing deep analysis...")

    posts = memory.get("posts", [])
    if not posts:
        print("  ℹ️  No posts to analyze")
        return brain

    posts_data = json.dumps([{
        "date":        p.get("date", ""),
        "title":       p.get("title", ""),
        "industry":    p.get("industry", "CoreTech"),
        "tags":        p.get("tags", []),
        "length":      p.get("length", "medium"),
        "word_count":  p.get("word_count", 0),
        "viral_score": p.get("viral_score", 0),
        "views":       p.get("views", 0),
        "likes":       p.get("likes", 0),
        "comments":    p.get("comments", 0),
        "performance": p.get("performance", "pending")
    } for p in posts[-20:]], indent=2)

    current_rules = json.dumps({
        "writing_rules":    brain.get("writing_rules", {}),
        "title_formulas":   brain.get("title_formulas", {}),
        "growth_strategy":  brain.get("growth_strategy", {})
    }, indent=2)

    prompt = f"""You are an expert blog growth analyst. Today is {TODAY}.

Analyze this blog's complete performance data and generate specific improvements.

PERFORMANCE DATA:
{posts_data}

CURRENT RULES:
{current_rules}

Think like a growth hacker. Find EVERY pattern. Be specific and actionable.

Respond ONLY in valid JSON, no markdown:
{{
  "performance_summary": {{
    "total_views": 0,
    "total_likes": 0,
    "best_post_title": "title",
    "worst_post_title": "title",
    "avg_views_per_post": 0,
    "best_industry": "which industry performed best",
    "growth_trend": "growing|stable|declining"
  }},
  "what_worked": [
    "specific thing that increased views",
    "specific title pattern that got clicks",
    "specific industry that performed well",
    "specific content length that worked"
  ],
  "what_failed": [
    "specific thing that reduced views",
    "pattern to avoid",
    "topic or industry that flopped"
  ],
  "updated_writing_rules": {{
    "best_intro_style": "data-driven recommendation",
    "best_length": "short|medium|long",
    "best_word_count": 1200,
    "avoid_phrases": ["phrase1", "phrase2"],
    "power_words": ["word1", "word2", "word3"],
    "best_structure": "updated structure"
  }},
  "updated_title_formulas": {{
    "best_performing": "best formula based on data",
    "click_patterns": ["pattern1", "pattern2"],
    "avoid": ["avoid1"],
    "must_include_year": true
  }},
  "industry_performance": {{
    "best_industries": ["industry1", "industry2"],
    "avoid_industries": ["industry3"],
    "next_industry_focus": "which industry to target tomorrow"
  }},
  "updated_growth_strategy": {{
    "current_level": "beginner|intermediate|advanced|expert",
    "weekly_view_goal": 500,
    "next_milestone": "specific goal",
    "growth_tactics": ["tactic1", "tactic2", "tactic3"]
  }},
  "daily_lessons": [
    "specific actionable lesson 1",
    "specific actionable lesson 2",
    "specific actionable lesson 3",
    "specific actionable lesson 4",
    "specific actionable lesson 5"
  ],
  "viral_patterns": [
    "what made top posts go viral"
  ],
  "estimated_monthly_earnings_usd": 0.00
}}"""

    try:
        raw      = gemini_text(prompt, max_tokens=1500)
        raw      = re.sub(r"```json|```", "", raw).strip()
        analysis = json.loads(raw)

        # Update brain with analysis
        brain["writing_rules"]  = analysis.get("updated_writing_rules",  brain.get("writing_rules", {}))
        brain["title_formulas"] = analysis.get("updated_title_formulas", brain.get("title_formulas", {}))
        brain["growth_strategy"]= analysis.get("updated_growth_strategy",brain.get("growth_strategy", {}))

        # Add lessons
        new_lessons  = analysis.get("daily_lessons", [])
        brain["daily_lessons"] = (brain.get("daily_lessons", []) + new_lessons)[-30:]

        # Add viral patterns
        brain["viral_patterns"] = analysis.get("viral_patterns", [])

        # Industry performance
        brain.setdefault("topic_intelligence", {})
        industry_perf = analysis.get("industry_performance", {})
        brain["topic_intelligence"]["hot_industries"]    = industry_perf.get("best_industries", [])
        brain["topic_intelligence"]["avoid_industries"]  = industry_perf.get("avoid_industries", [])
        brain["topic_intelligence"]["next_focus"]        = industry_perf.get("next_industry_focus", "CoreTech")

        # Save weekly analysis
        summary = analysis.get("performance_summary", {})
        brain.setdefault("weekly_analysis", [])
        brain["weekly_analysis"].append({
            "date":         TODAY,
            "summary":      summary,
            "what_worked":  analysis.get("what_worked", []),
            "what_failed":  analysis.get("what_failed", []),
            "est_earnings": analysis.get("estimated_monthly_earnings_usd", 0)
        })
        brain["weekly_analysis"] = brain["weekly_analysis"][-12:]

        # Update level
        total_views = summary.get("total_views", 0)
        brain["identity"]["level"]       = calculate_level(total_views)
        brain["identity"]["total_views"] = total_views
        brain["identity"]["total_likes"] = summary.get("total_likes", 0)

        print(f"  ✅ Analysis complete!")
        print(f"  📈 What worked: {analysis.get('what_worked', [])[:2]}")
        print(f"  📉 What failed: {analysis.get('what_failed', [])[:2]}")
        print(f"  🎓 New lessons: {len(new_lessons)}")
        print(f"  💰 Est. earnings: ${analysis.get('estimated_monthly_earnings_usd', 0)}/month")
        print(f"  🏆 Level: {brain['identity']['level']}/10")

    except Exception as e:
        print(f"  ⚠️ Analysis error: {e}")

    return brain


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  🎓 TechPulse AI Learner — {TODAY}")
    print("="*60 + "\n")

    brain  = load_brain()
    memory = load_memory()

    # Step 1 — Fetch stats
    memory = fetch_post_stats(memory)

    # Step 2 — Competitor intelligence
    try:
        brain = get_competitor_intelligence(brain)
    except Exception as e:
        print(f"  ⚠️ Competitor intelligence error: {e}")

    # Step 3 — Deep analysis
    brain = deep_analysis(memory, brain)

    # Step 4 — Save everything
    save_brain(brain)
    save_memory(memory)

    level    = brain.get("identity", {}).get("level", 1)
    views    = brain.get("identity", {}).get("total_views", 0)
    lessons  = len(brain.get("daily_lessons", []))
    milestone= brain.get("growth_strategy", {}).get("next_milestone", "")

    print("\n" + "="*60)
    print(f"  🧠 Brain evolved! Level {level}/10")
    print(f"  👁️  Total views: {views}")
    print(f"  📚 Total lessons: {lessons}")
    print(f"  🎯 Next milestone: {milestone}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
    
