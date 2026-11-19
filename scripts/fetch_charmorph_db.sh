#!/usr/bin/env bash
# Fetches the CharMorph character database (github.com/Upliner/CharMorph-db) at a fixed commit into
# assets/thirdparty/charmorph-db (not committed, ~1.5 GB).  Only the data is used (meshes, morphs,
# weights, textures); the CharMorph add-on code is not run.  Used character: Reom (CC-BY, see
# docs/CREDITS.md).  The MB-Lab characters in the same database are AGPL-3 and are NOT used.
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=assets/thirdparty/charmorph-db
COMMIT=a8512ac299c0cb1724c7b5417267c94bef024d64
if [ ! -d "$DEST/.git" ]; then
  git clone --recursive https://github.com/Upliner/CharMorph-db "$DEST"
fi
git -C "$DEST" fetch --depth 1 origin "$COMMIT" 2>/dev/null || true
git -C "$DEST" checkout -q "$COMMIT"
git -C "$DEST" submodule update --init --recursive
echo "CharMorph-db at $(git -C "$DEST" rev-parse --short HEAD) in $DEST"
