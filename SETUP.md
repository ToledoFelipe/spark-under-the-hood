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

### Run everything from PowerShell (Windows), not WSL Ubuntu

If you also have a WSL distro (e.g. Ubuntu) installed, **don't** run `docker`/`docker compose` from inside it unless you've explicitly enabled Docker Desktop's WSL Integration for that distro (Settings → Resources → WSL Integration). Without that, a WSL Ubuntu terminal has no Docker daemon of its own and fails with `failed to connect to the docker API at unix:///var/run/docker.sock`.

This repo's containers are meant to be run from **PowerShell (or Git Bash) on Windows**, talking to Docker Desktop's engine directly — that's what all the commands in this doc assume.

This also bites VS Code's **Dev Containers** extension: if its `dev.containers.executeInWSL` setting is `true`, it tries to list/attach to containers *from inside WSL* instead of from Windows, and will report "no container running" even though `docker ps` in PowerShell shows them fine. Set it to `false` (or remove it) in VS Code's `settings.json` if you hit that.

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

## Performance testing — using more CPU/RAM for an isolated run

The default `spark-worker` (2 cores / 2g) is deliberately modest so the cluster doesn't fight your machine for resources during everyday dev. For a real performance test, there are **three ceilings**, in order — raising the container's limits alone does nothing if a layer above it is still capped:

1. **Docker Desktop's own VM.** With the WSL2 backend and no `.wslconfig`, Windows defaults to giving it *all* logical cores but only **50% of total RAM** — check your ceiling with `wsl --status` and `Get-CimInstance Win32_ComputerSystem` (total RAM) as a reference point. To raise the RAM ceiling, create `C:\Users\<you>\.wslconfig`:
   ```ini
   [wsl2]
   memory=24GB
   processors=14
   ```
   Then apply it with `wsl --shutdown` (Docker Desktop restarts its VM automatically on next use). Leave a couple of cores/GB of headroom for Windows itself and Docker Desktop's own overhead — don't set this to 100% of the host.

2. **The container's resource limit.** `docker-compose.yml` reads `SPARK_WORKER_CORES`/`SPARK_WORKER_MEMORY` (and `SPARK_DRIVER_CORES`/`SPARK_DRIVER_MEMORY` for `spark-submit`) as env vars, defaulting to the modest 2/2g if unset — so a normal `docker compose up` doesn't change. For a test run, set them higher:
   ```powershell
   $env:SPARK_WORKER_CORES = "10"
   $env:SPARK_WORKER_MEMORY = "18g"
   $env:SPARK_DRIVER_CORES = "2"
   $env:SPARK_DRIVER_MEMORY = "3g"
   docker compose up -d
   ```
   (Or put the same `KEY=value` lines in a `.env` file next to `docker-compose.yml` so you don't have to re-export every session.)

3. **Spark's own accounting.** The `--cores`/`--memory` flags the Worker process starts with are driven by those same env vars, so step 2 already covers this — but if you set them by hand instead, keep them equal to (not higher than) what Docker actually grants in step 2, or Spark will advertise capacity it can't back and executors will fail or get throttled.

### Keeping the test isolated (not just fast)

- Stick to a single worker (`--scale spark-worker=1`, the default) — one well-understood resource pool beats splitting the same total across several.
- Close other heavy apps/containers while measuring — you're trying to isolate Spark's behavior, not compete with Chrome for the same cores.
- Watch `docker stats` during the run to confirm you're actually using what you allocated, not silently capped somewhere.
- If you're comparing partition counts before/after (e.g. exercise 01), consider `spark.conf.set("spark.sql.adaptive.enabled", "false")` — Adaptive Query Execution can auto-coalesce shuffle partitions at runtime and mask the exact effect you're trying to measure.
- Run each scenario more than once and discard the first ("cold") run — JIT warmup and OS file-cache effects make the first run of anything look slower than steady state.
