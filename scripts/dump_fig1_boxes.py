# -*- coding: ascii -*-
"""Dump the FROZEN Fig.1 design model ink boxes for every text item.

The builder (scripts/build_fig1_constants.py) owns the ink-box model that the
design audit (_qa_fig1_design.txt) was run against, so we reuse its functions
verbatim instead of re-deriving them.  The builder source is executed from a
temp copy whose output path is redirected, so the frozen
outputs/origin_data/fig1_origin_constants.json is never rewritten.

writes outputs/origin_data/fig1_text_boxes.json  {name: [x0, y0, x1, y1]}
"""
import os, io, json, hashlib, tempfile

B  = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
SRC = os.path.join(B, "scripts", "build_fig1_constants.py")
REAL = os.path.join(OD, "fig1_origin_constants.json")
before = hashlib.md5(io.open(REAL, "rb").read()).hexdigest()

src = io.open(SRC, encoding="utf-8").read()
assert "fig1_origin_constants.json" in src
tmp = os.path.join(tempfile.gettempdir(), "_f1_builder_copy.py")
io.open(tmp, "w", encoding="utf-8").write(src.replace("fig1_origin_constants.json", "_tmp_fig1_boxes_build.json"))
g = {"__name__": "__main__", "__file__": SRC}
exec(compile(io.open(tmp, encoding="utf-8").read(), SRC, "exec"), g)

D = json.load(io.open(REAL, encoding="utf-8"))
ink_box = g["ink_box"]
out = {}
for it in D["texts"]:
    b = ink_box(it)
    out[it["name"]] = [round(float(z), 4) for z in b]
json.dump(out, io.open(os.path.join(OD, "fig1_text_boxes.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)

after = hashlib.md5(io.open(REAL, "rb").read()).hexdigest()
tj = os.path.join(OD, "_tmp_fig1_boxes_build.json")
if os.path.exists(tj):
    os.remove(tj)
os.remove(tmp)
print("items=%d  frozen json md5 unchanged=%s (%s)" % (len(out), before == after, before))
w = [v[2] - v[0] for v in out.values()]; h = [v[3] - v[1] for v in out.values()]
print("box w: min %.2f max %.2f   h: min %.2f max %.2f" % (min(w), max(w), min(h), max(h)))
