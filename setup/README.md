RUNNING.md
===========

This document explains how to run the services in this repository on Windows and on Linux/WSL.

Files you can use
- `Makefile`         — original POSIX Makefile (works in Git Bash or WSL/Linux)
- `Makefile.win`     — Windows-optimized Makefile (use with GNU make from Chocolatey)
- `make-windows.ps1` — PowerShell wrapper that implements the same targets (up/down/logs)

Quick overview
- Use the original `Makefile` in a Unix-like shell (Git Bash or WSL) with `make up`.
- On Windows PowerShell you can either use `make -f Makefile.win <target>` (requires GNU make) or `.\make-windows.ps1 <target>` (PowerShell script).

Prerequisites (Windows)
- Docker Desktop installed and running. Use Linux containers (WSL2 backend recommended).
- If you plan to use `Makefile.win` you need GNU make. Install via Chocolatey:

```powershell
choco install make -y
```

- Alternatively use PowerShell script (`make-windows.ps1`) which does not require GNU make.

Prerequisites (Linux / WSL)
- Docker and docker-compose (or Docker Desktop with WSL2 integration enabled so `docker` works in WSL).
- make (usually preinstalled on many distros).

Running (Windows — PowerShell)

1) Using `Makefile.win` (GNU make via Chocolatey):

```powershell
# From the repo's `setup` folder
make -f Makefile.win up

# stop
make -f Makefile.win down

# logs
make -f Makefile.win logs
```

2) Using the PowerShell wrapper (no make required):

```powershell
# From the repo's `setup` folder
.\make-windows.ps1 up
.\make-windows.ps1 down
.\make-windows.ps1 logs
```

If PowerShell blocks script execution, run temporarily with an execution policy bypass:

```powershell
pwsh -ExecutionPolicy Bypass -File .\make-windows.ps1 up
```

Running (Linux / WSL / Git Bash)

```bash
# From the repo's setup folder
make up
make down
make logs
```

Environment variables and `.env`
- The docker-compose stacks may read environment variables (for example `REDIS_PASSWORD`). If you see warnings like:

```
The "REDIS_PASSWORD" variable is not set. Defaulting to a blank string.
```

set the variable in the shell or create a `.env` file next to the compose file with `REDIS_PASSWORD=your_password`.

Troubleshooting
- Named-pipe error (Windows):

```
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

This indicates Docker Desktop isn't reachable. Fixes:
  - Start Docker Desktop and wait until it reports "Running".
  - Ensure Docker is using Linux containers (right-click the Docker tray icon → switch to Linux containers if needed).
  - Verify from PowerShell: `docker version` and `docker info` should return without errors.

- If `docker` works in WSL but not in PowerShell, prefer running `make up` from WSL (or enable WSL2 integration in Docker Desktop).

- If a compose image cannot be found/pulled, ensure internet access and that Docker can pull images. Example: `chirpstack/chirpstack-gateway-bridge:4` is a Linux image and requires Linux containers.

Notes about file/folder names
- The repository contains a folder named `persistance` (with an `a`) in some places. The project Makefiles were originally written to reference `persistence` (e). Two helper artifacts exist to reduce friction:
  - `Makefile.win` uses the folder names present in this repo. If you prefer the original names, either rename the folder to `persistence` or edit the Makefile(s) to match.
  - `make-windows.ps1` and `Makefile.win` will warn/skip if a `docker-compose.yml` is missing for a service.

Advanced: dry-run or skip checks
- If you want to preview commands without running them, use the PowerShell script and modify it to print commands (or set a DRY_RUN flag in the script). If you want me to add a `DRY_RUN` mode to `Makefile.win` or `make-windows.ps1`, I can update them.

Summary
- For reliability on Windows: start Docker Desktop (Linux containers) then run `make -f Makefile.win up` or `.\make-windows.ps1 up`.
- For parity with Linux: use WSL and `make up`.

If you want, I can:
- Add a `DRY_RUN`/preview target to `Makefile.win` and the PowerShell script,
- Normalize folder names (rename `persistance` → `persistence`) across the repo, or
- Add `.env` templates for required environment variables.
