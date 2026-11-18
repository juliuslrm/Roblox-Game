# MakeHuman data (CC0)

Source: https://github.com/makehumancommunity/makehuman (`makehuman/data/`, branch `master`).
The MakeHuman project released these assets under CC0 1.0 Universal (see `LICENSE.md` in this
folder, copied from the repository). Only data is used here, no MakeHuman program code.

| File | Content |
|---|---|
| `3dobjs/base.obj` | base mesh hm08 (body, eyes, eyelashes, teeth, helper geometry) |
| `rigs/default.mhskel` | default skeleton: joints as vertex groups of the base mesh |
| `rigs/default_weights.mhw` | skin weights of the default skeleton |
| `targets/*.target.gz` | macro targets (gender, age, muscle, weight, height, ethnic shape), gzip-compressed |

`blender/village/human.py` reads these files. A target that is missing is downloaded once from the
source above and stored here.
