# Daily Publisher Automation

This LaunchAgent runs the Underside AI daily publisher at 10:00 every day. It does not run automatically until you install and load the plist.

## Files

- `scripts/run_daily_ai_publisher.sh`: zsh automation wrapper.
- `scripts/daily_ai_publisher_prompt.md`: Codex prompt used by the wrapper.
- `automation/be.underside.ai.daily-publisher.plist`: macOS LaunchAgent definition.

Logs are written to:

```sh
~/Library/Logs/underside-ai
```

## Installation

From the repository root:

```sh
mkdir -p ~/Library/LaunchAgents ~/Library/Logs/underside-ai
cp automation/be.underside.ai.daily-publisher.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/be.underside.ai.daily-publisher.plist
launchctl enable gui/$(id -u)/be.underside.ai.daily-publisher
```

## Uninstallation

```sh
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/be.underside.ai.daily-publisher.plist
rm ~/Library/LaunchAgents/be.underside.ai.daily-publisher.plist
```

## Manual Start

Run the job through launchd:

```sh
launchctl kickstart -k gui/$(id -u)/be.underside.ai.daily-publisher
```

Or run the script directly from the repository:

```sh
./scripts/run_daily_ai_publisher.sh
```

## Stop

```sh
launchctl kill TERM gui/$(id -u)/be.underside.ai.daily-publisher
```

If a stale lock remains after an interrupted run and no publisher process is active:

```sh
rmdir /tmp/underside-ai-daily-publisher.lock
```

## Logs

List recent logs:

```sh
ls -lt ~/Library/Logs/underside-ai
```

Follow launchd stderr/stdout:

```sh
tail -f ~/Library/Logs/underside-ai/launchd.err.log ~/Library/Logs/underside-ai/launchd.out.log
```

Follow the latest publisher run:

```sh
tail -f "$(ls -t ~/Library/Logs/underside-ai/daily-publisher-*.log | head -n 1)"
```

## Verify LaunchAgent

Check plist syntax:

```sh
plutil -lint automation/be.underside.ai.daily-publisher.plist
```

Check launchd state:

```sh
launchctl print gui/$(id -u)/be.underside.ai.daily-publisher
```

Check the next scheduled run in Console.app or by inspecting launchd state after loading.

## Troubleshooting

- If the script exits before Codex starts, check that the repository is on `main`, synchronized with `origin/main`, and clean.
- If Codex is not found, verify that `codex` exists under `/Users/christophedegraeve/.local/bin` or another directory included in the script `PATH`.
- If no publication is made, inspect the run log; "publish nothing" is expected when no official, relevant, non-duplicate topic is available.
- If staging fails, inspect `/tmp/underside-ai-daily-publisher-manifest.txt` and `git status --porcelain`. The script stages only files listed in the manifest.
- If launchd cannot start the job, verify the absolute script path in the plist and reload it with `launchctl bootout` followed by `launchctl bootstrap`.
