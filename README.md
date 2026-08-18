# Spark + PySpark on Docker

Two ways to use it, depending on what you need:

- **Single-container mode** (`docker run`) — Spark in `local[*]`, everything in a single process. Good for quickly testing code.
- **Cluster mode** (`docker compose`) — master + worker(s) + driver in separate containers, for real. Good for *seeing* in practice what the Spark guide describes (driver coordinating, master allocating, worker hosting the executor).

## Project structure

```
spark-under-the-hood/
├── README.md               → repo overview + quick start
├── SETUP.md                → machine specs, Docker install, debugging setup
├── CAVEATS.md              → dev-only patterns here that shouldn't reach production
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml → cluster: master + worker + driver
├── scripts/                → test/example scripts (e.g. test_spark.py)
├── notes/                  → study guide on Spark fundamentals
├── data/                   → sample data used by the scripts
├── exercises/              → roadmap of hands-on exercises to reinforce each concept
└── .gitignore
```

## Single-container mode

```bash
docker build -t spark-study:3.5.6 .
docker run -it --rm spark-study:3.5.6 pyspark
```

## Cluster mode (docker compose)

```bash
docker compose up --build
```

This brings up 3 services:

| Service | Role | UI |
|---|---|---|
| `spark-master` | Cluster Manager — allocates resources, doesn't run your code | http://localhost:8080 |
| `spark-worker` | Machine hosting the executor(s) | http://localhost:8081 |
| `spark-submit` | Where the Driver runs (client mode). Idle by default — jobs are triggered manually, see below. | http://localhost:4040 (only while a job is running) |

To simulate more parallelism with multiple workers:

```bash
docker compose up --build --scale spark-worker=3
```

`spark-submit` doesn't run a job automatically — it stays up (`tail -f /dev/null`) so you can `exec`/attach into it whenever you want. Run any script (the container mounts the whole repo at `/app`, so any path under `scripts/`, `notes/`, etc. works):

```bash
docker compose exec spark-submit spark-submit --master spark://spark-master:7077 /app/scripts/test_spark.py
```

## Interactive development (no rebuild)

Rebuild is only needed when the `Dockerfile` changes (new dependencies) — `.py` files don't need it. `spark-submit` stays up and idle by default, so just `exec` into it and re-run jobs as many times as you want:

```bash
docker compose up -d
docker compose exec spark-submit bash
# inside the container:
spark-submit --master spark://spark-master:7077 /app/scripts/your_script.py
```

Edits made on the host show up immediately inside the container. Same command works for `spark-master`/`spark-worker` if you need a shell in those instead. See [SETUP.md](SETUP.md) for setting up real breakpoint debugging via VS Code's "Attach to Running Container".

## Mapping to the interview-guide concepts

- **Driver** → the `spark-submit` process (container `spark-submit`). It runs your Python code, builds the DAG, and talks to the master.
- **Cluster Manager** → `spark-master`. Doesn't process data, just decides which workers have free resources.
- **Worker** → `spark-worker`. It's the "machine" — it can host one or more **executors** inside it, depending on `--cores`/`--memory`.
- **Executor** → the process the worker spins up *inside itself* when the master allocates resources for your application. It's not a separate container — it's a child process inside the worker's container (you'll see it show up in the worker's log when the job starts running).

Want to see it happen live? Bring up the cluster, open the master's UI (`:8080`) in a tab before running a job — you'll see the worker registered, and once you trigger `spark-submit` (see above), an application and an allocated executor will show up.

## Notes

- To test the new line (4.x, currently 4.1.x), change `ARG SPARK_VERSION` in the Dockerfile.
- This cluster is local (containers on your own machine, not separate physical nodes) — but the process topology (driver, master, worker, executor) is the same as a real cluster.
