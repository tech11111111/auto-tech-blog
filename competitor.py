"""
competitor.py
─────────────
Watches top performing blogs on Dev.to every day.
Finds content gaps, learns title patterns, discovers hot topics.
Saves intelligence into brain.json for main.py to use.
"""

import json
import requests
from datetime import datetime


DEVTO_API = "https://dev.to/api"


def fetch_top_articles():
    """Fetch top articles from Dev.to today"""
    print("  🕵️  Fetching top Dev.to articles...")
    try:
        r = requests.get(
            f"{DEVTO_API}/articles?top=1&per_page=30",
            timeout=10
        )
        return r.json()
    except Exception as e:
        print(f"    ⚠️ Error: {e}")
        return []


def fetch_trending_tags():
    """Fetch what tags are trending on Dev.to"""
    print("  🏷️  Fetching trending tags...")
    try:
        r = requests.get(
            f"{DEVTO_API}/tags?per_page=20",
            timeout=10
        )
        return r.json()
    except Exception as e:
        print(f"    ⚠️ Error: {e}")
        return []


def analyze_title_patterns(articles):
    """
    Analyze what makes top titles successful.
    Looks for: power words, length, structure, numbers, year usage.
    """
    patterns = {
        "starts_with_why":    0,
        "starts_with_how":    0,
        "starts_with_what":   0,
        "has_number":         0,
        "has_year":           0,
        "avg_title_length":   0,
        "top_power_words":    {}
    }

    power_words = [
        "why", "how", "what", "secret", "truth", "finally",
        "exposed", "guide", "best", "top", "free", "fast",
        "easy", "new", "now", "today", "2026", "never", "always"
    ]

    total_length = 0
    for a in articles:
        title = a.get("title", "").lower()
        total_length += len(title.split())

        if title.startswith("why"):   patterns["starts_with_why"] += 1
        if title.startswith("how"):   patterns["starts_with_how"] += 1
        if title.startswith("what"):  patterns["starts_with_what"] += 1
        if any(c.isdigit() for c in title): patterns["has_number"] += 1
        if "2026" in title or "2025" in title: patterns["has_year"] += 1

        for word in power_words:
            if word in title:
                patterns["top_power_words"][word] = patterns["top_power_words"].get(word, 0) + 1

    if articles:
        patterns["avg_title_length"] = round(total_length / len(articles), 1)

    # Sort power words by frequency
    patterns["top_power_words"] = dict(
        sorted(patterns["top_power_words"].items(), key=lambda x: x[1], reverse=True)[:10]
    )

    return patterns


def find_content_gaps(articles, brain):
    """
    Find topics competitors are NOT covering well.
    These are opportunities for us to rank.
    """
    covered_topics = set()
    for a in articles:
        tags = a.get("tag_list", [])
        covered_topics.update(tags)

    our_niches = ["ai", "machinelearning", "cybersecurity", "hardware", "software"]
    gaps = []

    for niche in our_niches:
        niche_articles = [
            a for a in articles
            if niche in [t.lower() for t in a.get("tag_list", [])]
        ]
        if len(niche_articles) < 3:
            gaps.append(f"Low competition in '{niche}' — only {len(niche_articles)} top posts")

    return gaps


def get_competitor_intelligence(brain):
    """
    Main function — runs full competitor analysis.
    Returns updated brain with new intelligence.
    """
    print("🕵️  Running competitor analysis...")

    articles = fetch_top_articles()
    tags     = fetch_trending_tags()

    if not articles:
        print("  ⚠️ No competitor data found")
        return brain

    # Analyze titles
    title_patterns = analyze_title_patterns(articles)

    # Find content gaps
    gaps = find_content_gaps(articles, brain)

    # Get trending tags
    trending_tag_names = [t.get("name", "") for t in tags[:15]] if tags else []

    # Get top performing topics
    top_topics = []
    for a in sorted(articles, key=lambda x: x.get("positive_reactions_count", 0), reverse=True)[:5]:
        top_topics.append({
            "title":  a.get("title", ""),
            "views":  a.get("page_views_count", 0),
            "likes":  a.get("positive_reactions_count", 0),
            "tags":   a.get("tag_list", [])
        })

    # Update brain with competitor intelligence
    brain["topic_intelligence"]["competitor_gaps"]   = gaps
    brain["topic_intelligence"]["trending_keywords"] = trending_tag_names
    brain["competitor_intel"] = {
        "last_updated":    datetime.now().strftime("%Y-%m-%d"),
        "title_patterns":  title_patterns,
        "top_topics":      top_topics,
        "trending_tags":   trending_tag_names
    }

    print(f"  ✅ Found {len(gaps)} content gaps")
    print(f"  ✅ Top power words: {list(title_patterns['top_power_words'].keys())[:5]}")
    print(f"  ✅ Trending tags: {trending_tag_names[:5]}")

    return brain
