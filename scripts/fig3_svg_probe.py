import re, sys, collections
path = sys.argv[1]
t = open(path, encoding="utf-8", errors="replace").read()
tag = re.search(r"<svg[^>]*>", t).group(0)
vb = re.search(r'viewBox="([^"]+)"', tag).group(1).replace(",", " ").split()
print("SVG tag attrs:", re.findall(r'([\w:.-]+)="([^"]*)"', tag)[:12])
U = 771.840 / float(vb[2])
print("units=", vb, "pt per user unit=", round(U,6))
pat = re.compile(r"<(text|path|polyline|rect|line|circle|polygon|ellipse)\b([^>]*)/?>", re.S)
want = sys.argv[2] if len(sys.argv) > 2 else None
n = 0
for mm in pat.finditer(t):
    name = mm.group(1); raw = mm.group(2).rstrip()
    if raw.endswith("/"): raw = raw[:-1]
    a = dict(re.findall(r'([\w:.-]+)="([^"]*)"', raw))
    sc = a.get("olab:scope", "") + " " + a.get("olab:name","")
    st = a.get("style","")
    def sv(k, d=""):
        m2 = re.search(k + r":\s*([^;]+)", st); return m2.group(1).strip() if m2 else d
    line = "%-8s sc=%-26s stroke=%-9s sw=%-8s fill=%-9s fo=%-6s op=%-6s dash=%-14s stop=%-8s attrs=%s" % (
        name, sc[:26], sv("stroke"), sv("stroke-width"), a.get("fill", sv("fill")), sv("fill-opacity"),
        a.get("opacity", sv("opacity")), sv("stroke-dasharray"), a.get("stop-opacity",""),
        " ".join("%s=%s" % (k, v[:16]) for k, v in a.items() if k not in ("style","olab:scope","fill","olab:name")))
    if want and not re.search(want, line): continue
    print(line); n += 1
    if n > 220: print("..."); break
