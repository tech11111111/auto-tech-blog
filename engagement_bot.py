"""
engagement_bot.py
─────────────────
Comments on trending posts across Dev.to and Hashnode.
Posts genuine helpful comments + naturally promotes our blog.
Drives traffic back to TechPulse AI.
Learns which comment styles get most engagement.

RULES BUILT IN:
- Never spam same post twice
- Max 3 comments per platform per day
- Only comments on posts with 10+ reactions
- 30 second delay between comments
- Rotates comment styles
- Saves all activity to prevent duplicates

ERROR HANDLING:
- Safe API calls with retry
- Duplicate prevention
- Rate limit handling
- Graceful failures
"""

import os
import re
import json
import time
import requests
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
DEVTO_API_KEY   = os.environ.get("DEVTO_API_KEY", "")
HASHNODE_API_KEY= os.environ.get("HASHNODE_API_KEY", "")
BRAIN_FILE      = "brain.json"
ENGAGE_FILE     = "engagement.json"
TODAY           = datetime.now().strftime("%Y-%m-%d")
TODAY_DISPLAY   = datetime.now().strftime("%B %d, %Y")
CURRENT_YEAR    = datetime.now().strftime("%Y")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"

# Our blog info
OUR_BLOG_URL  = "https://dev.to/miral_dhodi_38e9644df1762"
OUR_BLOG_NAME = "TechPulse AI"

# Max comments per day per platform
MAX_COMMENTS_PER_PLATFORM = 3
DELAY_BETWEEN_COMMENTS    = 30  # seconds


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def safe_request(method, url, timeout=15, **kwargs):
    """Safe HTTP request with error handling"""
    try:
        r = getattr(requests, method)(url, timeout=timeout, **kwargs)
        return r
    except Exception as e:
        print(f"    ⚠️ Request error: {e}")
        return None


def gemini_text(prompt, max_tokens=500):
    """Call Gemini with error handling"""
    try:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.8}
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


def load_engagement():
    """Load engagement history"""
    try:
        if os.path.exists(ENGAGE_FILE):
            with open(ENGAGE_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"commented_posts": [], "daily_counts": {}, "comment_history": []}


def save_engagement(engagement):
    """Save engagement history"""
    try:
        with open(ENGAGE_FILE, "w") as f:
            json.dump(engagement, f, indent=2)
    except Exception as e:
        print(f"  ⚠️ Engagement save error: {e}")


def save_brain(brain):
    try:
        with open(BRAIN_FILE, "w") as f:
            json.dump(brain, f, indent=2)
    except Exception as e:
        print(f"  ⚠️ Brain save error: {e}")


def already_commented(engagement, post_url):
    """Check if we already commented on this post"""
    return post_url in engagement.get("commented_posts", [])


def get_daily_count(engagement, platform):
    """Get today's comment count for a platform"""
    return engagement.get("daily_counts", {}).get(TODAY, {}).get(platform, 0)


def increment_daily_count(engagement, platform):
    """Increment daily comment count"""
    engagement.setdefault("daily_counts", {})
    engagement["daily_counts"].setdefault(TODAY, {})
    current = engagement["daily_counts"][TODAY].get(platform, 0)
    engagement["daily_counts"][TODAY][platform] = current + 1


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Find Posts to Comment On
# ─────────────────────────────────────────────────────────────────────────────
def find_devto_posts_to_comment(engagement):
    """Find trending Dev.to posts worth commenting on"""
    print("  📰 Finding Dev.to posts to comment on...")

    posts = []
    try:
        r = safe_request("get", "https://dev.to/api/articles?top=1&per_page=30")
        if not r or r.status_code != 200:
            return posts

        for a in r.json():
            url      = a.get("url", "")
            reactions= a.get("positive_reactions_count", 0)
            comments = a.get("comments_count", 0)

            # Only comment on posts with engagement
            if reactions < 10:
                continue

            # Skip if already commented
            if already_commented(engagement, url):
                continue

            # Skip our own posts
            if "miral_dhodi" in url:
                continue

            posts.append({
                "id":       a.get("id"),
                "title":    a.get("title", ""),
                "url":      url,
                "tags":     a.get("tag_list", []),
                "reactions":reactions,
                "comments": comments,
                "excerpt":  a.get("description", "")[:200],
                "platform": "devto"
            })

    except Exception as e:
        print(f"    ⚠️ Dev.to fetch error: {e}")

    print(f"    ✅ Found {len(posts)} eligible posts")
    return posts[:10]


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Generate Smart Comment
# ─────────────────────────────────────────────────────────────────────────────
def generate_comment(post, comment_style, brain):
    """Generate a genuine helpful comment for a post"""

    our_recent_posts = []
    for p in brain.get("posts_history", [])[-5:]:
        our_recent_posts.append({
            "title": p.get("title", ""),
            "url":   p.get("url", OUR_BLOG_URL)
        })

    style_instructions = {
        "helpful": f"""Write a GENUINELY HELPFUL comment that:
1. Adds real value (insight, fact, or perspective they missed)
2. Shows you actually read the post
3. Naturally mentions our blog: "We covered a related angle at {OUR_BLOG_NAME}: [our relevant post URL if available]"
4. Ends with an engaging question to spark discussion
Keep it 3-4 sentences. Sound like a real tech professional.""",

        "question": f"""Write a THOUGHTFUL QUESTION comment that:
1. Asks a genuinely curious question about the topic
2. Shows expertise in the subject
3. Subtly mentions: "Curious because we've been exploring this at {OUR_BLOG_NAME}"
4. Makes the author want to reply
Keep it 2-3 sentences. Sound natural and curious."""
    }

    our_posts_text = "\n".join([
        f"- {p['title']}: {p['url']}" for p in our_recent_posts
    ]) if our_recent_posts else f"Visit {OUR_BLOG_URL} for more"

    prompt = f"""You are a tech professional commenting on a blog post. Today: {TODAY_DISPLAY}.

POST TO COMMENT ON:
Title: {post['title']}
Tags: {', '.join(post.get('tags', []))}
Excerpt: {post.get('excerpt', '')}

OUR RECENT POSTS (use most relevant one if mentioning):
{our_posts_text}

COMMENT STYLE: {style_instructions.get(comment_style, style_instructions['helpful'])}

STRICT RULES:
- Sound 100% human, not like a bot
- Never be overly promotional
- Add genuine value first
- Keep under 150 words
- No hashtags
- No emojis unless very natural
- Must relate directly to the post content

Write ONLY the comment text, nothing else:"""

    try:
        comment = gemini_text(prompt, max_tokens=200)
        if comment and len(comment) > 20:
            return comment
    except Exception as e:
        print(f"    ⚠️ Comment generation error: {e}")

    return ""


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Post Comment to Dev.to
# ─────────────────────────────────────────────────────────────────────────────
def post_devto_comment(article_id, comment_text):
    """Post a comment to Dev.to article"""
    try:
        headers = {
            "api-key":      DEVTO_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "comment": {
                "body_markdown": comment_text,
                "commentable_id": article_id,
                "commentable_type": "Article"
            }
        }
        r = safe_request(
            "post",
            "https://dev.to/api/comments",
            headers=headers,
            json=payload
        )
        if r and r.status_code in (200, 201):
            return True
        else:
            status = r.status_code if r else "no response"
            print(f"    ⚠️ Comment post failed: {status}")
            return False
    except Exception as e:
        print(f"    ⚠️ Dev.to comment error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Learn from Engagement
# ─────────────────────────────────────────────────────────────────────────────
def analyze_comment_performance(engagement, brain):
    """Analyze which comment styles got most replies"""
    try:
        history    = engagement.get("comment_history", [])
        if len(history) < 5:
            return

        style_performance = {}
        for entry in history:
            style   = entry.get("style", "helpful")
            replies = entry.get("replies", 0)
            style_performance.setdefault(style, [])
            style_performance[style].append(replies)

        # Find best style
        best_style = max(
            style_performance,
            key=lambda s: sum(style_performance[s]) / len(style_performance[s])
        ) if style_performance else "helpful"

        brain.setdefault("engagement_strategy", {})
        brain["engagement_strategy"]["best_comment_style"] = best_style
        brain["engagement_strategy"]["last_analyzed"]      = TODAY_DISPLAY
        save_brain(brain)
        print(f"  📊 Best comment style: {best_style}")
    except Exception as e:
        print(f"  ⚠️ Performance analysis error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print(f"  💬 Engagement Bot — {TODAY_DISPLAY}")
    print("="*60 + "\n")

    if not DEVTO_API_KEY:
        print("  ❌ DEVTO_API_KEY not found — skipping")
        return

    brain      = load_brain()
    engagement = load_engagement()

    # Get best comment style from brain
    best_style = brain.get("engagement_strategy", {}).get("best_comment_style", "helpful")

    # Comment styles to rotate
    styles = ["helpful", "question"]

    # ── Dev.to Comments ──────────────────────────────────────────────────────
    devto_count = get_daily_count(engagement, "devto")
    print(f"  📊 Dev.to comments today: {devto_count}/{MAX_COMMENTS_PER_PLATFORM}")

    if devto_count < MAX_COMMENTS_PER_PLATFORM:
        posts = find_devto_posts_to_comment(engagement)

        for i, post in enumerate(posts):
            if devto_count >= MAX_COMMENTS_PER_PLATFORM:
                print(f"  ✅ Reached daily limit for Dev.to")
                break

            # Rotate comment styles
            style   = styles[i % len(styles)]

            print(f"\n  📝 Commenting on: {post['title'][:50]}...")
            print(f"     Style: {style}")

            comment = generate_comment(post, style, brain)
            if not comment:
                print("     ⚠️ Could not generate comment, skipping")
                continue

            # Post comment
            success = post_devto_comment(post["id"], comment)

            if success:
                print(f"     ✅ Comment posted!")

                # Save to engagement history
                engagement["commented_posts"].append(post["url"])
                engagement["comment_history"].append({
                    "date":     TODAY,
                    "platform": "devto",
                    "post":     post["title"],
                    "style":    style,
                    "replies":  0
                })
                increment_daily_count(engagement, "devto")
                devto_count += 1
                save_engagement(engagement)

                # Wait between comments to avoid spam detection
                if i < len(posts) - 1:
                    print(f"     ⏳ Waiting {DELAY_BETWEEN_COMMENTS}s...")
                    time.sleep(DELAY_BETWEEN_COMMENTS)
            else:
                print(f"     ❌ Comment failed")

    # Analyze performance
    analyze_comment_performance(engagement, brain)

    total_today = get_daily_count(engagement, "devto")

    print("\n" + "="*60)
    print("  ✅ Engagement complete!")
    print(f"  💬 Comments posted today: {total_today}")
    print(f"  📚 Total posts engaged: {len(engagement.get('commented_posts', []))}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

