# Edge case: omitted mark vs empty mark

**Edge case:** The spec says `mark` is optional on create, but doesn’t define what happens if it’s omitted or sent as an empty value.

**My decision:**
- **POST /students**: If `mark` is omitted or null/empty, I default it to `0`.
  - Reason: keeps persistence simple, ensures stats always work, and matches the frontend behaviour (it sends 0 when blank).
- **PUT /students/{id}**: If `mark` is omitted, I keep the existing mark. If `mark` is provided but empty/null, I treat it as an error.
  - Reason: PUT should be explicit; “empty” is ambiguous (clear vs invalid). Omitting the field is the clean “no change” signal.

This produces consistent API behaviour and prevents accidental mark wiping.