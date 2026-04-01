# 30-Second Demo Video Script — IndieStack MCP

For awesome-claude-code submission (April 7). Patrick records this on his laptop.

---

## Script (30 seconds)

**[Screen: Terminal with Claude Code open]**

**[Type]:** `claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`

**[Voiceover/text overlay]:** "One command. Your AI agent now searches 3,100 dev tools."

**[Type in Claude Code]:** "Find me an auth solution for my Next.js app"

**[Wait for response — should show ranked tools with install commands]**

**[Text overlay]:** "Install commands. Compatibility data. Migration intelligence."

**[Type]:** "What's the lightest open-source payments library?"

**[Wait for response]**

**[Text overlay]:** "From 8,700+ real GitHub repos. Not hallucinated."

**[Final screen]:**
```
indiestack.ai
pip install indiestack
```

---

## Recording Tips
- Use a clean terminal (no clutter)
- Dark theme looks better in README embeds
- Font size 16+ so it's readable at small sizes
- No music needed — silence or typing sounds is fine
- Export as GIF (for README) AND mp4 (for Twitter/PH)
- Tools: asciinema (terminal recording) or OBS (screen capture)
- GIF conversion: `ffmpeg -i demo.mp4 -vf "fps=10,scale=800:-1" demo.gif`

## Fastest recording method
```bash
# Install asciinema
pip install asciinema

# Record
asciinema rec demo.cast

# In the recording:
claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
# Then chat with Claude using IndieStack

# Convert to GIF (needs agg)
pip install asciinema-agg
agg demo.cast demo.gif
```
