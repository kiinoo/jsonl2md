#!/usr/bin/env python3
"""
Convert Claude Code JSONL conversation log to Markdown.
Usage: python3 jsonl2md.py <input.jsonl> [output.md]
"""

import json, sys, re
from pathlib import Path
from datetime import datetime

def iso_to_local(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts[:16]

def extract_blocks(content):
    """Return list of (kind, text)."""
    if isinstance(content, str):
        return [("text", content)]
    results = []
    for block in content:
        if not isinstance(block, dict):
            continue
        t = block.get("type", "")
        if t == "text":
            results.append(("text", block.get("text", "")))
        elif t == "tool_use":
            name = block.get("name", "tool")
            inp = block.get("input", {})
            inp_str = json.dumps(inp, ensure_ascii=False, indent=2) if inp else ""
            results.append(("tool_use", f"**`{name}`**\n```json\n{inp_str}\n```"))
        elif t == "tool_result":
            inner = block.get("content", "")
            if isinstance(inner, list):
                inner = "\n".join(b.get("text", "") for b in inner if b.get("type") == "text")
            results.append(("tool_result", str(inner)))
    return results

SKIP = re.compile(r"^<(bash-input|bash-stdout|bash-stderr|local-command-caveat)>", re.S)

def is_boring(content) -> bool:
    if isinstance(content, str):
        s = content.strip()
        return not s or bool(SKIP.match(s))
    if isinstance(content, list):
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        return all(not t.strip() or bool(SKIP.match(t.strip())) for t in texts)
    return True

def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".md")

    messages = []
    with src.open(encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if obj.get("type") not in ("user", "assistant"):
                continue
            if obj.get("isMeta"):
                continue
            msg = obj.get("message", {})
            content = msg.get("content", "")
            if is_boring(content):
                continue
            messages.append({
                "role": msg.get("role", obj.get("type")),
                "content": content,
                "ts": obj.get("timestamp", ""),
            })

    out = [
        f"# {src.stem}",
        "",
        f"*Exported {datetime.now().strftime('%Y-%m-%d')} — {len(messages)} messages*",
        "",
        "---",
        "",
    ]

    for m in messages:
        role = m["role"]
        ts = iso_to_local(m["ts"]) if m["ts"] else ""
        label = "🧑 User" if role == "user" else "🤖 Assistant"
        out.append(f"### {label}" + (f"  <sub>{ts}</sub>" if ts else ""))
        out.append("")

        for kind, text in extract_blocks(m["content"]):
            text = text.strip()
            if not text:
                continue
            if kind == "tool_use":
                out += ["<details>", "<summary>Tool call</summary>", "", text, "", "</details>"]
            elif kind == "tool_result":
                snippet = text[:4000] + ("..." if len(text) > 4000 else "")
                out += ["<details>", "<summary>Tool result</summary>", "", "```", snippet, "```", "", "</details>"]
            else:
                out.append(text)
        out += ["", "---", ""]

    dst.write_text("\n".join(out), encoding="utf-8")
    print(f"OK: {dst}  ({len(messages)} messages, {dst.stat().st_size//1024} KB)")

if __name__ == "__main__":
    main()
