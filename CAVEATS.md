# Caveats — dev-only patterns, don't ship these

Things set up in this repo purely for local study/debugging convenience that would be wrong in a real deployment. Read this before copying anything from here into production code.

## `spark-submit` runs idle (`tail -f /dev/null`)

In `docker-compose.yml`, the `spark-submit` service doesn't run a job and exit — it stays up forever doing nothing, so you can `docker compose exec` or VS Code "Attach to Running Container" into it whenever you want (see [SETUP.md](SETUP.md)).

**Remember to shut it down when you're not actively debugging:**

```bash
docker compose down
# or, to stop just this one and keep master/worker up:
docker compose stop spark-submit
```

Why this matters:

- **It's holding resources for nothing.** An idle container still reserves memory/CPU accounting and a port (`4040`) — no different from leaving a VM running overnight.
- **It hides the signal that actually matters in production.** A real `spark-submit` process's exit code is how orchestrators (Airflow, a Kubernetes Job, an EMR step) know whether the job succeeded or failed and whether to retry/alert. An idle container never exits, so that signal never exists.
- **An idle shell is unnecessary attack surface.** A container sitting there with a shell available, doing nothing, is exactly the kind of thing that's easy to forget about — and easy for something else to find.

In production, `spark-submit` should be **ephemeral by design**: a Kubernetes `Job` (not a `Deployment`), or an orchestrator step that starts it, waits for completion, and tears it down. The idle pattern here exists only to make local F5-debugging convenient — never carry it into a real deployment.
