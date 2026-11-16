import json, math, re, os
import xml.etree.ElementTree as ET

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
REF = os.path.join(BASE, "outputs", "figures", "Fig3_protocol_W_parity_metrics.svg")
OUT = os.path.join(BASE, "outputs", "origin_data", "fig3_reference_targets.json")
raw = open(REF, encoding="utf-8").read()
m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', raw)
W, H = float(m.group(1)), float(m.group(2))
root = ET.fromstring(raw)


def sget(st, key):
    mm = re.search(key + r":\s*([^;]+)", st or "")
    return mm.group(1).strip() if mm else None


paths = {}
for p in root.iter("{http://www.w3.org/2000/svg}path"):
    pid = p.get("id")
    if not pid:
        continue
    d = (p.get("d") or "").replace("\n", " ")
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    if not xs:
        continue
    paths[pid] = dict(minx=min(xs), maxx=max(xs), miny=min(ys), maxy=max(ys),
                      sw=sget(p.get("style"), "stroke-width"), d=re.sub(r"\s+", " ", d)[:70])

uses = []


def walk(node, chain):
    for ch in list(node):
        tag = ch.tag.split("}")[-1]
        if tag == "g":
            walk(ch, chain + [ch.get("id") or ""])
        elif tag == "use":
            href = ch.get("{http://www.w3.org/1999/xlink}href") or ch.get("href")
            st = ch.get("style", "")
            uses.append(dict(href=href, x=float(ch.get("x")), y=float(ch.get("y")),
                             stroke=sget(st, "stroke"), sw=sget(st, "stroke-width"),
                             chain="/".join([c for c in chain if c][-4:])))
        elif tag == "text":
            st = ch.get("style", "")
            uses.append(dict(kind="text", x=float(ch.get("x", 0)), y=float(ch.get("y", 0)),
                             fs=float(re.sub(r"[^0-9.]", "", str(sget(st, "font-size") or ch.get("font-size") or 0)) or 0),
                             weight=sget(st, "font-weight") or ch.get("font-weight"),
                             fill=sget(st, "fill") or ch.get("fill"),
                             anchor=ch.get("text-anchor") or sget(st, "text-anchor"),
                             content="".join(ch.itertext()),
                             chain="/".join([c for c in chain if c][-4:])))
        elif tag == "path" and not ch.get("id"):
            d = (ch.get("d") or "").replace("\n", " ")
            nums = [float(v) for v in re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", d)]
            xs, ys = nums[0::2], nums[1::2]
            if xs:
                st = ch.get("style", "")
                uses.append(dict(kind="path", chain="/".join([c for c in chain if c][-4:]),
                                 bb=[min(xs), min(ys), max(xs), max(ys)],
                                 fill=sget(st, "fill"), stroke=sget(st, "stroke"),
                                 sw=sget(st, "stroke-width"), fo=sget(st, "fill-opacity"),
                                 dash=sget(st, "stroke-dasharray"), n=len(xs) // 2,
                                 d=re.sub(r"\s+", " ", d)[:60]))
        elif tag == "clipPath":
            for sub in ch.iter():
                if sub.tag.endswith("rect"):
                    uses.append(dict(kind="clip", chain="clip/" + "/".join([c for c in chain if c][-3:]),
                                     bb=[float(sub.get("x")), float(sub.get("y")),
                                         float(sub.get("x")) + float(sub.get("width")),
                                         float(sub.get("y")) + float(sub.get("height"))]))
        if tag == "g":
            continue


walk(root, [])
json.dump(dict(svg_w_pt=W, svg_h_pt=H, marker_paths=paths, items=uses),
          open(OUT, "w", encoding="utf-8"), indent=1)
kinds = {}
for u in uses:
    k = u.get("kind", "use")
    kinds[k] = kinds.get(k, 0) + 1
print("wrote", OUT, "items=", len(uses), kinds)
for u in uses:
    if u.get("kind") == "clip":
        print("CLIP", [round(v, 3) for v in u["bb"]], u["chain"][:50])
for u in uses:
    if u.get("kind") == "text":
        print("TXT", round(u["x"], 2), round(u["y"], 2), u["fs"], u["weight"], u["anchor"], u["fill"],
              repr(u["content"])[:34], "|", u["chain"][:34])

