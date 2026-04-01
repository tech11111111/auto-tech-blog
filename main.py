"""
main.py
───────
Runs every morning at 9AM.
Reads brain.json to know what works.
Finds today's viral topic.
Writes, humanizes, and publishes the best possible blog post.
Gets better every single day.
"""

import os
import re
import json
import base64
import requests
import xml.etree.ElementTree as ET
from datetime import datetime


# ── API KEYS ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DEVTO_API_KEY  = os.environ["DEVTO_API_KEY"]

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────
GEMINI_TEXT_URL  = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
GEMINI_IMAGE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={GEMINI_API_KEY}"

# ── AFFILIATE LINKS ───────────────────────────────────────────────────────────
AFFILIATE_LINKS = {
    "amazon":    "https://amzn.to/YOUR_AFFILIATE_ID",
    "hostinger": "https://www.hostinger.com/?ref=YOUR_ID",
    "coursera":  "https://www.coursera.org/?ref=YOUR_ID",
    "udemy":     "https://www.udemy.com/?ref=YOUR_ID",
    "nordvpn":   "https://nordvpn.com/?ref=YOUR_ID",
}

# ── DATE (always current) ─────────────────────────────────────────────────────
TODAY         = datetime.now().strftime("%B %d, %Y")
CURRENT_YEAR  = datetime.now().strftime("%Y")
CURRENT_MONTH = datetime.now().strftime("%B %Y")

# ── FILES ─────────────────────────────────────────────────────────────────────
BRAIN_FILE  = "brain.json"
MEMORY_FILE = "memory.json"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def gemini_text(prompt, max_tokens=3000):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.8}
    }
    r = requests.post(GEMINI_TEXT_URL, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def load_brain():
    if os.path.exists(BRAIN_FILE):
        with open(BRAIN_FILE) as f:
            return json.load(f)
    return {}


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {"posts": []}


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Find Viral Topics (All Free)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_hackernews():
    print("  📡 Hacker News...")
    topics = []
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10
        ).json()[:30]
        for sid in ids[:15]:
            s = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=10
            ).json()
            if s and s.get("score", 0) > 50:
                topics.append({
                    "title":   s.get("title", ""),
                    "score":   s.get("score", 0),
                    "comments":s.get("descendants", 0),
                    "source":  "HackerNews"
                })
    except Exception as e:
        print(f"    ⚠️ {e}")
    return topics


def fetch_devto_trending():
    print("  📡 Dev.to trending...")
    topics = []
    try:
        articles = requests.get(
            "https://dev.to/api/articles?top=7&per_page=20", timeout=10
        ).json()
        for a in articles:
            topics.append({
                "title":    a.get("title", ""),
                "score":    a.get("positive_reactions_count", 0),
                "comments": a.get("comments_count", 0),
                "source":   "DevTo"
            })
    except Exception as e:
        print(f"    ⚠️ {e}")
    return topics


def fetch_google_trends():
    print("  📡 Google Trends...")
    topics = []
    try:
        r    = requests.get(
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
            timeout=10
        )
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:15]:
            title   = item.findtext("title", "")
            traffic = item.findtext(
                "{https://trends.google.com/trends/trendingsearches/daily}approx_traffic", "0"
            )
            traffic_num = int(traffic.replace(",", "").replace("+", "")) if traffic else 0
            topics.append({
                "title":    title,
                "score":    traffic_num,
                "comments": 0,
                "source":   "GoogleTrends"
            })
    except Exception as e:
        print(f"    ⚠️ {e}")
    return topics


def fetch_all_topics():
    print("🔍 Fetching trending topics...")
    all_topics = fetch_hackernews() + fetch_devto_trending() + fetch_google_trends()

    tech_keywords = [
        "ai", "artificial intelligence", "machine learning", "cyber", "security",
        "software", "hardware", "app", "tech", "code", "programming", "data",
        "cloud", "robot", "gpu", "chip", "llm", "model", "open source", "hack",
        "privacy", "google", "microsoft", "apple", "linux", "python", "api",
        "neural", "gpt", "android", "ios", "startup", "crypto", "quantum"
    ]

    tech    = [t for t in all_topics if any(k in t["title"].lower() for k in tech_keywords)]
    final   = tech if len(tech) >= 5 else all_topics
    final.sort(key=lambda x: x["score"] + x["comments"], reverse=True)
    print(f"  ✅ Found {len(final)} trending topics")
    return final[:25]


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — AI Picks Best Topic Using Brain Intelligence
# ─────────────────────────────────────────────────────────────────────────────
def pick_best_topic(topics, brain, memory):
    print("🧠 AI selecting best topic using brain intelligence...")

    past_titles   = [p["title"] for p in memory.get("posts", [])[-30:]]
    lessons       = brain.get("daily_lessons", [])[-10:]
    hot_cats      = brain.get("topic_intelligence", {}).get("hot_categories", [])
    cold_cats     = brain.get("topic_intelligence", {}).get("cold_categories", [])
    gaps          = brain.get("topic_intelligence", {}).get("competitor_gaps", [])
    title_formula = brain.get("title_formulas", {}).get("best_performing", "")
    growth_tactic = brain.get("growth_strategy", {}).get("growth_tactics", [])
    level         = brain.get("identity", {}).get("level", 1)

    topics_text   = "\n".join([
        f"{i+1}. [{t['source']}] {t['title']} (score:{t['score']} comments:{t['comments']})"
        for i, t in enumerate(topics)
    ])

    prompt = f"""You are an expert tech blog growth strategist AI. Today is {TODAY}. Current year: {CURRENT_YEAR}.

You manage a tech blog at Level {level}/10. Your job is to pick today's BEST topic to maximize views and growth.

TRENDING TOPICS RIGHT NOW:
{topics_text}

BRAIN INTELLIGENCE (use this to make smart decisions):
- Hot categories performing well: {hot_cats}
- Cold categories to avoid: {cold_cats}
- Competitor content gaps (opportunities): {gaps}
- Best title formula that works: {title_formula}
- Growth tactics: {growth_tactic}

PAST POSTS (DO NOT repeat):
{chr(10).join(past_titles) if past_titles else "None yet"}

LESSONS FROM PAST PERFORMANCE:
{chr(10).join(lessons) if lessons else "None yet"}

RULES:
- ALWAYS use {CURRENT_YEAR} in the title, never older years
- Never pick a topic similar to past posts
- Exploit competitor gaps when possible
- Apply all lessons learned
- Pick for maximum Google search traffic potential

Respond ONLY in valid JSON, no markdown:
{{
  "blog_title": "SEO title with {CURRENT_YEAR}",
  "reason": "why this will get maximum views",
  "target_audience": "specific audience",
  "estimated_length": "short|medium|long",
  "focus_keyword": "main SEO keyword",
  "secondary_keywords": ["kw1", "kw2", "kw3"],
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "affiliate_opportunity": "amazon|coursera|udemy|nordvpn|hostinger|none",
  "competitor_gap_exploited": "what gap we are filling or none"
}}"""

    raw    = gemini_text(prompt, max_tokens=600)
    raw    = re.sub(r"```json|```", "", raw).strip()
    result = json.loads(raw)
    print(f"  ✅ Chosen: {result['blog_title']}")
    print(f"  💡 Gap exploited: {result.get('competitor_gap_exploited', 'none')}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Write Blog Using Brain's Writing Rules
# ─────────────────────────────────────────────────────────────────────────────
def write_blog(topic_info, brain):
    print("✍️  Writing blog using brain's writing rules...")

    # Get writing rules from brain
    rules        = brain.get("writing_rules", {})
    length_map   = {"short": "700-900 words", "medium": "1200-1600 words", "long": "2000-2800 words"}
    length       = length_map.get(topic_info["estimated_length"], "1200-1600 words")
    intro_style  = rules.get("best_intro_style", "start with a shocking fact")
    avoid        = rules.get("avoid_phrases", [])
    power_words  = rules.get("power_words", [])
    structure    = rules.get("best_structure", "hook + problem + solution + FAQ + CTA")
    lessons      = brain.get("daily_lessons", [])[-5:]

    # Affiliate
    affiliate    = topic_info.get("affiliate_opportunity", "none")
    aff_url      = AFFILIATE_LINKS.get(affiliate, "")
    aff_note     = f"Naturally include ONE affiliate recommendation for {affiliate} ({aff_url})." if aff_url and affiliate != "none" else ""

    prompt = f"""Write a complete high-quality tech blog post in Markdown.

TODAY: {TODAY} | YEAR: {CURRENT_YEAR}
IMPORTANT: Always reference {CURRENT_YEAR} for current stats/trends. NEVER use 2024 or older as current.

TITLE: {topic_info['blog_title']}
FOCUS KEYWORD: {topic_info['focus_keyword']}
SECONDARY KEYWORDS: {', '.join(topic_info['secondary_keywords'])}
AUDIENCE: {topic_info['target_audience']}
LENGTH: {length}

WRITING RULES FROM BRAIN (follow strictly):
- Intro style: {intro_style}
- Structure: {structure}
- Use power words naturally: {power_words}
- NEVER use these phrases: {avoid}

STRUCTURE (use exactly):
- Introduction: {intro_style}
- ## Section 1 (use secondary keyword)
- ## Section 2
- ## Section 3
- ## Section 4 (if long post)
- ## Key Takeaways (5 bullet points)
- ## Frequently Asked Questions
  (4 questions people search on Google with direct answers)
- ## Conclusion (strong CTA to follow the blog)

SEO RULES:
- Use focus keyword in first 100 words
- Use {CURRENT_YEAR} for any year references
- Write for humans first, Google second

{aff_note}

LESSONS FROM PAST POSTS TO APPLY:
{chr(10).join(lessons) if lessons else "None yet - write best possible post"}

Do NOT include title at top. No author info. Markdown only."""

    content = gemini_text(prompt, max_tokens=3500)
    print(f"  ✅ Written ({len(content.split())} words)")
    return content


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Humanize Content
# ─────────────────────────────────────────────────────────────────────────────
def humanize_blog(content, brain):
    print("🧑 Humanizing content...")

    avoid   = brain.get("writing_rules", {}).get("avoid_phrases", [])
    voice   = brain.get("identity", {}).get("voice", "confident, witty, expert")

    prompt = f"""Rewrite this tech blog to sound like a real human expert wrote it.

TODAY: {TODAY} | CURRENT YEAR: {CURRENT_YEAR}
VOICE: {voice}

RULES:
- Remove ALL robotic AI phrases: {avoid}
- Also remove: "In conclusion", "It is worth noting", "Delve into", "Furthermore", "Moreover"
- Use natural conversational transitions
- Add personality, opinions, light humor
- If any year older than {CURRENT_YEAR} is used as "current" — update it to {CURRENT_YEAR}
- Keep ALL Markdown formatting (##, ###, bullets, bold)
- Keep FAQ section exactly as is
- Do NOT remove any sections

BLOG:
{content}"""

    humanized = gemini_text(prompt, max_tokens=3500)
    print("  ✅ Humanized")
    return humanized


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Generate Cover Image
# ─────────────────────────────────────────────────────────────────────────────
def generate_cover_image(topic_info):
    print("🖼️  Generating cover image...")
    try:
        img_prompt = f"Professional tech blog cover image about {topic_info['blog_title']}. Modern clean digital art, dark background with blue and cyan accents, futuristic minimal style. No text overlay."
        body = {
            "instances":  [{"prompt": img_prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": "16:9"}
        }
        r = requests.post(GEMINI_IMAGE_URL, json=body, timeout=60)
        if r.status_code == 200:
            img_data  = r.json()["predictions"][0]["bytesBase64Encoded"]
            img_path  = "cover_image.png"
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(img_data))
            print("  ✅ Image generated")
            return img_path
        else:
            print(f"  ⚠️ Image failed: {r.status_code}")
            return None
    except Exception as e:
        print(f"  ⚠️ Image error: {e}")
        return None


def upload_image_to_devto(img_path):
    print("  📤 Uploading image...")
    try:
        with open(img_path, "rb") as f:
            r = requests.post(
                "https://dev.to/api/images",
                headers={"api-key": DEVTO_API_KEY},
                files={"image": ("cover.png", f, "image/png")},
                timeout=30
            )
        if r.status_code == 200:
            url = r.json().get("url", "")
            print(f"  ✅ Image uploaded")
            return url
    except Exception as e:
        print(f"  ⚠️ Upload error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Publish to Dev.to
# ─────────────────────────────────────────────────────────────────────────────
def publish_to_devto(topic_info, content, image_url=None):
    print("🚀 Publishing to Dev.to...")

    if image_url:
        content = f"![Cover Image]({image_url})\n\n{content}"

    tags    = [t.lower().replace(" ", "")[:30] for t in topic_info.get("tags", [])][:4]

    payload = {
        "article": {
            "title":         topic_info["blog_title"],
            "body_markdown": content,
            "published":     True,
            "tags":          tags,
            "description":   f"{topic_info['focus_keyword']} — {topic_info['blog_title']}"
        }
    }
    if image_url:
        payload["article"]["main_image"] = image_url

    r = requests.post(
        "https://dev.to/api/articles",
        json=payload,
        headers={"api-key": DEVTO_API_KEY, "Content-Type": "application/json"},
        timeout=30
    )

    if r.status_code in (200, 201):
        data = r.json()
        print(f"  ✅ Published! → {data.get('url', '')}")
        return data.get("url", ""), data.get("id", "")
    else:
        raise Exception(f"Dev.to publish failed: {r.status_code} — {r.text}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Save Post to Memory
# ─────────────────────────────────────────────────────────────────────────────
def save_post(memory, topic_info, url, article_id, content):
    memory["posts"].append({
        "date":        TODAY,
        "title":       topic_info["blog_title"],
        "url":         url,
        "article_id":  article_id,
        "tags":        topic_info.get("tags", []),
        "length":      topic_info.get("estimated_length", "medium"),
        "word_count":  len(content.split()),
        "views":       0,
        "likes":       0,
        "comments":    0,
        "performance": "pending",
        "gap_exploited": topic_info.get("competitor_gap_exploited", "none")
    })
    save_memory(memory)
    print("  ✅ Saved to memory")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  🤖 AutoBlog AI — {TODAY}")
    print("="*60 + "\n")

    brain  = load_brain()
    memory = load_memory()

    level = brain.get("identity", {}).get("level", 1)
    print(f"  🧠 Brain Level: {level}/10")
    print(f"  📚 Lessons loaded: {len(brain.get('daily_lessons', []))}")
    print(f"  📝 Past posts: {len(memory.get('posts', []))}\n")

    # Pipeline
    topics     = fetch_all_topics()
    topic_info = pick_best_topic(topics, brain, memory)
    content    = write_blog(topic_info, brain)
    content    = humanize_blog(content, brain)
    img_path   = generate_cover_image(topic_info)
    image_url  = upload_image_to_devto(img_path) if img_path else None
    url, aid   = publish_to_devto(topic_info, content, image_url)
    save_post(memory, topic_info, url, aid, content)

    print("\n" + "="*60)
    print("  🎉 SUCCESS!")
    print(f"  📝 {topic_info['blog_title']}")
    print(f"  🔗 {url}")
    print(f"  📊 Total posts: {len(memory['posts'])}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
                                     
