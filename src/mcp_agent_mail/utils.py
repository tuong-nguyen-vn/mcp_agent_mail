"""Utility helpers for the MCP Agent Mail service."""

from __future__ import annotations

import random
import re
from typing import Iterable, Optional

# Agent name word lists - used to generate memorable adjective+noun combinations
# These lists are designed to provide a large namespace (62 x 69 = 4278 combinations)
# while keeping names easy to remember, spell, and distinguish.
#
# Design principles:
# - All words are capitalized for consistent CamelCase output (e.g., "GreenLake")
# - Adjectives are colors, weather, materials, and nature-themed descriptors
# - Nouns are nature, geography, animals, and simple objects
# - No offensive, controversial, or confusing words
# - No words that could be easily misspelled or confused with each other

ADJECTIVES: Iterable[str] = (
    # Colors (original + expanded)
    "Red",
    "Orange",
    "Pink",
    "Black",
    "Purple",
    "Blue",
    "Brown",
    "White",
    "Green",
    "Chartreuse",
    "Lilac",
    "Fuchsia",
    "Azure",
    "Amber",
    "Coral",
    "Crimson",
    "Cyan",
    "Gold",
    "Gray",
    "Indigo",
    "Ivory",
    "Jade",
    "Lavender",
    "Magenta",
    "Maroon",
    "Navy",
    "Olive",
    "Pearl",
    "Rose",
    "Ruby",
    "Sage",
    "Scarlet",
    "Silver",
    "Teal",
    "Topaz",
    "Violet",
    "Cobalt",
    "Copper",
    "Bronze",
    "Emerald",
    "Sapphire",
    "Turquoise",
    # Weather and nature
    "Sunny",
    "Misty",
    "Foggy",
    "Stormy",
    "Windy",
    "Frosty",
    "Dusty",
    "Hazy",
    "Cloudy",
    "Rainy",
    # Descriptive
    "Swift",
    "Quiet",
    "Bold",
    "Calm",
    "Bright",
    "Dark",
    "Wild",
    "Silent",
    "Gentle",
    "Rustic",
)

NOUNS: Iterable[str] = (
    # Original nouns
    "Stone",
    "Lake",
    "Dog",
    "Creek",
    "Pond",
    "Cat",
    "Bear",
    "Mountain",
    "Hill",
    "Snow",
    "Castle",
    # Geography and nature
    "River",
    "Forest",
    "Valley",
    "Canyon",
    "Meadow",
    "Prairie",
    "Desert",
    "Island",
    "Cliff",
    "Cave",
    "Glacier",
    "Waterfall",
    "Spring",
    "Stream",
    "Reef",
    "Dune",
    "Ridge",
    "Peak",
    "Gorge",
    "Marsh",
    "Brook",
    "Glen",
    "Grove",
    "Hollow",
    "Basin",
    "Cove",
    "Bay",
    "Harbor",
    # Animals
    "Fox",
    "Wolf",
    "Hawk",
    "Eagle",
    "Owl",
    "Deer",
    "Elk",
    "Moose",
    "Falcon",
    "Raven",
    "Heron",
    "Crane",
    "Otter",
    "Beaver",
    "Badger",
    "Finch",
    "Robin",
    "Sparrow",
    "Lynx",
    "Puma",
    # Objects and structures
    "Tower",
    "Bridge",
    "Forge",
    "Mill",
    "Barn",
    "Gate",
    "Anchor",
    "Lantern",
    "Beacon",
    "Compass",
)

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_AGENT_NAME_RE = re.compile(r"[^A-Za-z0-9]+")


def slugify(value: str) -> str:
    """Normalize a human-readable value into a slug."""
    normalized = value.strip().lower()
    slug = _SLUG_RE.sub("-", normalized).strip("-")
    return slug or "project"


# Regex for WSL path pattern: /mnt/<drive>/... or /mnt/<drive>
_WSL_PATH_RE = re.compile(r"^/mnt/([a-zA-Z])(?:/(.*))?$")


def canonicalize_project_identifier(identifier: str) -> str:
    """Normalize path identifiers for consistent project lookup.

    Handles WSL/Windows path equivalence so the same physical directory
    produces the same canonical form regardless of access path:

    - /mnt/c/foo → c:/foo
    - C:\\foo → c:/foo
    - c:/foo → c:/foo (already canonical)
    - /home/user/project → /home/user/project (Linux passthrough)

    The canonical form uses:
    - Lowercase drive letters
    - Forward slashes only
    - No trailing slashes (except root)
    - Collapsed repeated slashes

    Args:
        identifier: A path string or project identifier.

    Returns:
        Canonicalized identifier string.
    """
    if not identifier:
        return identifier

    # Strip whitespace
    result = identifier.strip()
    if not result:
        return result

    # Normalize all backslashes to forward slashes
    result = result.replace("\\", "/")

    # Collapse repeated slashes (but preserve leading // for UNC if needed)
    while "//" in result:
        result = result.replace("//", "/")

    # Check for WSL path: /mnt/c/... → c:/...
    wsl_match = _WSL_PATH_RE.match(result)
    if wsl_match:
        drive = wsl_match.group(1).lower()
        rest = wsl_match.group(2)
        result = f"{drive}:/{rest}" if rest else f"{drive}:/"

    # Check for Windows drive letter path: C:/... or C:...
    # Match pattern like "C:/" or "C:" at start
    elif len(result) >= 2 and result[1] == ":" and result[0].isalpha():
        drive = result[0].lower()
        rest = result[2:]
        # Ensure path starts with / after drive
        if rest and not rest.startswith("/"):
            rest = "/" + rest
        result = f"{drive}:{rest}" if rest else f"{drive}:/"

    # Remove trailing slash unless it's a root path
    # Keep trailing slash for drive roots like "c:/"
    if len(result) > 1 and result.endswith("/") and not (len(result) == 3 and result[1] == ":"):
        result = result.rstrip("/")

    return result


def generate_agent_name() -> str:
    """Return a random adjective+noun combination."""
    adjective = random.choice(tuple(ADJECTIVES))
    noun = random.choice(tuple(NOUNS))
    return f"{adjective}{noun}"


def validate_agent_name_format(name: str) -> bool:
    """
    Validate that an agent name matches the required adjective+noun format.

    CRITICAL: Agent names MUST be randomly generated two-word combinations
    like "GreenLake" or "BlueDog", NOT descriptive names like "BackendHarmonizer".

    Names should be:
    - Unique and easy to remember
    - NOT descriptive of the agent's role or task
    - One of the predefined adjective+noun combinations

    Note: This validation is case-insensitive to match the database behavior
    where "GreenLake", "greenlake", and "GREENLAKE" are treated as the same.

    Returns True if valid, False otherwise.
    """
    if not name:
        return False

    # Check if name matches any valid adjective+noun combination (case-insensitive)
    name_lower = name.lower()
    for adjective in ADJECTIVES:
        for noun in NOUNS:
            if name_lower == f"{adjective}{noun}".lower():
                return True

    return False


def sanitize_agent_name(value: str) -> Optional[str]:
    """Normalize user-provided agent name; return None if nothing remains."""
    cleaned = _AGENT_NAME_RE.sub("", value.strip())
    if not cleaned:
        return None
    return cleaned[:128]
