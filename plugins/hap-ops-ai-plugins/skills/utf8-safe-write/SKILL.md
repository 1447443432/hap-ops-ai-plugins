---
name: utf8-safe-write
description: Reliable workflow for reading, editing, and writing text files without corrupting UTF-8, BOM, or line endings; use when modifying source files, docs, or skills in Windows PowerShell/Git projects, especially after a file has shown garbled text or encoding damage.
metadata:
  short-description: Safe file writing and encoding recovery
---

# UTF-8 Safe Write

Use this skill whenever a file must be edited or repaired and encoding matters.

## Core rules

- Read before writing. Never rewrite a file blindly.
- Treat mixed Chinese/ASCII files as UTF-8 unless the repo clearly says otherwise.
- Never trust the terminal preview alone for Chinese text. Verify the bytes with a UTF-8 read after writing.
- Do not use default shell redirection, `echo`, or ad hoc search/replace on text that may contain Chinese, BOM, or CRLF/LF differences.
- Prefer the smallest possible edit. If only one line needs to change, change only that line.
- If a file is already garbled, recover from `git show HEAD:path` first, then reapply the intended change.

## Preferred write flow on Windows

1. Inspect the current file with an explicit UTF-8 read.
2. If the file looks corrupted, restore the clean baseline from Git before editing.
3. Edit using a byte-safe method:
   - `apply_patch` for small, local changes.
   - `[System.IO.File]::ReadAllText(..., [Text.Encoding]::UTF8)` and `WriteAllText(..., [Text.UTF8Encoding]::new($false))` when scripting.
4. Re-read the file with `-Encoding utf8`.
5. Run `git diff --check` and the narrowest useful test.

## Recovery pattern

Use this when a file displays mojibake, missing quotes, or broken strings:

```powershell
# inspect clean source from Git first
git show HEAD:path/to/file

# restore from HEAD if needed, then reapply the minimal change
```

## Writing pattern

Use UTF-8 without BOM for source files unless the repo explicitly requires something else:

```powershell
$text = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
# modify text here
[System.IO.File]::WriteAllText($path, $text, [System.Text.UTF8Encoding]::new($false))
```

## Common pitfalls to avoid

- Do not use PowerShell default encoding for text replacement.
- Do not mix byte-safe reads with shell redirection writes.
- Do not “fix” Chinese by adding a Python encoding comment alone; the file contents still need to be written correctly.
- Do not do broad regex replacement on files that contain Chinese strings unless the exact surrounding text has been verified first.
- Do not assume `Get-Content` output is trustworthy unless you used `-Encoding utf8`.

## Sanity checks

- `git diff --check`
- Re-open the edited file with UTF-8 encoding
- If the file is Python, run the narrowest syntax or unit test you can
