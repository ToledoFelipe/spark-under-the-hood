# Setup — Windows 11 (PowerShell)

Prerequisites and installation steps to run this lab locally. Written for Windows 11 with PowerShell, on the AMD64/Intel architecture.

## Machine specs

### Minimum to run this lab comfortably

The `docker-compose.yml` cluster runs 3 containers at once (master + worker + driver), plus WSL2 and Docker Desktop's own overhead, plus the ~1.5-2GB dataset used in the exercises.

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 4 logical cores | 8+ (compose worker alone is configured for 2 cores; leave headroom for master/driver/Docker/WSL2) |
| RAM | 8GB | 16GB+ (worker is capped at 2g, but WSL2 + Docker Desktop + your IDE also compete for RAM) |
| Free disk | 10GB | 20GB+ (Docker images, the dataset, exercise output files, and WSL2's virtual disk all grow over time) |
| OS | Windows 11 (or Windows 10 21H2+), 64-bit | Windows 11 |

### Check your own machine's specs

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfLogicalProcessors
[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB, 1)
Get-PSDrive C | Select-Object Used, Free
```

## Install Docker Desktop

1. Confirm your architecture is AMD64/x64 (not ARM64) with `$env:PROCESSOR_ARCHITECTURE` — the installer differs by architecture.
2. Download **Docker Desktop for Windows (AMD64)** from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).
3. Run the installer. Keep **"Use WSL 2 instead of Hyper-V"** checked (default) — it's lighter and is what this repo's setup assumes.
4. Restart Windows if the installer asks for it.
5. Launch Docker Desktop and let it finish onboarding (it installs/updates the WSL2 backend automatically if needed).

### Verify WSL2 is set up

```powershell
wsl --status
wsl -l -v
```

You should see a `docker-desktop` distro listed as `Running`. If `wsl --status` errors out or WSL looks outdated, run `wsl --update`.

### Verify the install

```powershell
docker --version
docker compose version
docker run hello-world
```

If PowerShell says `docker` is not recognized right after installing, **close and reopen your terminal** (and restart VS Code if you're using its integrated terminal) — the installer adds Docker Desktop's `resources\bin` folder to your user `PATH`, but already-open shell sessions don't pick up the change until restarted.

## Run this repo's cluster

```powershell
cd docker
docker compose up --build
```

Then check the UIs come up:
- Master — http://localhost:8080
- Worker — http://localhost:8081
- Driver/application (only while a job runs) — http://localhost:4040

See the main [README.md](README.md) for what each service does, and [exercises/](exercises/) for hands-on practice once the cluster is running.

## Debugging with Attach to Running Container

Real breakpoints and step-through debugging inside the exact container where PySpark is installed — no rebuild needed to iterate.

1. Install the **Dev Containers** extension in VS Code (`ms-vscode-remote.remote-containers`).
2. Start the cluster in the background:
   ```powershell
   cd docker
   docker compose up -d
   ```
3. `Ctrl+Shift+P` → **Dev Containers: Attach to Running Container** → pick `spark-submit`. A new VS Code window opens with that container's filesystem.
4. In the new window: **File → Open Folder** → `/app` (this is the repo root, bind-mounted from your host). Install the Python extension when prompted, and select the interpreter that has `pyspark` installed.
5. Open a script under `scripts/`, set a breakpoint, and press **F5**. This repo already ships a `.vscode/launch.json` with a "Python: Debug Current File (Spark cluster)" config, so F5 just works.

Two things that make this work without `spark-submit`:

- The scripts run with plain `python`, not `spark-submit` — `spark-submit` is just a wrapper, and the `pyspark` pip package already has everything needed to start a driver directly.
- Because `python script.py` alone would default to `local[*]` (in-process, not the real cluster), the scripts read the master URL from the `SPARK_MASTER_URL` env var (defaulting to `spark://spark-master:7077`) and set it explicitly via `.master(...)`. The `launch.json` config sets that env var for you, so F5 connects to the real `spark-worker` container — you'll see the executor register in the master UI (`:8080`) exactly like a `spark-submit` run.
