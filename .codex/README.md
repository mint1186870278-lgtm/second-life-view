# Codex API routing

Use `bin/codex-api` from this repository to run Codex with the repository's
API profile (`gpt-6-astra`) and YOLO permissions. The API credential and
provider profile are stored in the user's `~/.codex` directory, not in Git.

Interactive Bash sessions also route a plain `codex` command to this launcher
while the current directory is inside this repository. Outside the repository,
`codex` continues to use the normal global ChatGPT login.
