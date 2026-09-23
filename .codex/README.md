# Codex API routing

Use `bin/codex-api` from this repository to run Codex with the repository's
API profile (`evomap-gpt-5.6-terra`, `max` reasoning) and YOLO permissions. The API credential and
provider profile are stored in the user's `~/.codex` directory, not in Git.

The profile is configured for EvoMap's `/v1` API base. Its current public
endpoint is `/v1/chat/completions`; Codex custom providers require the
Responses protocol, so the gateway must also expose `/v1/responses` (or be
fronted by a Responses-to-Chat-Completions bridge) before this profile can run.

Interactive Bash sessions also route a plain `codex` command to this launcher
while the current directory is inside this repository. Outside the repository,
`codex` continues to use the normal global ChatGPT login.
