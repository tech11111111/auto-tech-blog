"""
main.py
───────
Upgraded daily posting pipeline.
Uses ALL intelligence from brain.json:
- Viral scores from viral_detector.py
- Industry opportunities from industry_scanner.py  
- SEO gaps from seo_optimizer.py
- Keyword research from keyword_researcher.py
- Optimized titles from title_optimizer.py
- Past lessons from learner.py

Posts to Dev.to every day at 9AM.

ERROR HANDLING:
- Every step has try/except
- Fallbacks at every level
- Validates data before posting
- Never crashes silently
"""

import os
import re
import json
import base64
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Import our modules safely
try:
    from title_optimizer import optimize_title
    TITLE_OPTIMIZER_AVAILABLE = True
except ImportError:
    TITLE_OPTIMIZER_AVAILABLE = False
    print("⚠️ title_optimizer not found — using basic titles")

# ── API KEYS ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DEVTO_API_KEY  = os.environ.get("DEVTO_API_KEY", "")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not set in GitHub Secrets!")
if not DEVTO_API_KEY:
    raise ValueError("❌ DEVTO_API_KEY not set in GitHub Secrets!")

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

# ── DATE ──────────────────────────────────────────────────────────────────────
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
    """Gemini text generation with error handling"""
    try:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.8}
        }
        r = requests.post(GEMINI_TEXT_URL, json=body, timeout=90)
        r.raise_for_status()
        candidates = r.json().get("candidates", [])
        if candidates:
            return candidates[0]["content"]["parts"][0]["text"].strip()
        raise ValueError("No candidates in response")
    except Exception as e:
        print(f"  ⚠️ Gemini text error: {e}")
        raise


def load_brain():
    """Load brain with complete fallback"""
    try:
        if os.path.exists(BRAIN_FILE):
            with open(BRAIN_FILE) as f:
                return json.load(f)
    except Exception as e:
        print(f"  ⚠️ Brain load error: {e}")
    return {
        "identity":          {"blog_name": "TechPulse AI", "level": 1, "total_posts": 0},
        "writing_rules":     {"best_intro_style": "shocking fact", "best_word_count": 1200},
        "title_formulas":    {"click_patterns": ["Why", "How", "What"], "avoid": []},
        "topic_intelligence":{"hot_categories": ["AI", "cybersecurity"], "competitor_gaps": []},
        "daily_lessons":     [],
        "viral_predictions": {},
        "industry_intelligence": {},
        "seo_intelligence":  {},
        "keyword_research":  {}
    }


def load_memory():
    """Load memory with fallback"""
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


def save_brain(brain):
    try:
        brain["last_updated"] = TODAY
        with open(BRAIN_FILE, "w") as f:
            json.dump(brain, f, indent=2)
    except Exception as e:
        print(f"  ⚠️ Brain save error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Find Topics (Multi-Source)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_topics():
    """Fetch trending topics from multiple free sources"""
    print("🔍 Fetching trending topics...")
    topics = []

    # HackerNews
    try:
        r  = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        ids= r.json()[:30]
        for sid in ids[:15]:
            s = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=10
            ).json()
            if s and s.get("score", 0) > 30:
                topics.append({
                    "title":   s.get("title", ""),
                    "score":   s.get("score", 0),
                    "comments":s.get("descendants", 0),
                    "source":  "HackerNews"
                })
    except Exception as e:
        print(f"  ⚠️ HN error: {e}")

    # Dev.to trending
    try:
        r = requests.get("https://dev.to/api/articles?top=7&per_page=20", timeout=10)
        for a in r.json():
            topics.append({
                "title":   a.get("title", ""),
                "score":   a.get("positive_reactions_count", 0),
                "comments":a.get("comments_count", 0),
                "source":  "DevTo"
            })
    except Exception as e:
        print(f"  ⚠️ DevTo error: {e}")

    # Google Trends
    try:
        r    = requests.get(
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
            timeout=10
        )
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:10]:
            title   = item.findtext("title", "")
            traffic = item.findtext(
                "{https://trends.google.com/trends/trendingsearches/daily}approx_traffic", "0"
            )
            traffic_num = int(traffic.replace(",", "").replace("+", "")) if traffic else 0
            topics.append({"title": title, "score": traffic_num, "comments": 0, "source": "GoogleTrends"})
    except Exception as e:
        print(f"  ⚠️ Google Trends error: {e}")

    topics.sort(key=lambda x: x["score"] + x["comments"], reverse=True)
    print(f"  ✅ Found {len(topics)} topics")
    return topics[:25]


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Pick Best Topic Using Full Brain Intelligence
# ─────────────────────────────────────────────────────────────────────────────
def pick_best_topic(topics, brain, memory):
    """Pick best topic using ALL brain intelligence"""
    print("🧠 Picking best topic using brain intelligence...")

    past_titles  = [p["title"] for p in memory.get("posts", [])[-30:]]
    lessons      = brain.get("daily_lessons", [])[-10:]
    viral_pred   = brain.get("viral_predictions", {})
    industry_intel= brain.get("industry_intelligence", {})
    seo_intel    = brain.get("seo_intelligence", {})
    kw_intel     = brain.get("keyword_research", {})
    level        = brain.get("identity", {}).get("level", 1)

    # Get all intelligence
    viral_best   = viral_pred.get("best_topic", "")
    industry_best= industry_intel.get("best_opportunity", "")
    seo_gaps     = [g.get("gap", "") for g in seo_intel.get("gaps", [])[:3]]
    best_keyword = kw_intel.get("best_keyword_today", "")
    hot_industries= brain.get("topic_intelligence", {}).get("hot_industries", [])

    topics_text  = "\n".join([
        f"{i+1}. [{t['source']}] {t['title']} (score:{t['score']} comments:{t['comments']})"
        for i, t in enumerate(topics)
    ])

    prompt = f"""You are an expert viral content strategist. Today is {TODAY}. Year: {CURRENT_YEAR}.

Blog level: {level}/10 — Think like a growth hacker.

TRENDING TOPICS RIGHT NOW:
{topics_text}

BRAIN INTELLIGENCE (use ALL of this):
- Viral prediction for today: {viral_best}
- Best industry opportunity: {industry_best}
- SEO gaps to exploit: {seo_gaps}
- Best keyword to target: {best_keyword}
- Hot industries today: {hot_industries}
- Lessons learned: {lessons[-5:] if lessons else 'None yet'}

PAST POSTS (NEVER repeat similar topics):
{chr(10).join(past_titles[-20:]) if past_titles else "None yet"}

SELECTION RULES:
1. Topic must have BOTH viral AND SEO potential
2. Can be ANY industry where tech is involved
3. Must be unique — nobody else writing about this angle
4. Must include year {CURRENT_YEAR} in title
5. Viral score must be 7+ to qualify
6. Prefer topics that affect many people's lives

Respond ONLY in valid JSON, no markdown:
{{
  "blog_title": "viral SEO title with {CURRENT_YEAR}",
  "topic_summary": "what this post is about in 1 sentence",
  "industry": "CoreTech|MedTech|AgriTech|EdTech|FinTech|SpaceTech|other",
  "viral_score": 8.5,
  "seo_score": 8.0,
  "target_audience": "specific audience who will read and share",
  "estimated_length": "short|medium|long",
  "focus_keyword": "main SEO keyword phrase",
  "secondary_keywords": ["kw1", "kw2", "kw3"],
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "affiliate_opportunity": "amazon|coursera|udemy|nordvpn|hostinger|none",
  "unique_angle": "what makes this post different from all others",
  "why_viral": "why this will spread"
}}"""

    try:
        raw    = gemini_text(prompt, max_tokens=700)
        raw    = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)

        # Optimize title further
        if TITLE_OPTIMIZER_AVAILABLE and result.get("blog_title"):
            try:
                winner, _ = optimize_title(
                    result["blog_title"],
                    result.get("focus_keyword", ""),
                    result.get("industry", "tech"),
                    brain
                )
                result["blog_title"] = winner
            except Exception as e:
                print(f"  ⚠️ Title optimizer error: {e}")

        print(f"  ✅ Chosen: {result['blog_title']}")
        print(f"  🔥 Viral: {result.get('viral_score', 'N/A')} | SEO: {result.get('seo_score', 'N/A')}")
        print(f"  🌍 Industry: {result.get('industry', 'N/A')}")
        return result

    except Exception as e:
        print(f"  ⚠️ Topic selection error: {e}")
        # Fallback topic
        return {
            "blog_title":        f"Top AI Developments You Need to Know in {CURRENT_YEAR}",
            "industry":          "CoreTech",
            "viral_score":       7.0,
            "seo_score":         7.0,
            "target_audience":   "tech enthusiasts",
            "estimated_length":  "medium",
            "focus_keyword":     f"AI developments {CURRENT_YEAR}",
            "secondary_keywords":["artificial intelligence", "tech trends", "AI news"],
            "tags":              ["ai", "technology", "programming", "webdev"],
            "affiliate_opportunity": "coursera",
            "unique_angle":      "comprehensive overview",
            "why_viral":         "AI is always trending"
        }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Write Full Blog Post
# ─────────────────────────────────────────────────────────────────────────────
def write_blog(topic_info, brain):
    """Write complete blog post using brain's writing rules"""
    print("✍️  Writing full blog post...")

    rules        = brain.get("writing_rules", {})
    length_map   = {"short": "700-900 words", "medium": "1200-1600 words", "long": "2000-2800 words"}
    length       = length_map.get(topic_info.get("estimated_length", "medium"), "1200-1600 words")
    intro_style  = rules.get("best_intro_style", "start with a shocking fact or statistic")
    avoid        = rules.get("avoid_phrases", ["In conclusion", "It is worth noting", "Delve into"])
    power_words  = rules.get("power_words", ["secretly", "finally", "exposed", "truth"])
    structure    = rules.get("best_structure", "hook + problem + solution + examples + FAQ + CTA")
    lessons      = brain.get("daily_lessons", [])[-5:]
    seo_gaps     = brain.get("seo_intelligence", {}).get("gaps", [])[:2]

    affiliate    = topic_info.get("affiliate_opportunity", "none")
    aff_url      = AFFILIATE_LINKS.get(affiliate, "")
    aff_note     = f"Naturally include ONE affiliate mention for {affiliate} ({aff_url}) where relevant." if aff_url and affiliate != "none" else ""

    prompt = f"""Write a complete VIRAL high-quality blog post in Markdown.

TODAY: {TODAY} | YEAR: {CURRENT_YEAR}
⚠️ CRITICAL: Always use {CURRENT_YEAR} for any year references. NEVER use 2024 or older as current year.

TITLE: {topic_info['blog_title']}
INDUSTRY: {topic_info.get('industry', 'tech')}
FOCUS KEYWORD: {topic_info['focus_keyword']}
SECONDARY KEYWORDS: {', '.join(topic_info.get('secondary_keywords', []))}
AUDIENCE: {topic_info.get('target_audience', 'tech enthusiasts')}
UNIQUE ANGLE: {topic_info.get('unique_angle', '')}
LENGTH: {length}

WRITING RULES FROM BRAIN (FOLLOW STRICTLY):
- Intro style: {intro_style}
- Structure: {structure}
- Use power words naturally: {power_words}
- NEVER use: {avoid}
- SEO gaps to address: {[g.get('gap', '') for g in seo_gaps]}

STRUCTURE (follow exactly):
1. HOOK: {intro_style} — grab reader in first 2 sentences
2. ## Why This Matters (establish stakes)
3. ## [Section using secondary keyword 1]
4. ## [Section using secondary keyword 2]
5. ## [Section using secondary keyword 3]
6. ## Real World Examples (make it concrete)
7. ## Key Takeaways (5 bullet points)
8. ## Frequently Asked Questions
   - 5 questions people actually Google
   - Direct clear answers (helps AI search engines cite us)
9. ## What This Means For You (conclusion + strong CTA)

SEO RULES:
- Use focus keyword in first 100 words naturally
- Use {CURRENT_YEAR} for ALL year references
- Write for humans first, Google second
- Every section should be skimmable

{aff_note}

LESSONS FROM PAST POSTS:
{chr(10).join(lessons) if lessons else "First post — write best possible content"}

⚠️ Do NOT include title at top. No author info. Pure Markdown only."""

    try:
        content = gemini_text(prompt, max_tokens=3500)
        print(f"  ✅ Written ({len(content.split())} words)")
        return content
    except Exception as e:
        print(f"  ⚠️ Blog writing error: {e}")
        # Emergency fallback content
        return f"""Technology is evolving faster than ever in {CURRENT_YEAR}.

## What's Happening

The tech landscape continues to transform across industries.

## Why It Matters

Understanding these changes helps you stay ahead.

## Key Takeaways

- Technology affects every industry
- Staying informed is crucial
- Early adopters win

## Frequently Asked Questions

**What is the biggest tech trend?**
AI continues to dominate across all sectors.

## Conclusion

Stay curious and keep learning. Follow TechPulse AI for daily updates."""


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Humanize Content
# ─────────────────────────────────────────────────────────────────────────────
def humanize_blog(content, brain):
    """Remove AI tone, make it sound human"""
    print("🧑 Humanizing content...")

    avoid = brain.get("writing_rules", {}).get(
        "avoid_phrases",
        ["In conclusion", "It is worth noting", "Delve into", "Furthermore", "Moreover"]
    )
    voice = brain.get("identity", {}).get("voice", "confident, witty, knowledgeable")

    prompt = f"""Rewrite this tech blog to sound like a real human expert wrote it.

TODAY: {TODAY} | YEAR: {CURRENT_YEAR}
VOICE: {voice}

RULES:
- Remove ALL robotic phrases: {avoid}
- Use natural conversational transitions
- Add personality, real opinions, occasional humor
- If ANY year older than {CURRENT_YEAR} used as "current" — fix it to {CURRENT_YEAR}
- Keep ALL Markdown formatting (##, ###, bullets, bold)
- Keep FAQ section intact
- Keep all sections — do NOT remove content
- Target length: same as input

BLOG:
{content}"""

    try:
        humanized = gemini_text(prompt, max_tokens=3500)
        print("  ✅ Humanized")
        return humanized
    except Exception as e:
        print(f"  ⚠️ Humanize error: {e}")
        return content  # Return original if humanize fails


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Generate Cover Image
# ─────────────────────────────────────────────────────────────────────────────
def generate_cover_image(topic_info):
    """Generate AI cover image for blog post"""
    print("🖼️  Generating cover image...")
    try:
        industry = topic_info.get("industry", "tech")
        style_map = {
            "MedTech":  "medical technology, blue and white, clean",
            "AgriTech": "agricultural technology, green and gold",
            "FinTech":  "financial technology, gold and dark blue",
            "SpaceTech":"space technology, dark with stars and blue",
            "CoreTech": "technology, dark background cyan accents futuristic"
        }
        style     = style_map.get(industry, "technology, dark background blue accents futuristic")
        img_prompt= f"Professional tech blog cover image about: {topic_info['blog_title']}. Style: {style}. Modern minimal design. No text."

        body = {
            "instances":  [{"prompt": img_prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": "16:9"}
        }
        r = requests.post(GEMINI_IMAGE_URL, json=body, timeout=90)

        if r.status_code == 200:
            predictions = r.json().get("predictions", [])
            if predictions:
                img_data = predictions[0].get("bytesBase64Encoded", "")
                if img_data:
                    img_path = "cover_image.png"
                    with open(img_path, "wb") as f:
                        f.write(base64.b64decode(img_data))
                    print("  ✅ Image generated")
                    return img_path
        print(f"  ⚠️ Image generation failed: {r.status_code}")
        return None
    except Exception as e:
        print(f"  ⚠️ Image error: {e}")
        return None


def upload_image_to_devto(img_path):
    """Upload image to Dev.to"""
    if not img_path or not os.path.exists(img_path):
        return None
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
            if url:
                print(f"  ✅ Image uploaded")
                return url
    except Exception as e:
        print(f"  ⚠️ Upload error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Publish to Dev.to
# ─────────────────────────────────────────────────────────────────────────────
def publish_to_devto(topic_info, content, image_url=None):
    """Publish blog post to Dev.to"""
    print("🚀 Publishing to Dev.to...")

    if image_url:
        content = f"![Cover Image]({image_url})\n\n{content}"

    # Clean and validate tags
    raw_tags  = topic_info.get("tags", ["tech"])
    clean_tags= []
    for tag i
