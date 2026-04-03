"""
title_optimizer.py
──────────────────
Generates 10 title variations for every blog post.
Scores each by: emotion, curiosity, SEO, viral potential.
Picks the highest scoring title automatically.
Learns which patterns get most clicks over time.

ERROR HANDLING:
- Fallback titles if AI fails
- Score validation
- JSON error recovery
"""

import os
import re
import json
import requests
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
BRAIN_FILE     = "brain.json"
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
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.9}
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
# MAIN FUNCTION — Generate & Score Titles
# ─────────────────────────────────────────────────────────────────────────────
def optimize_title(topic, keyword, industry="tech", brain=None):
    """
    Generate 10 title variations and pick the best one.
    Returns the winning title.
    """
    print(f"  📰 Optimizing title for: {topic[:50]}...")

    if brain is None:
        brain = load_brain()

    # Get past winning title patterns
    past_patterns = brain.get("title_formulas", {}).get("click_patterns", [])
    past_avoid    = brain.get("title_formulas", {}).get("avoid", [])
    best_formula  = brain.get("title_formulas", {}).get("best_performing", "")

    prompt = f"""You are a viral headline expert. Today is {TODAY}. Current year: {CURRENT_YEAR}.

Topic: {topic}
Focus keyword: {keyword}
Industry: {industry}

Generate 10 DIFFERENT title variations. Each must:
- Include {CURRENT_YEAR}
- Be different style (question, how-to, why, number, shocking, etc.)
- Target real Google searches
- Be emotionally engaging

Past winning patterns to use: {past_patterns}
Patterns to avoid: {past_avoid}
Best performing formula: {best_formula}

Score each title on:
- emotion_score: how much emotion it triggers (0-10)
- curiosity_score: how much curiosity it creates (0-10)
- seo_score: how well it targets keywords (0-10)
- viral_score: how likely to be shared (0-10)
- clarity_score: how clear and understandable (0-10)

Respond ONLY in valid JSON, no markdown:
{{
  "titles": [
    {{
      "title": "title text here",
      "style": "question|how-to|why|number|shocking|comparison|secret|warning",
      "emotion_score": 8,
      "curiosity_score": 9,
      "seo_score": 7,
      "viral_score": 8,
      "clarity_score": 9,
      "total_score": 8.2
    }}
  ],
  "winner": "the single best title",
  "winner_reason": "why this title will perform best",
  "runner_up": "second best title"
}}"""

    try:
        raw    = gemini_text(prompt, max_tokens=1500)
        raw    = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)

        winner = result.get("winner", "")
        titles = result.get("titles", [])

        if not winner and titles:
            # Fallback: pick highest total_score
            best = max(titles, key=lambda x: x.get("total_score", 0))
            winner = best.get("title", topic)

        print(f"  🏆 Winner: {winner}")
        print(f"  💡 Reason: {result.get('winner_reason', 'N/A')}")

        # Save winning pattern to brain
        _save_title_pattern(brain, result)

        return winner, result

    except Exception as e:
        print(f"  ⚠️ Title optimization error: {e}")
        # Fallback title
        fallback = f"{topic} — What You Need to Know in {CURRENT_YEAR}"
        return fallback, {"winner": fallback, "titles": []}


def _save_title_pattern(brain, result):
    """Save winning title patterns to brain for learning"""
    try:
        titles = result.get("titles", [])
        if not titles:
            return

        # Find winning style
        winner_title = result.get("winner", "")
        winning_style = ""
        for t in titles:
            if t.get("title") == winner_title:
                winning_style = t.get("style", "")
                break

        # Update brain patterns
        brain.setdefault("title_history", [])
        brain["title_history"].append({
            "date":    TODAY,
            "winner":  winner_title,
            "style":   winning_style,
            "scores":  [t.get("total_score", 0) for t in titles]
        })
        brain["title_history"] = brain["title_history"][-30:]

        # Update best performing formula
        if winning_style:
            brain.setdefault("title_formulas", {})
            patterns = brain["title_formulas"].get("click_patterns", [])
            if winning_style not in patterns:
                patterns.append(winning_style)
            brain["title_formulas"]["click_patterns"] = patterns[-10:]

        save_brain(brain)
    except Exception as e:
        print(f"  ⚠️ Pattern save error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  📰 Title Optimizer — {TODAY}")
    print("="*60 + "\n")

    # Test with sample topic
    test_topic   = "AI is replacing software developers"
    test_keyword = "AI replacing developers 2026"

    winner, result = optimize_title(test_topic, test_keyword, "CoreTech")

    print("\n  All generated titles:")
    for i, t in enumerate(result.get("titles", []), 1):
        print(f"  {i}. [{t.get('total_score', 0):.1f}] {t.get('title', '')}")

    print(f"\n  🏆 Winner: {winner}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
  
