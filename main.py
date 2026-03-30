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

# ── GEMINI ENDPOINTS ──────────────────────────────────────────────────────────
GEMINI_TEXT_URL  = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
GEMINI_IMAGE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={GEMINI_API_KEY}"

# ── AFFILIATE LINKS (add your own links here) ─────────────────────────────────
AFFILIATE_LINKS = {
    "amazon":   "https://amzn.to/YOUR_AFFILIATE_ID",
    "hostinger":"https://www.hostinger.com/?ref=YOUR_ID",
    "coursera": "https://www.coursera.org/?ref=YOUR_ID",
    "udemy":    "https://www.udemy.com/?ref=YOUR_ID",
    "nordvpn":  "https://nordvpn.com/?ref=YOUR_ID",
}

MEMORY_FILE = "memory.json"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def gemini_text(prompt, max_tokens=3000):
    """Call Gemini text generation"""
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.8}
    }
    r = requests.post(GEMINI_TEXT_URL, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def load_memory():
    """Load memory file (history of past posts)"""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"posts": [], "lessons": [], "best_tags": [], "avg_performance": 0}


def save_memory(memory):
    """Save memory file"""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Find Viral Topics (All Free, No API Key)
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
                    "title": s.get("title", ""),
                    "score": s.get("score", 0),
                    "comments": s.get("descendants", 0),
                    "source": "HackerNews"
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
                "title": a.get("title", ""),
                "score": a.get("positive_reactions_count", 0),
                "comments": a.get("comments_count", 0),
                "source": "DevTo"
            })
    except Exception as e:
        print(f"    ⚠️ {e}")
    return topics


def fetch_google_trends():
    print("  📡 Google Trends...")
    topics = []
    try:
        r = requests.get(
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
            timeout=10
        )
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:15]:
            title = item.findtext("title", "")
            traffic = item.findtext(
                "{https://trends.google.com/trends/trendingsearches/daily}approx_traffic", "0"
            )
            traffic_num = int(traffic.replace(",", "").replace("+", "")) if traffic else 0
            topics.append({
                "title": title,
                "score": traffic_num,
                "comments": 0,
                "source": "GoogleTrends"
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

    tech = [t for t in all_topics if any(k in t["title"].lower() for k in tech_keywords)]
    final = tech if len(tech) >= 5 else all_topics
    final.sort(key=lambda x: x["score"] + x["comments"], reverse=True)
    print(f"  ✅ Found {len(final)} trending topics")
    return final[:25]


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — AI Picks Best Topic (avoids repeats, learns from history)
# ─────────────────────────────────────────────────────────────────────────────
def pick_best_topic(topics, memory):
    print("🧠 AI selecting best topic...")

    past_titles = [p["title"] for p in memory.get("posts", [])[-30:]]
    lessons     = memory.get("lessons", [])[-5:]
    best_tags   = memory.get("best_tags", [])

    topics_text  = "\n".join([
        f"{i+1}. [{t['source']}] {t['title']} (score:{t['score']} comments:{t['comments']})"
        for i, t in enumerate(topics)
    ])
    past_text    = "\n".join(past_titles) if past_titles else "None yet"
    lessons_text = "\n".join(lessons) if lessons else "None yet"
    tags_text    = ", ".join(best_tags) if best_tags else "None yet"

    prompt = f"""You are a tech blog strategist. Pick the SINGLE best topic to write about today.

Niches: AI & Machine Learning, Cybersecurity, Software, Hardware

Trending topics:
{topics_text}

Already posted (DO NOT repeat these):
{past_text}

Lessons learned from past performance:
{lessons_text}

Best performing tags so far:
{tags_text}

Rules:
- Never pick a topic similar to already posted ones
- Apply lessons learned
- Pick topic with broad appeal and Google search potential
- Must fit our tech niches

Respond ONLY in valid JSON, no markdown:
{{
  "blog_title": "SEO optimized title with current year",
  "reason": "why this topic will perform well",
  "target_audience": "who will read this",
  "estimated_length": "short|medium|long",
  "focus_keyword": "main SEO keyword",
  "secondary_keywords": ["kw1", "kw2", "kw3"],
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "affiliate_opportunity": "amazon|coursera|udemy|nordvpn|hostinger|none"
}}"""

    raw    = gemini_text(prompt, max_tokens=600)
    raw    = re.sub(r"```json|```", "", raw).strip()
    result = json.loads(raw)
    print(f"  ✅ Chosen: {result['blog_title']}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Write Full Blog Post
# ─────────────────────────────────────────────────────────────────────────────
def write_blog(topic_info, memory):
    print("✍️  Writing full blog post...")

    length_guide = {"short": "700–900 words", "medium": "1200–1600 words", "long": "2000–2800 words"}
    length       = length_guide.get(topic_info["estimated_length"], "1200–1600 words")
    lessons      = "\n".join(memory.get("lessons", [])[-3:]) or "None yet"
    affiliate    = topic_info.get("affiliate_opportunity", "none")
    aff_url      = AFFILIATE_LINKS.get(affiliate, "")
    aff_note     = f"Naturally include ONE affiliate recommendation for {affiliate} ({aff_url}) where relevant." if aff_url and affiliate != "none" else ""

    prompt = f"""Write a complete high-quality tech blog post in Markdown.

Title: {topic_info['blog_title']}
Focus keyword: {topic_info['focus_keyword']}
Secondary keywords: {', '.join(topic_info['secondary_keywords'])}
Target audience: {topic_info['target_audience']}
Length: {length}

Structure (use exactly):
- Hook introduction (first paragraph must answer: what is this and why should I care)
- ## Section 1
- ## Section 2  
- ## Section 3
- ## Section 4 (if long)
- ## Key Takeaways (bullet points)
- ## Frequently Asked Questions
  - 4 questions people actually search on Google
  - Direct clear answers (this helps AI search engines cite us)
- ## Conclusion (strong CTA)

SEO rules:
- Use focus keyword naturally in first 100 words
- Use secondary keywords in subheadings
- Write for humans first, Google second

{aff_note}

Lessons from past posts to apply:
{lessons}

Do NOT include the title at top. No author info. Markdown only."""

    content = gemini_text(prompt, max_tokens=3500)
    print(f"  ✅ Written ({len(content.split())} words)")
    return content


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Humanize
# ─────────────────────────────────────────────────────────────────────────────
def humanize_blog(content):
    print("🧑 Humanizing content...")

    prompt = f"""Rewrite this tech blog to sound like a real experienced human tech journalist.

Rules:
- Remove robotic phrases: "In conclusion", "It's worth noting", "Delve into", "Importantly", "Furthermore"
- Use natural transitions and conversational tone
- Add personality, real opinions, light humor where appropriate
- Keep ALL Markdown formatting (##, ###, bullet points, bold)
- Keep the FAQ section exactly as is
- Do NOT remove any sections or change meaning

Blog:
{content}"""

    humanized = gemini_text(prompt, max_tokens=3500)
    print("  ✅ Humanized")
    return humanized


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Generate Cover Image with Gemini
# ─────────────────────────────────────────────────────────────────────────────
def generate_cover_image(topic_info):
    print("🖼️  Generating cover image...")
    try:
        image_prompt = f"Professional tech blog cover image about {topic_info['blog_title']}. Modern, clean, digital art style, dark background with blue and purple accents, futuristic feel. No text."

        body = {
            "instances": [{"prompt": image_prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": "16:9"}
        }

        r = requests.post(GEMINI_IMAGE_URL, json=body, timeout=60)

        if r.status_code == 200:
            img_data    = r.json()["predictions"][0]["bytesBase64Encoded"]
            img_bytes   = base64.b64decode(img_data)
            img_path    = "cover_image.png"
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            print("  ✅ Image generated")
            return img_path
        else:
            print(f"  ⚠️ Image generation failed: {r.status_code}")
            return None
    except Exception as e:
        print(f"  ⚠️ Image error: {e}")
        return None


def upload_image_to_devto(img_path):
    """Upload image to Dev.to and get URL"""
    print("  📤 Uploading image to Dev.to...")
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
            print(f"  ✅ Image uploaded: {url}")
            return url
    except Exception as e:
        print(f"  ⚠️ Upload error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Publish to Dev.to
# ─────────────────────────────────────────────────────────────────────────────
def publish_to_devto(topic_info, content, image_url=None):
    print("🚀 Publishing to Dev.to...")

    # Add cover image at top of content
    if image_url:
        content = f"![Cover Image]({image_url})\n\n{content}"

    tags = [t.lower().replace(" ", "")[:30] for t in topic_info.get("tags", [])][:4]

    payload = {
        "article": {
            "title":         topic_info["blog_title"],
            "body_markdown": content,
            "published":     True,
            "tags":          tags,
            "description":   f"{topic_info['blog_title']} — {topic_info['focus_keyword']}",
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
        url  = data.get("url", "")
        id_  = data.get("id", "")
        print(f"  ✅ Published! → {url}")
        return url, id_
    else:
        raise Exception(f"Dev.to publish failed: {r.status_code} — {r.text}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Save to Memory
# ─────────────────────────────────────────────────────────────────────────────
def save_post_to_memory(memory, topic_info, url, article_id, content):
    memory["posts"].append({
        "date":       datetime.now().strftime("%Y-%m-%d"),
        "title":      topic_info["blog_title"],
        "url":        url,
        "article_id": article_id,
        "tags":       topic_info.get("tags", []),
        "length":     topic_info.get("estimated_length", "medium"),
        "word_count": len(content.split()),
        "views":      0,
        "likes":      0,
        "comments":   0,
        "performance": "pending"
    })
    save_memory(memory)
    print("  ✅ Saved to memory")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Check Yesterday's Performance & Learn
# ─────────────────────────────────────────────────────────────────────────────
def check_and_learn(memory):
    print("📊 Checking past performance & learning...")

    posts = memory.get("posts", [])
    if not posts:
        print("  ℹ️  No past posts yet")
        return memory

    # Check last 5 posts performance from Dev.to
    for post in posts[-5:]:
        article_id = post.get("article_id")
        if not article_id or post.get("performance") == "analyzed":
            continue
        try:
            r = requests.get(
                f"https://dev.to/api/articles/{article_id}",
                headers={"api-key": DEVTO_API_KEY},
                timeout=10
            )
            if r.status_code == 200:
                data            = r.json()
                post["views"]   = data.get("page_views_count", 0)
                post["likes"]   = data.get("positive_reactions_count", 0)
                post["comments"]= data.get("comments_count", 0)

                # Score performance
                score = post["views"] + (post["likes"] * 10) + (post["comments"] * 5)
                if score > 500:
                    post["performance"] = "high"
                elif score > 100:
                    post["performance"] = "medium"
                else:
                    post["performance"] = "low"
        except Exception as e:
            print(f"  ⚠️ Could not fetch stats: {e}")

    # AI analyzes performance and generates lessons
    if len(posts) >= 2:
        posts_summary = json.dumps([{
            "title":       p["title"],
            "tags":        p["tags"],
            "length":      p["length"],
            "views":       p["views"],
            "likes":       p["likes"],
            "performance": p["performance"]
        } for p in posts[-10:]], indent=2)

        prompt = f"""You are a blog performance analyst. Analyze these past blog posts and generate actionable lessons.

Past posts performance:
{posts_summary}

Analyze and respond ONLY in valid JSON, no markdown:
{{
  "pros": ["what worked well - be specific"],
  "cons": ["what did not work - be specific"],
  "lessons": ["actionable lesson 1", "actionable lesson 2", "actionable lesson 3"],
  "best_tags": ["top performing tags to reuse"],
  "recommended_length": "short|medium|long based on what performs best",
  "estimated_daily_earnings_usd": 0.00
}}"""

        try:
            raw      = gemini_text(prompt, max_tokens=600)
            raw      = re.sub(r"```json|```", "", raw).strip()
            analysis = json.loads(raw)

            # Save lessons & best tags
            memory["lessons"]     = analysis.get("lessons", [])
            memory["best_tags"]   = analysis.get("best_tags", [])
            memory["last_analysis"] = {
                "date":     datetime.now().strftime("%Y-%m-%d"),
                "pros":     analysis.get("pros", []),
                "cons":     analysis.get("cons", []),
                "est_earnings": analysis.get("estimated_daily_earnings_usd", 0)
            }

            print(f"  ✅ Lessons learned: {len(memory['lessons'])}")
            print(f"  📈 Pros: {analysis.get('pros', [])}")
            print(f"  📉 Cons: {analysis.get('cons', [])}")
            print(f"  💰 Est. earnings: ${analysis.get('estimated_daily_earnings_usd', 0)}/day")

        except Exception as e:
            print(f"  ⚠️ Analysis error: {e}")

    save_memory(memory)
    return memory


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  🤖 AutoBlog AI — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    # Load memory (history + lessons)
    memory = load_memory()

    # Step 1 — Check & learn from yesterday first
    memory = check_and_learn(memory)

    # Step 2 — Find viral topics
    topics = fetch_all_topics()
    if not topics:
        print("❌ No topics found. Exiting.")
        return

    # Step 3 — Pick best topic (using lessons)
    topic_info = pick_best_topic(topics, memory)

    # Step 4 — Write blog
    content = write_blog(topic_info, memory)

    # Step 5 — Humanize
    content = humanize_blog(content)

    # Step 6 — Generate cover image
    img_path  = generate_cover_image(topic_info)
    image_url = upload_image_to_devto(img_path) if img_path else None

    # Step 7 — Publish
    url, article_id = publish_to_devto(topic_info, content, image_url)

    # Step 8 — Save to memory
    save_post_to_memory(memory, topic_info, url, article_id, content)

    print("\n" + "="*60)
    print("  🎉 SUCCESS!")
    print(f"  📝 {topic_info['blog_title']}")
    print(f"  🔗 {url}")
    print(f"  📊 Total posts: {len(memory['posts'])}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
      
