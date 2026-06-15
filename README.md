# FitFindr 🛍️

A multi-tool AI agent that helps users find secondhand clothing and build outfits around thrifted pieces. The agent searches a mock listings dataset, suggests outfit combinations using an LLM, and generates a shareable caption — handling failures gracefully at each step.

## Setup

1. Clone the repo and install dependencies:

2. Create a `.env` file in the project root:


3. Run the app:
Then open the URL shown in your terminal.

---

## Tool Inventory

### `search_listings(description: str, size: str | None, max_price: float | None) → list[dict]`
**Purpose:** Searches the mock listings dataset for items matching the user's query.  
**Inputs:**
- `description` (str) — keywords describing the item (e.g. "vintage graphic tee")
- `size` (str | None) — size filter, case-insensitive. None skips size filtering.
- `max_price` (float | None) — price ceiling, inclusive. None skips price filtering.

**Output:** A list of matching listing dicts sorted by keyword relevance score, highest first. Returns an empty list if nothing matches — never raises an exception.

Each dict contains: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`.

---

### `suggest_outfit(new_item: dict, wardrobe: dict) → str`
**Purpose:** Uses the Groq LLM to suggest 1–2 outfit combinations using the thrifted item and the user's wardrobe.  
**Inputs:**
- `new_item` (dict) — a listing dict returned by `search_listings`
- `wardrobe` (dict) — a wardrobe dict with an `items` key containing wardrobe pieces. Can be empty.

**Output:** A non-empty string with outfit suggestions. If the wardrobe is empty, returns general styling advice instead of crashing.

---

### `create_fit_card(outfit: str, new_item: dict) → str`
**Purpose:** Uses the Groq LLM to generate a short, shareable Instagram/TikTok-style caption for the outfit.  
**Inputs:**
- `outfit` (str) — the outfit suggestion string from `suggest_outfit`
- `new_item` (dict) — the listing dict for the thrifted item

**Output:** A 2–4 sentence caption string. If `outfit` is empty, returns a descriptive error message string instead of raising an exception.

---

## How the Planning Loop Works

The agent runs in `agent.py` inside `run_agent(query, wardrobe)`. It does not call all three tools unconditionally — it branches based on what each tool returns.

**Step-by-step logic:**

1. Initialize a session dict to store all state for this interaction.
2. Parse the query using regex to extract `description`, `size` (e.g. "size M"), and `max_price` (e.g. "under $30"). Store in `session["parsed"]`.
3. Call `search_listings()` with the parsed parameters. Store results in `session["search_results"]`.
4. **Branch:** If results is an empty list → set `session["error"]` to a helpful message and return early. `suggest_outfit` and `create_fit_card` are never called.
5. If results exist → set `session["selected_item"] = results[0]` (top match by relevance score).
6. Call `suggest_outfit(selected_item, wardrobe)`. Store result in `session["outfit_suggestion"]`.
7. **Branch:** If outfit is empty → set `session["error"]` and return early. `create_fit_card` is never called with empty input.
8. Call `create_fit_card(outfit_suggestion, selected_item)`. Store result in `session["fit_card"]`.
9. Return the completed session.

The key decision point is step 4 — if search returns nothing, the agent communicates this clearly and stops. It never passes empty data downstream.

---

## State Management

All state is stored in a single session dict initialized by `_new_session()` at the start of each interaction. Nothing is hardcoded between steps.

| Key | Set when | Used by |
|-----|----------|---------|
| `session["parsed"]` | After query parsing | `search_listings` call |
| `session["search_results"]` | After `search_listings` | Planning branch check |
| `session["selected_item"]` | After results confirmed non-empty | `suggest_outfit`, `create_fit_card` |
| `session["outfit_suggestion"]` | After `suggest_outfit` | `create_fit_card` |
| `session["fit_card"]` | After `create_fit_card` | Returned to UI |
| `session["error"]` | On any failure | UI error display |

State passes automatically — `selected_item` set in step 5 is the exact same dict passed into `suggest_outfit` in step 6. The user never re-enters anything between steps.

---

## Error Handling

### `search_listings`
Returns an empty list `[]` if no listings match — never raises an exception.  
**Example from testing:**
