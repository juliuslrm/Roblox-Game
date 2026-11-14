"""Central list of every reusable asset and how it is built."""
from .houses import HOUSES
from .landmarks import LANDMARKS
from .meshkit import MeshBuilder
from .nature import NATURE
from .props import PROPS

# category -> (builders, directory of the editable .blend sources, default collision)
CATEGORIES = {
    "houses": (HOUSES, "assets/houses", "proxy"),
    "landmarks": (LANDMARKS, "assets/landmarks", "proxy"),
    "nature": (NATURE, "assets/nature", "none"),
    "props": (PROPS, "assets/props", "mesh"),
}

TRI_LIMIT = 10000          # hard limit per mesh (conservative for the Roblox importer)
TRI_BUDGET = {"houses": 8000, "landmarks": 10000, "nature": 800, "props": 1200}

ASSETS = {}
for _cat, (_builders, _dir, _col) in CATEGORIES.items():
    for _name, _fn in _builders.items():
        assert _name not in ASSETS, f"duplicate asset id {_name}"
        ASSETS[_name] = {"category": _cat, "fn": _fn, "dir": _dir, "default_collision": _col}


def stable_seed(name):
    """Deterministic seed (Python's hash() is salted per process)."""
    return sum((i + 1) * ord(c) for i, c in enumerate(name)) % 100003


def build(name):
    """Build one asset and return its MeshBuilder."""
    mb = MeshBuilder(seed=stable_seed(name))
    ASSETS[name]["fn"](mb)
    if mb.collision is None:
        mb.collision = ASSETS[name]["default_collision"]
    return mb
