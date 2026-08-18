# Spark + PySpark em Docker

Duas formas de usar, dependendo do que você precisa:

- **Modo single-container** (`docker run`) — Spark em `local[*]`, tudo num processo só. Bom pra testar código rápido.
- **Modo cluster** (`docker compose`) — master + worker(s) + driver em containers separados, de verdade. Bom pra *ver* na prática o que o guia de Spark descreve (driver coordenando, master alocando, worker hospedando executor).

## Modo single-container

```bash
docker build -t spark-study:3.5.6 .
docker run -it --rm spark-study:3.5.6 pyspark
```

## Modo cluster (docker compose)

```bash
docker compose up --build
```

Isso sobe 3 serviços:

| Serviço | Papel | UI |
|---|---|---|
| `spark-master` | Cluster Manager — aloca recursos, não roda seu código | http://localhost:8080 |
| `spark-worker` | Máquina que hospeda o(s) executor(s) | http://localhost:8081 |
| `spark-submit` | Onde o Driver roda (client mode) — executa `test_spark.py` | http://localhost:4040 (só enquanto o job roda) |

Pra simular mais paralelismo com múltiplos workers:

```bash
docker compose up --build --scale spark-worker=3
```

Pra rodar seu próprio script em vez do `test_spark.py`, edite o `command` do serviço `spark-submit` no `docker-compose.yml`, ou suba só master+worker e rode manualmente:

```bash
docker compose up -d spark-master spark-worker
docker compose run --rm spark-submit spark-submit --master spark://spark-master:7077 /app/seu_script.py
```

## Mapeamento pros conceitos do guia de entrevista

- **Driver** → o processo `spark-submit` (container `spark-submit`). É ele que roda seu código Python, constrói o DAG e conversa com o master.
- **Cluster Manager** → `spark-master`. Não processa dados, só decide quais workers têm recursos livres.
- **Worker** → `spark-worker`. É a "máquina" — pode hospedar um ou mais **executors** dentro dele, dependendo de `--cores`/`--memory`.
- **Executor** → processo que o worker sobe *dentro dele* quando o master aloca recursos pra sua aplicação. Não é um container separado — é um processo filho dentro do container do worker (você vê ele aparecer no log do worker quando o job começa a rodar).

Se quiser ver isso acontecendo ao vivo: suba o cluster, abra a UI do master (`:8080`) numa aba antes de rodar o job — você vai ver o worker registrado, e quando o `spark-submit` rodar, vai aparecer uma aplicação e um executor alocado nela.

## Notas

- Não existe Spark 3.9 — a série 3.x vai até 3.5.x (última: 3.5.6). Usei essa por ser a mais próxima do que roda no Databricks Runtime hoje. Pra testar a linha nova (4.x, atualmente 4.1.x), troque o `ARG SPARK_VERSION` no Dockerfile.
- Esse cluster ainda é local (containers na sua máquina, não em nós físicos separados) — mas a topologia de processos (driver, master, worker, executor) é a mesma de um cluster real. É o suficiente pra entender e explicar o modelo em entrevista.
- Não testei o `docker compose up` fim a fim neste ambiente porque o sandbox aqui não tem daemon Docker disponível — validei a sintaxe do `docker-compose.yml` e do Dockerfile, mas vale você rodar aí e me mandar o log se algo não subir.