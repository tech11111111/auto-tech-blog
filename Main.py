import google.generativeai as genai
import os

# 1. Setup AI
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. The Strategy Prompt (Competitor + Viral Focus)
prompt = """
Find the top trending tech news today from Reddit and Techmeme. 
Write a 1000-word blog post in clean HTML format.
Use a 'Tech Enthusiast' tone. 
Include SEO keywords, a catchy title, and H2 headings. 
Ensure there is a section that addresses 'what others are missing' compared to competitors.
"""

# 3. Generate & Save
response = model.generate_content(prompt)
with open("public/index.html", "w") as f:
    f.write(response.text)
