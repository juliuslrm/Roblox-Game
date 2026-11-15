"""Serialise Python data as a Luau table literal and encode the height map."""
import re

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_KEYWORDS = {"and", "break", "do", "else", "elseif", "end", "false", "for", "function", "if", "in", "local",
             "nil", "not", "or", "repeat", "return", "then", "true", "until", "while", "continue"}


def _num(v):
    if isinstance(v, int):
        return str(v)
    t = f"{v:.4f}".rstrip("0").rstrip(".")
    return t if t not in ("", "-", "-0") else "0"


def to_lua(v, indent=0, inline_depth=1):
    pad = "\t" * indent
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(v, (list, tuple)):
        if all(not isinstance(x, (dict, list, tuple)) for x in v):
            return "{" + ", ".join(to_lua(x) for x in v) + "}"
        if inline_depth <= 0:
            return "{" + ", ".join(to_lua(x, 0, 0) for x in v) + "}"
        inner = ",\n".join(pad + "\t" + to_lua(x, indent + 1, inline_depth - 1) for x in v)
        return "{\n" + inner + ",\n" + pad + "}"
    if isinstance(v, dict):
        def key(k):
            return k if _IDENT.match(k) and k not in _KEYWORDS else f"[{to_lua(k)}]"
        if inline_depth <= 0:
            return "{" + ", ".join(f"{key(k)} = {to_lua(x, 0, 0)}" for k, x in v.items()) + "}"
        inner = ",\n".join(f"{pad}\t{key(k)} = {to_lua(x, indent + 1, inline_depth - 1)}" for k, x in v.items())
        return "{\n" + inner + ",\n" + pad + "}"
    raise TypeError(type(v))


# ---- height map: two characters per sample, 90 printable symbols without '"' and '\'
ALPHABET = "".join(chr(c) for c in range(35, 126) if c != 92)
assert len(ALPHABET) == 90
H_OFFSET, H_STEP = 50.0, 0.02


def encode_heights(values):
    out = []
    for h in values:
        q = int(round((h + H_OFFSET) / H_STEP))
        q = max(0, min(8099, q))
        out.append(ALPHABET[q // 90] + ALPHABET[q % 90])
    return "".join(out)


def decode_heights(text):
    idx = {c: i for i, c in enumerate(ALPHABET)}
    return [(idx[text[i]] * 90 + idx[text[i + 1]]) * H_STEP - H_OFFSET for i in range(0, len(text), 2)]
