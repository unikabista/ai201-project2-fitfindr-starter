"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:

    # Step 1: Load all listings from data/listings.json
    listings = load_listings()

    # Step 2 & 3: Filter by price and size
    filtered = []
    for item in listings:

        # Skip if item costs more than max_price
        if max_price is not None and item["price"] > max_price:
            continue

        # Skip if size doesn't match (case-insensitive)
        if size is not None and size.lower() not in item["size"].lower():
            continue

        filtered.append(item)

    # Step 4: Score each item by keyword overlap
    keywords = description.lower().split()  # ["vintage", "graphic", "tee"]

    scored = []
    for item in filtered:
        # Combine all text fields into one big searchable string
        searchable = (
            item["title"] + " " +
            item["description"] + " " +
            " ".join(item["style_tags"])
        ).lower()

        # Count how many keywords appear in that string
        score = sum(1 for word in keywords if word in searchable)

        # Only keep items that matched at least 1 keyword
        if score > 0:
            scored.append((score, item))

    # Step 5: Sort highest score first, return just the dicts
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored]

# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    client = _get_groq_client()

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        prompt = f"""A user is considering buying this thrifted item:
Item: {new_item['title']}
Description: {new_item['description']}
Style tags: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}

They don't have a wardrobe set up yet. Suggest 1-2 general outfit ideas
for this item — what types of pieces pair well with it, what vibe it suits,
how to style it. Keep it casual and specific."""

    else:
        wardrobe_text = "\n".join([
    f"- {item.get('name') or item.get('title', 'Unknown item')} ({item.get('colors', [])})"
    for item in wardrobe_items
])

        prompt = f"""A user just found this thrifted item:
Item: {new_item['title']}
Description: {new_item['description']}
Style tags: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}

Their current wardrobe includes:
{wardrobe_text}

Suggest 1-2 specific outfit combinations using the new item + pieces from
their wardrobe. Name the specific wardrobe pieces. Keep it casual and specific."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def create_fit_card(outfit: str, new_item: dict) -> str:
    # Step 1: Guard against empty outfit string
    if not outfit or not outfit.strip():
        return "Error: cannot create a fit card without an outfit suggestion."

    client = _get_groq_client()

    prompt = f"""Write a short Instagram/TikTok caption for this thrifted outfit.

Thrifted item: {new_item['title']}
Price: ${new_item['price']}
Platform: {new_item['platform']}
Outfit: {outfit}

Rules:
- 2-4 sentences max
- Casual, authentic tone - like a real person posting an OOTD, not a product description
- Mention the item name, price, and platform once each, naturally
- Capture the specific vibe of the outfit
- No hashtags"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.2
    )

    return response.choices[0].message.content
