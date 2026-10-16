# SPL parser check (part6, first 200 labels)

Read-only diagnostics written to check `medsafe/spl.py` against real DailyMed files. Run from the
repo root with the venv python in isolated mode. Replace `ZIP` with the zip path.

```
aakaash\.venv\Scripts\python.exe -I aakaash\scripts\spl_check\zip_check.py ZIP
aakaash\.venv\Scripts\python.exe -I aakaash\scripts\spl_check\inner_layout.py ZIP 200
aakaash\.venv\Scripts\python.exe -I aakaash\scripts\spl_check\parser_check.py aakaash ZIP 200 parser OUT.json
aakaash\.venv\Scripts\python.exe -I aakaash\scripts\spl_check\parser_check.py aakaash ZIP 200 survey OUT.json
aakaash\.venv\Scripts\python.exe -I aakaash\scripts\spl_check\parser_deepdive.py aakaash ZIP 200
aakaash\.venv\Scripts\python.exe -I aakaash\scripts\spl_check\parser_fallback_check.py aakaash ZIP
```
`parser_check.py` reports peak working set through the Windows API, so it runs on Windows only.
