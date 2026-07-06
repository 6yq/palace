#!/usr/bin/env python3
"""Mneme MCP server — expose the dot store as typed MCP tools + resources.

Stdlib only, same as serve.py (no `pip install mcp`). Speaks the MCP stdio
transport: newline-delimited JSON-RPC 2.0 on stdin/stdout (logs go to stderr).
Reuses serve.py's parser/writer/reindex so the graph stays the single source of truth.

Wire it up (project-scoped) via mneme/.mcp.json, or:
    claude mcp add Mneme -- python3 viewer/mcp_server.py

Tools:  search · get · neighbors · affiliate · upsert · reindex · stats
Resources:  mneme://index ,  mneme://dot/<id>
"""
import sys, os, json, re, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import serve   # collect(), parse_dot, write_dot(payload), reindex(), ROOT, DOTS

def _reindex():
    """serve.reindex() prints to stdout; stdout is the JSON-RPC channel, so muffle it."""
    with contextlib.redirect_stdout(sys.stderr):
        serve.reindex()

PROTO = "2024-11-05"
STOP = set("the a an of to in for and or on with by is are be as at from into via using "
           "we our this that it its per over under new use used uses model method".split())

def log(*a): print("[mneme-mcp]", *a, file=sys.stderr, flush=True)
def toks(s): return {w for w in re.findall(r"[a-z0-9][a-z0-9+/_.-]{1,}", (s or "").lower()) if w not in STOP}

# ── tool implementations (return plain text; the model reads it) ────────────
def _nodes(): return serve.collect()["nodes"]

def t_search(a):
    q = (a.get("query") or "").lower().strip()
    if not q: return "give a query"
    hits = [n for n in _nodes()
            if q in n["title"].lower() or q in " ".join(n.get("keywords") or []).lower()
            or q in n["project"].lower()]
    if not hits: return f"no dots match {q!r}"
    return "\n".join(f"{n['id']}  [{n['type']}/{n['project']}]  {n['title']}"
                     + ("  <imported>" if n.get("source") else "") for n in hits[:40])

def t_get(a):
    p = serve.DOTS / f"{(a.get('id') or '').strip()}.md"
    return p.read_text(encoding="utf-8") if p.exists() else f"no dot {a.get('id')!r}"

def t_neighbors(a):
    did = (a.get("id") or "").strip(); g = serve.collect()
    title = {n["id"]: n["title"] for n in g["nodes"]}
    out = [f"{e['rel']}  ->  {e['target']}  ({title.get(e['target'],'?')})"
           for e in g["edges"] if e["source"] == did]
    out += [f"{e['rel']}  <-  {e['source']}  ({title.get(e['source'],'?')})"
            for e in g["edges"] if e["target"] == did]
    return "\n".join(out) if out else f"{did} has no links"

def t_affiliate(a):
    qkw = {x.strip().lower() for x in (a.get("keywords") or "").split(",") if x.strip()}
    qtok = qkw | toks(a.get("title"))
    if not qtok: return "give keywords"
    scored, lanes = [], {}
    for n in _nodes():
        nkw = {k.lower() for k in (n.get("keywords") or [])}
        shared = qkw & nkw; ttok = toks(n["title"]) & qtok
        sc = 3*len(shared) + len(ttok - shared)
        if sc:
            scored.append((sc, n["id"], n["project"], sorted(shared | ttok)))
            lanes[n["project"]] = lanes.get(n["project"], 0) + sc
    scored.sort(reverse=True)
    lanes = sorted(lanes.items(), key=lambda x: -x[1])
    r = ["best-fit lanes:"] + [f"  {v:3d}  {p}" for p, v in lanes[:6]]
    r += ["candidate related dots:"] + [f"  {s:3d}  [[{i}]] ({p}) — {', '.join(sh)}"
                                        for s, i, p, sh in scored[:8]]
    return "\n".join(r)

def t_upsert(a):
    did = (a.get("id") or "").strip()
    if not did: return "id required"
    fields = {k: a.get(k, "") for k in
              ("title","type","project","date","status","milestone","keywords","source")}
    serve.write_dot({"id": did, "fields": fields, "body": a.get("body","")})
    _reindex()
    return f"saved {did}.md and reindexed"

def t_reindex(a):
    _reindex(); g = serve.collect()
    return f"reindexed: {len(g['nodes'])} dots, {len(g['edges'])} links"

def t_stats(a):
    ns = _nodes(); byp, byt = {}, {}
    for n in ns:
        byp[n["project"]] = byp.get(n["project"], 0) + 1
        byt[n["type"]] = byt.get(n["type"], 0) + 1
    imp = sum(1 for n in ns if n.get("source"))
    return (f"{len(ns)} dots ({imp} imported) across {len(byp)} lanes\n"
            + "lanes: " + ", ".join(f"{p}:{c}" for p, c in sorted(byp.items(), key=lambda x:-x[1]))
            + "\ntypes: " + ", ".join(f"{t}:{c}" for t, c in sorted(byt.items())))

_S = lambda **p: {"type": "object", "properties": p}
TOOLS = [
    ("search", "Find dots by substring in title / keywords / project.", _S(query={"type":"string"}), ["query"], t_search),
    ("get", "Full markdown of one dot by id.", _S(id={"type":"string"}), ["id"], t_get),
    ("neighbors", "Linked dots (in + out edges) of a dot id.", _S(id={"type":"string"}), ["id"], t_neighbors),
    ("affiliate", "Given comma-separated keywords (+ optional title), rank the project lanes the dot fits and candidate related dots.", _S(keywords={"type":"string"}, title={"type":"string"}), ["keywords"], t_affiliate),
    ("upsert", "Create or overwrite a dot. Fields: title,type,project,date,status,milestone,keywords(comma-sep),source(blank=own work),body(markdown incl. ## Links).", _S(id={"type":"string"}, title={"type":"string"}, type={"type":"string"}, project={"type":"string"}, date={"type":"string"}, status={"type":"string"}, milestone={"type":"boolean"}, keywords={"type":"string"}, source={"type":"string"}, body={"type":"string"}), ["id"], t_upsert),
    ("reindex", "Regenerate INDEX.md.", _S(), [], t_reindex),
    ("stats", "Counts of dots by lane / type / origin.", _S(), [], t_stats),
]
TOOLMAP = {name: fn for name, _d, _s, _r, fn in TOOLS}

# ── resources ───────────────────────────────────────────────────────────────
def res_list():
    out = [{"uri": "mneme://index", "name": "INDEX.md", "mimeType": "text/markdown"}]
    for n in _nodes():
        out.append({"uri": f"mneme://dot/{n['id']}", "name": n["title"], "mimeType": "text/markdown"})
    return out

def res_read(uri):
    if uri == "mneme://index":
        p = serve.ROOT / "INDEX.md"
        return p.read_text(encoding="utf-8") if p.exists() else "(no INDEX.md — run reindex)"
    m = re.match(r"^mneme://dot/(.+)$", uri)
    if m: return t_get({"id": m.group(1)})
    raise ValueError(f"unknown resource {uri}")

# ── JSON-RPC dispatch ─────────────────────────────────────────────────────────
def handle(msg):
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        return {"protocolVersion": params.get("protocolVersion", PROTO),
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "mneme", "version": "0.1.0"}}
    if method == "ping": return {}
    if method == "tools/list":
        return {"tools": [{"name": n, "description": d, "inputSchema": {**s, "required": r}}
                          for n, d, s, r, _ in TOOLS]}
    if method == "tools/call":
        name = params.get("name"); args = params.get("arguments") or {}
        fn = TOOLMAP.get(name)
        if not fn: return {"content": [{"type": "text", "text": f"unknown tool {name}"}], "isError": True}
        try:
            return {"content": [{"type": "text", "text": str(fn(args))}]}
        except Exception as e:
            log("tool error", name, e)
            return {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True}
    if method == "resources/list": return {"resources": res_list()}
    if method == "resources/read":
        try:
            return {"contents": [{"uri": params.get("uri"), "mimeType": "text/markdown",
                                  "text": res_read(params.get("uri"))}]}
        except Exception as e:
            raise
    raise KeyError(method)   # -> method not found

def main():
    log("Mneme MCP up (stdio) — dots at", serve.DOTS)
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: msg = json.loads(line)
        except json.JSONDecodeError: continue
        mid = msg.get("id")
        if mid is None and msg.get("method","").startswith(("notifications/", "notification")):
            continue                                   # notification: no reply
        try:
            result = handle(msg)
            resp = {"jsonrpc": "2.0", "id": mid, "result": result}
        except KeyError as e:
            resp = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {e}"}}
        except Exception as e:
            log("dispatch error", e)
            resp = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(e)}}
        if mid is not None:                            # requests get a reply; notifications don't
            sys.stdout.write(json.dumps(resp) + "\n"); sys.stdout.flush()

if __name__ == "__main__":
    main()
