# Jev Bookmarks

[日本語のREADME](README.md) · [Design and acceptance criteria](docs/design.md)

Jev Bookmarks is a CLI that finds a starting page in your Chrome history, lets Jev operate the browser, and keeps only pages Jev judged useful in a small, project-scoped address book.

**Status:** preview for macOS, Windows, and Linux, callable from Claude Code, Codex, Cursor, and Grok Build. History and browser operation use the same dedicated Chrome profile owned by Jev Bookmarks. The extension is loaded once as an unpacked extension.

## After setup

Run one command from any directory inside the target Git project:

```sh
jev-bookmarks run 'Show the Example Domain page'
```

The command first checks `<git-root>/jev-bookmark/bookmarks.json`, then asks the Chrome extension for history candidates if needed. Jev selects an existing URL, `jev-ultrafast` operates Chrome, and Jev judges the page observed after the operation. Only a useful page is saved. The result is JSON; the parent agent does not need to choose or approve intermediate steps.

Version 0.3.6 pins Jev to the maintained source that follows the upstream execution sequence. Jev Bookmarks continues to own the separate usefulness judgment for address-book entries.

## Install (macOS, Windows, Linux)

You need Python 3.12, `uv`, Git, Google Chrome, a TypeSafe API key, and a working `jev-ultrafast` model configuration.

```sh
git clone https://github.com/kitepon/jev-bookmarks.git
cd jev-bookmarks
uv sync --locked
uv tool install --editable .
jev-bookmarks install \
  --typesafe-env /path/to/typesafe.env \
  --browser-env /path/to/jev-ultrafast.env
jev-bookmarks harness install
```

Put `TYPESAFE_API_KEY` in `typesafe.env` and the upstream model settings in the other env file. Jev Bookmarks owns the Chrome endpoint and ignores `BU_CDP_URL` and `BU_CDP_WS` from that file. Do not commit either file.

`install` starts regular Google Chrome with a dedicated Jev Bookmarks profile. It loads the fixed-ID history extension through that profile's loopback CDP endpoint and verifies the Native Messaging connection. No manual Developer mode setup is required. After installation, `status` should report `history_connected: true`.

The dedicated profile does not share cookies, logins, or history with everyday Chrome. Sign in to the required sites in that window. Later `run` calls reconnect both `jev-ultrafast` and history search to that exact profile under the dedicated `jev-bookmarks` Browser Harness name.

From your Git project, use `jev-bookmarks run`, `list`, or `forget <url>`. `jev-bookmarks status` reports whether the local history host is listening; a `run` checks the full history request path. On Windows, `install` also registers the host manifest under `HKCU\Software\Google\Chrome\NativeMessagingHosts`.

`jev-bookmarks harness install` adds a `jev-bookmarks` skill to every detected harness (`~/.claude/skills`, `$CODEX_HOME/skills`, `~/.cursor/skills`, `~/.grok/skills`) so the agent passes the goal to `run` once. Each copy carries that harness's notes on timeouts and sandboxing. Pass harness names to limit it, and use `jev-bookmarks harness status` to check. A skill of the same name that you wrote yourself is left untouched.

Shared code, OS adaptation (`src/jev_bookmarks/platforms/`), and harness adaptation (`src/jev_bookmarks/harnesses/`) live in separate files.

## Data and limits

- The project address book stores the goal, full observed URL, title, and time locally. Its JSON and temporary files are ignored by Git. Old machine-wide address books are not migrated automatically.
- Full Chrome history is not copied to disk. Jev receives at most 80 candidate titles and host/path displays for URL selection. A portion of the observed page text is sent to TypeSafe for usefulness judgment. The upstream browser agent uses the model connection configured for it.
- URLs and visible page text can contain sensitive information. Inspect the providers and data sent before using private pages. Never paste real account pages or keys into public issues.
- The previous macOS path was exercised end to end with real Chrome history. The dedicated-profile launch, private CDP endpoint, and Browser Harness routing were verified by observing a public page through `jev-ultrafast.Agent`; a new end-to-end run on a signed-in dedicated profile remains. On Windows the real-history round trip through the extension and named pipe, and on Linux the round trip through the extension and Unix socket in a test profile, have been verified; a full `run` with TypeSafe and browser operation has not yet been verified there. All four harnesses were checked to see the skill on all three OSes.

For the full walkthrough, evidence, and current limitations, see the [Japanese README](README.md). Bug reports and contributions are welcome through [Issues](https://github.com/kitepon/jev-bookmarks/issues) and [CONTRIBUTING.md](CONTRIBUTING.md). Report vulnerabilities as described in [SECURITY.md](SECURITY.md). Licensed under the [MIT License](LICENSE).
