#!/usr/bin/env python3
"""palace viewer server — stdlib only (no pip; works on minimal Python installs).

Serves the Cytoscape graph and reads/writes dots as markdown.
Markdown files in ../dots/*.md are the source of truth; this server never
holds a database — it parses the files on every request.

Run:   python3 serve.py [--port 8899] [--reindex]
Local: open http://127.0.0.1:8899
Remote (no X):  ssh -L 8899:127.0.0.1:8899 host  then open localhost:8899 locally.

Security: binds 127.0.0.1 only. POST writes are confined to ../dots/ and the
id is sanitized — never expose this to a network.
"""
import http.server, socketserver, json, re, sys, os, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                 # palace/
DOTS = ROOT / "dots"
EXAMPLES = ROOT / "examples"

def source_dir():
    """Real dots if any exist; else the shipped synthetic examples (so a fresh
    clone with an empty/absent dots/ still renders something)."""
    if DOTS.exists() and any(DOTS.glob("*.md")):
        return DOTS
    return EXAMPLES
ID_RE = re.compile(r"^[0-9A-Za-z._-]+$")
WIKILINK = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
TYPED_EDGE = re.compile(r"^\s*-\s*([A-Za-z_-]+)\s*::\s*\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", re.M)

# ---- minimal frontmatter parser (no PyYAML) --------------------------------

def parse_scalar(v):
    v = v.strip()
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
    return v.strip("'\"")

def parse_dot(path):
    text = path.read_text(encoding="utf-8")
    fm, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, _, v = line.partition(":")
                fm[k.strip()] = parse_scalar(v)
        body = m.group(2)
    fm.setdefault("id", path.stem)
    fm.setdefault("title", fm.get("id"))
    fm.setdefault("type", "insight")
    fm.setdefault("project", "misc")
    fm.setdefault("status", "open")
    fm.setdefault("milestone", False)
    fm.setdefault("date", "")
    fm.setdefault("source", "")          # provenance for imported dots (DOI/URL/cite); "" = own work
    fm.setdefault("keywords", [])
    if isinstance(fm["keywords"], str):
        fm["keywords"] = [fm["keywords"]] if fm["keywords"] else []
    fm["body"] = body.rstrip() + "\n"
    return fm

def collect():
    nodes, edges, ids = [], [], set()
    src = source_dir()
    if not src.exists():
        return {"nodes": [], "edges": []}
    dots = {}
    for p in sorted(src.glob("*.md")):
        d = parse_dot(p)
        dots[d["id"]] = d
        ids.add(d["id"])
    for d in dots.values():
        nodes.append({k: d[k] for k in
                      ("id", "title", "type", "project", "date", "status",
                       "milestone", "keywords", "source", "body")})
        body = d["body"]
        typed = set()
        for rel, tgt in TYPED_EDGE.findall(body):
            typed.add(tgt)
            edges.append({"source": d["id"], "target": tgt, "rel": rel,
                          "dangling": tgt not in ids})
        # untyped wikilinks elsewhere -> 'related', unless already typed
        for tgt in WIKILINK.findall(body):
            if tgt and tgt not in typed and tgt != d["id"]:
                edges.append({"source": d["id"], "target": tgt, "rel": "related",
                              "dangling": tgt not in ids})
                typed.add(tgt)
    return {"nodes": nodes, "edges": edges}

def write_dot(payload):
    did = payload.get("id", "").strip()
    if not ID_RE.match(did):
        raise ValueError("bad id")
    dest = (DOTS / f"{did}.md").resolve()
    if DOTS.resolve() not in dest.parents:
        raise ValueError("path escape")
    f = payload.get("fields", {})
    kw = f.get("keywords", [])
    if isinstance(kw, str):
        kw = [x.strip() for x in kw.split(",") if x.strip()]
    ms = str(f.get("milestone", False)).lower() in ("true", "1", "yes", "on")
    src = str(f.get("source", "")).strip()
    fm = (
        f"---\n"
        f"id: {did}\n"
        f"title: {f.get('title','').strip()}\n"
        f"type: {f.get('type','insight').strip()}\n"
        f"project: {f.get('project','misc').strip()}\n"
        f"date: {f.get('date','').strip()}\n"
        f"status: {f.get('status','open').strip()}\n"
        f"milestone: {'true' if ms else 'false'}\n"
        f"keywords: [{', '.join(kw)}]\n"
        + (f"source: {src}\n" if src else "")
        + f"---\n"
    )
    body = payload.get("body", "").rstrip() + "\n"
    DOTS.mkdir(exist_ok=True)
    dest.write_text(fm + body, encoding="utf-8")
    return did

def reindex():
    data = collect()
    by_proj = {}
    for n in data["nodes"]:
        by_proj.setdefault(n["project"], []).append(n)
    lines = ["# Palace index", "",
             f"{len(data['nodes'])} dots, {len(data['edges'])} links. "
             "Regenerated by `serve.py --reindex` — do not hand-edit.", ""]
    for proj in sorted(by_proj):
        lines.append(f"## {proj}")
        lines.append("")
        lines.append("| id | title | type | status | date | milestone |")
        lines.append("|---|---|---|---|---|---|")
        for n in sorted(by_proj[proj], key=lambda x: x["date"]):
            star = "★" if n["milestone"] else ""
            lines.append(f"| `{n['id']}` | {n['title']} | {n['type']} | "
                         f"{n['status']} | {n['date']} | {star} |")
        lines.append("")
    (ROOT / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"reindexed: {len(data['nodes'])} dots -> {ROOT/'INDEX.md'}")

# ---- http ------------------------------------------------------------------

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(HERE), **k)

    def _json(self, obj, code=200):
        b = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.rstrip("/") in ("/api/dots", "/api/dots?"):
            return self._json(collect())
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.rstrip("/") != "/api/dot":
            return self._json({"error": "not found"}, 404)
        n = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
            did = write_dot(payload)
            reindex()
            self._json({"ok": True, "id": did})
        except Exception as e:
            self._json({"error": str(e)}, 400)

    def log_message(self, *a):
        pass

def main():
    port = 8899
    if "--reindex" in sys.argv:
        reindex(); return
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        print(f"palace viewer: http://127.0.0.1:{port}  (Ctrl-C to stop)")
        print(f"remote: ssh -L {port}:127.0.0.1:{port} <host>, then open localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nbye")

if __name__ == "__main__":
    main()
