"""
learner.py
──────────
Runs every evening at 6PM.
Checks today's post performance on Dev.to.
Analyzes what worked and what didn't.
Updates brain.json with new lessons.
The system gets smarter every single day.
"""

import os
import json
import re
import requests
from datetime import datetime
from competitor import get_competitor_intelligence


DEVTO_API_KEY  = os.environ["DEVTO_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
BRAIN_FILE     = "brain.json"
MEMORY_FILE    = "memory.json"
CURRENT_YEAR   = datetime.now().strftime("%Y")
TODAY          = datetime.now().strftime("%B %d, %Y")


# ─────────────────────────────────────────────────────────────────────────────
# FILE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def load_brain():
    if os.path.exists(BRAIN_FILE):
        with open(BRAIN_FILE) as f:
            return json.load(f)
    return {}


def save_brain(brain):
    brain["last_updated"] = TODAY
    with open(BRAIN_FILE, "w") as f:
        json.dump(brain, f, indent=2)
    print("  💾 Brain saved!")


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {"posts": []}


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def gemini_text(prompt):
    """Call Gemini for analysis"""
    url  = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1000, "temperature": 0.3}
    }
    r = requests.post(url, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Fetch Latest Stats from Dev.to
# ─────────────────────────────────────────────────────────────────────────────
def fetch_post_stats(memory):
    """Fetch latest views/likes for all our posts from Dev.to"""
    print("📊 Fetching latest post stats from Dev.to...")

    posts = memory.get("posts", [])
    if not posts:
        print("  ℹ️  No posts yet to analyze")
        return memory

    for post in posts:
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

                # Score the post
                score = post["views"] + (post["likes"] * 10) + (post["comments"] * 5)
                if score > 1000:   post["performance"] = "viral"
                elif score > 500:  post["performance"] = "high"
                elif score > 100:  post["performance"] = "medium"
                else:              post["performance"] = "low"

                print(f"  📈 '{post['title'][:40]}...' → {post['views']} views, {post['likes']} likes")
        except Exception as e:
            print(f"  ⚠️ Stats error: {e}")

    save_memory(memory)
    return memory


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — AI Analyzes Performance & Generates Lessons
# ─────────────────────────────────────────────────────────────────────────────
def analyze_performance(memory, brain):
    """
    AI analyzes all post performance.
    Finds patterns in what works and what doesn't.
    Generates actionable lessons to improve tomorrow's post.
    """
    print("🧠 AI analyzing performance patterns...")

    posts = memory.get("posts", [])
    if len(posts) < 1:
        print("  ℹ️  Need at least 1 post to analyze")
        return brain

    # Prepare performance data
    posts_data = json.dumps([{
        "date":        p.get("date"),
        "title":       p.get("title"),
        "tags":        p.get("tags"),
        "word_count":  p.get("word_count", 0),
        "length":      p.get("length"),
        "views":       p.get("views", 0),
        "likes":       p.get("likes", 0),
        "comments":    p.get("comments", 0),
        "performance": p.get("performance", "pending")
    } for p in posts[-20:]], indent=2)

    current_brain = json.dumps({
        "writing_rules":    brain.get("writing_rules", {}),
        "title_formulas":   brain.get("title_formulas", {}),
        "topic_intelligence": brain.get("topic_intelligence", {}),
        "growth_strategy":  brain.get("growth_strategy", {})
    }, indent=2)

    prompt = f"""You are an expert blog growth strategist. Today is {TODAY}.

Analyze this blog's performance data and generate specific improvements.

POST PERFORMANCE DATA:
{posts_data}

CURRENT BRAIN/RULES:
{current_brain}

Your job: Think like a growth hacker. Analyze every pattern. Find what's working and what's not.

Respond ONLY in valid JSON, no markdown:
{{
  "performance_summary": {{
    "total_views": 0,
    "total_likes": 0,
    "best_post_title": "title here",
    "worst_post_title": "title here",
    "avg_views_per_post": 0,
    "growth_trend": "growing|stable|declining"
  }},
  "what_worked": [
    "specific thing that got more views",
    "specific title pattern that got clicks",
    "specific topic category that performed well"
  ],
  "what_failed": [
    "specific thing that got low views",
    "specific pattern to avoid",
    "specific topic that flopped"
  ],
  "updated_writing_rules": {{
    "best_intro_style": "updated based on data",
    "best_length": "short|medium|long",
    "best_word_count": 1200,
    "avoid_phrases": ["phrase1", "phrase2"],
    "power_words": ["word1", "word2", "word3"],
    "best_structure": "updated structure"
  }},
  "updated_title_formulas": {{
    "best_performing": "best title formula based on data",
    "click_patterns": ["pattern1", "pattern2"],
    "avoid": ["avoid1", "avoid2"],
    "must_include_year": true
  }},
  "updated_topic_intelligence": {{
    "hot_categories": ["category1", "category2"],
    "cold_categories": ["avoid1"],
    "focus_next_week": "specific topic to focus on"
  }},
  "updated_growth_strategy": {{
    "current_level": "beginner|intermediate|advanced|expert",
    "weekly_view_goal": 500,
    "next_milestone": "specific goal",
    "growth_tactics": ["tactic1", "tactic2", "tactic3"]
  }},
  "daily_lessons": [
    "specific lesson 1 for tomorrow",
    "specific lesson 2 for tomorrow",
    "specific lesson 3 for tomorrow"
  ],
  "estimated_monthly_earnings_usd": 0.00
}}"""

    try:
        raw      = gemini_text(prompt)
        raw      = re.sub(r"```json|```", "", raw).strip()
        analysis = json.loads(raw)

        # Update brain with AI analysis
        brain["writing_rules"]     = analysis.get("updated_writing_rules",     brain.get("writing_rules", {}))
        brain["title_formulas"]    = analysis.get("updated_title_formulas",    brain.get("title_formulas", {}))
        brain["topic_intelligence"].update(analysis.get("updated_topic_intelligence", {}))
        brain["growth_strategy"]   = analysis.get("updated_growth_strategy",   brain.get("growth_strategy", {}))

        # Add today's lessons (keep last 30)
        new_lessons = analysis.get("daily_lessons", [])
        brain["daily_lessons"] = (brain.get("daily_lessons", []) + new_lessons)[-30:]

        # Save weekly analysis
        brain.setdefault("weekly_analysis", []).append({
            "date":            TODAY,
            "summary":         analysis.get("performance_summary", {}),
            "what_worked":     analysis.get("what_worked", []),
            "what_failed":     analysis.get("what_failed", []),
            "est_earnings":    analysis.get("estimated_monthly_earnings_usd", 0)
        })

        # Keep only last 12 weekly analyses
        brain["weekly_analysis"] = brain["weekly_analysis"][-12:]

        # Update identity stats
        summary = analysis.get("performance_summary", {})
        brain["identity"]["total_views"] = summary.get("total_views", brain["identity"].get("total_views", 0))
        brain["identity"]["total_likes"] = summary.get("total_likes", brain["identity"].get("total_likes", 0))
        brain["identity"]["level"]       = calculate_level(summary.get("total_views", 0))

        print(f"  ✅ Analysis complete!")
        print(f"  📈 What worked: {analysis.get('what_worked', [])[:2]}")
        print(f"  📉 What failed: {analysis.get('what_failed', [])[:2]}")
        print(f"  🎓 New lessons: {new_lessons[:2]}")
        print(f"  💰 Est. monthly earnings: ${analysis.get('estimated_monthly_earnings_usd', 0)}")

    except Exception as e:
        print(f"  ⚠️ Analysis error: {e}")

    return brain


def calculate_level(total_views):
    """Level up the blog as it grows"""
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
# STEP 3 — Update Growth Strategy
# ─────────────────────────────────────────────────────────────────────────────
def update_growth_strategy(brain, memory):
    """
    Updates the growth strategy based on current performance.
    Sets new goals for next week.
    """
    print("📈 Updating growth strategy...")

    posts         = memory.get("posts", [])
    total_views   = sum(p.get("views", 0) for p in posts)
    total_posts   = len(posts)
    level         = brain["identity"]["level"]

    # Set goals based on current level
    goals = {
        1:  {"weekly": 100,   "monthly": 400,    "milestone": "First 100 views"},
        2:  {"weekly": 300,   "monthly": 1200,   "milestone": "First 500 views"},
        3:  {"weekly": 700,   "monthly": 2800,   "milestone": "First 1000 views"},
        4:  {"weekly": 1500,  "monthly": 6000,   "milestone": "5000 total views"},
        5:  {"weekly": 3000,  "monthly": 12000,  "milestone": "10K total views"},
        6:  {"weekly": 7000,  "monthly": 28000,  "milestone": "25K total views"},
        7:  {"weekly": 15000, "monthly": 60000,  "milestone": "50K total views"},
        8:  {"weekly": 30000, "monthly": 120000, "milestone": "100K total views"},
        9:  {"weekly": 60000, "monthly": 240000, "milestone": "500K total views"},
        10: {"weekly": 100000,"monthly": 400000, "milestone": "1M total views 🏆"}
    }

    goal = goals.get(level, goals[1])
    brain["growth_strategy"]["weekly_view_goal"]   = goal["weekly"]
    brain["growth_strategy"]["monthly_view_goal"]  = goal["monthly"]
    brain["growth_strategy"]["next_milestone"]     = goal["milestone"]
    brain["identity"]["total_posts"]               = total_posts
    brain["identity"]["total_views"]               = total_views

    print(f"  ✅ Level {level} — Goal: {goal['weekly']} views/week")
    print(f"  🎯 Next milestone: {goal['milestone']}")

    return brain


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — Daily Learning Pipeline
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  🎓 AutoBlog LEARNER — {TODAY}")
    print("="*60 + "\n")

    # Load files
    brain  = load_brain()
    memory = load_memory()

    # Step 1 — Fetch latest stats
    memory = fetch_post_stats(memory)

    # Step 2 — Competitor analysis
    brain = get_competitor_intelligence(brain)

    # Step 3 — AI analyzes performance & generates lessons
    brain = analyze_performance(memory, brain)

    # Step 4 — Update growth strategy
    brain = update_growth_strategy(brain, memory)

    # Save everything
    save_brain(brain)
    save_memory(memory)

    print("\n" + "="*60)
    print(f"  🧠 Brain updated! Level {brain['identity']['level']}")
    print(f"  📚 Total lessons: {len(brain.get('daily_lessons', []))}")
    print(f"  👁️  Total views: {brain['identity'].get('total_views', 0)}")
    print(f"  🎯 Next milestone: {brain['growth_strategy'].get('next_milestone', '')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
    
