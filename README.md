# jsonl2md

Convert [Claude Code](https://claude.ai/code) conversation logs (`.jsonl`) to readable Markdown.

Claude Code saves every session to `~/.claude/projects/<project>/`.
This script turns those files into clean, human-readable Markdown — useful for reviewing past work, sharing with teammates, or keeping an archive.

## Output

Each message becomes a section:

```
### 🧑 User  2026-06-18 14:32

How do I add a retry mechanism to this fetch call?

---

### 🤖 Assistant  2026-06-18 14:32

Here's a simple exponential backoff wrapper...
```

Tool calls and tool results are folded into `<details>` blocks so they don't clutter the main conversation, but are still there if you want to expand them.

Shell noise (`bash-input`, `bash-stdout`, `bash-stderr`, internal meta messages) is filtered out automatically.

## Usage

```bash
# Output next to the source file (same name, .md extension)
python3 jsonl2md.py ~/.claude/projects/my-project/abc123.jsonl

# Specify output path
python3 jsonl2md.py ~/.claude/projects/my-project/abc123.jsonl ~/Desktop/session.md
```

No dependencies — standard library only (Python 3.9+).

## Where are the JSONL files?

```
~/.claude/projects/
  -Users-alice-code-myproject/    # one folder per project (path encoded)
    abc123.jsonl                  # one file per session
    def456.jsonl
```

To find all sessions for the current directory:

```bash
project_dir=$(echo "$PWD" | sed 's|/|-|g')
ls ~/.claude/projects/${project_dir#-}/
```

## What gets filtered

| Filtered | Reason |
|---|---|
| `isMeta: true` messages | Internal Claude Code bookkeeping |
| `bash-input` / `bash-stdout` / `bash-stderr` wrappers | Shell command I/O, rarely useful in a transcript |
| `local-command-caveat` messages | Injected system notices |
| `type: mode`, `permission-mode`, `file-history-snapshot` | Session metadata, not conversation |

## License

MIT