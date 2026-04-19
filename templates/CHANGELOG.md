---

## Change Log Requirement (MANDATORY)

For every **meaningful or non-trivial change**, Claude must update a running change log inside CHANGELOG.md file.

### Rules

- Maintain a section at the **end of CHANGELOG.md** titled:

## Change Log

- After completing any significant task (feature addition, refactor, architectural change, dependency change), append a new entry.

- Each entry must include:

### [YYYY-MM-DD HH:MM] - <Short Title>

**Summary**
- What was implemented or changed

**Details**
- Key components/files affected
- Important implementation decisions

**Reason**
- Why this change was made

**Notes (optional)**
- Tradeoffs, limitations, or follow-ups

### Guidelines

- Keep entries **concise but meaningful**
- Do not log trivial changes (formatting, minor renames unless impactful)
- Prefer clarity over verbosity
- This log should help a future reader quickly understand how the system evolved

### Example

### 2026-03-30 14:20 - Initial Voice Loop Implementation

**Summary**
- Implemented end-to-end voice loop

**Details**
- Added microphone recording module
- Integrated local Whisper for transcription
- Connected OpenAI API for response generation
- Used macOS `say` for TTS

**Reason**
- Establish core Phase 1 functionality

**Notes**
- No session persistence yet