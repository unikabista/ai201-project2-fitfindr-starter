"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────
def run_agent(query: str, wardrobe: dict) -> dict:
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse query — simple keyword extraction
    description = query
    size = None
    max_price = None

    # Extract price if user said "under $X"
    import re
    price_match = re.search(r'under\s*\$?(\d+)', query, re.IGNORECASE)
    if price_match:
        max_price = float(price_match.group(1))

    # Extract size if user mentioned one
    size_match = re.search(r'\bsize\s*(XS|S|M|L|XL|XXL)\b', query, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).upper()

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price
    }

    # Step 3: Search listings
    results = search_listings(
        description=description,
        size=size,
        max_price=max_price
    )
    session["search_results"] = results

    # Planning branch: stop if nothing found
    if not results:
        session["error"] = (
            f"No listings found for '{query}'. "
            "Try different keywords, a different size, or a higher budget."
        )
        return session

    # Step 4: Pick top result
    session["selected_item"] = results[0]

    # Step 5: Suggest outfit
    outfit = suggest_outfit(session["selected_item"], wardrobe)
    if not outfit or not outfit.strip():
        session["error"] = "Outfit suggestion failed. Please try again."
        return session
    session["outfit_suggestion"] = outfit

    # Step 6: Create fit card
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"],
        session["selected_item"]
    )

    # Step 7: Return session
    return session
