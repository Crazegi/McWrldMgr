# mcworldmgr

CLI app to inspect and safely modify Minecraft Java worlds (vanilla-focused, 1.20+).

## Features in this version

- Auto-detect saves directory on Windows with manual override.
- Read-only world inspector.
- Backup and restore snapshots.
- World metadata edits (name, difficulty, game mode).
- Gamerule edits.
- Advanced world edits (time/weather/spawn/world border/hardcore/allow commands/seed).
- Player edits (position, health, hunger, selected inventory slot).
- Player kill and player data delete actions.
- Region operations (list/delete region files; chunk reset by region selection).
- Entity operations (list/delete entity region files, delete all entity regions, queue summon/kill commands).

## Safety

- Before every write command, the CLI prompts whether to create a backup.
- Writes are atomic when updating `level.dat` and player data files.
- The app checks for `session.lock` and warns before writes.

## Install

```powershell
cd "c:\Users\Cayman\Documents\Python Codes\App"
python -m pip install -e .
```

## Quick start

```powershell
mcworldmgr worlds list
mcworldmgr inspect --world "MyWorld"
mcworldmgr backup create --world "MyWorld"
mcworldmgr world set --world "MyWorld" --name "New Name" --difficulty hard --gamemode survival
mcworldmgr gamerule set --world "MyWorld" --rule keepInventory --value true
mcworldmgr player set --world "MyWorld" --uuid <player-uuid> --x 100 --y 70 --z -20 --health 20 --hunger 20
mcworldmgr player kill --world "MyWorld" --uuid <player-uuid>
mcworldmgr player delete --world "MyWorld" --uuid <player-uuid>
mcworldmgr world advanced-set --world "MyWorld" --time 6000 --weather clear --spawn-x 0 --spawn-y 80 --spawn-z 0
mcworldmgr regions list --world "MyWorld"
mcworldmgr entity queue-summon --world "MyWorld" --entity minecraft:zombie --x 0 --y 64 --z 0
mcworldmgr entity queue-kill --world "MyWorld" --selector "@e[type=minecraft:zombie]"
```

## GUI

Start the GUI:

```powershell
python -m mcworldmgr.gui_main
```

Or double-click [run_gui.bat](run_gui.bat). It launches via `pythonw` so no persistent terminal window is shown.

In the GUI:

- Use **World Selection** at the top (auto-detected world dropdown or manual world path/name).
- Use tabs for all actions: **Inspect**, **Backup**, **World**, **Gamerule**, **Player**, **Entity**, **Regions**.
- Write/destructive actions show confirmation dialogs and ask if backup should be created first.
- Backup/restore actions run in background and show file-count progress.
- Queued entity commands are written to `mcworldmgr_commands/queued_commands.mcfunction` inside the selected world.

## GitHub release builds

- CI tests run on pushes/PRs to `main` via [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- On every published GitHub Release, [`.github/workflows/release-windows.yml`](.github/workflows/release-windows.yml) builds Windows executables:
	- `mcworldmgr-cli.exe`
	- `mcworldmgr-gui.exe`
	- `mcworldmgr-windows.zip`
- Built files are attached to the Release automatically.
- To attach assets to an already published release tag (for example `1.0.0`), run [`.github/workflows/attach-existing-release.yml`](.github/workflows/attach-existing-release.yml) from the Actions tab and enter the tag.

## Notes

- Use the world folder name or absolute path with `--world`.
- Prefer editing worlds while Minecraft/server is not running.
- Keep backups outside cloud-sync conflict scenarios while editing.
