# Repository Sentinel Workflow

**Objective**: Monitor a git repository for uncommitted work or unpushed commits, and notify the user via Telegram so work isn't lost or left hanging.

## Inputs
- `repo_path`: The absolute path to the local git repository.

## Steps
1. Run `python tools/repo/sentinel.py <repo_path>`
2. The tool checks `git status` for uncommitted files.
3. The tool checks `git log @{u}..HEAD` for commits that haven't been pushed to the remote.
4. If issues exist, the tool autonomously sends a markdown alert directly to Telegram (using env variables).
5. Output is returned as JSON to the CLI.

## Outputs
- **JSON**: `{"status": "clean"}` or `{"status": "alert_sent"}`

## Edge Cases
- **No Remote Configured**: The script traps the error when checking unpushed commits and simply ignores it, focusing only on uncommitted files.
- **Not a Git Repo**: The script returns an error and exits `1`.
