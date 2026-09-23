# Codex account routing

Use `bin/codex-api` from this repository to run Codex through the globally
signed-in ChatGPT account with YOLO permissions. It does not load the
repository API credential or API profile.

Interactive Bash sessions also route a plain `codex` command to this launcher
while the current directory is inside this repository. Outside the repository,
`codex` continues to use the same global ChatGPT login without this
repository's YOLO flag.
