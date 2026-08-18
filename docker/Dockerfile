# Imagem base de Spark + PySpark, usada tanto pro master quanto pro
# worker e pro cliente que faz spark-submit (ver docker-compose.yml).
# Obs: não existe Spark 3.9 (a série 3.x parou em 3.5.x). Usei a última
# versão estável da linha 3.x (3.5.6) por ser a mais próxima do que o
# Databricks Runtime costuma usar. Se preferir a linha mais nova (4.x),
# é só trocar SPARK_VERSION abaixo.

FROM python:3.11-slim

ARG SPARK_VERSION=3.5.6

# Java é dependência obrigatória do Spark (roda sobre a JVM).
# procps é usado internamente pelo Spark para checar processos/memória.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openjdk-17-jdk-headless \
        procps \
        curl && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# PySpark no PyPI já empacota o Spark inteiro (JVM + Python bindings).
# Pra uma imagem "básica" de estudo, isso evita ter que baixar o tarball
# do Spark separadamente e configurar SPARK_HOME manualmente.
RUN pip install --no-cache-dir \
        pyspark==${SPARK_VERSION} \
        ipython

# SPARK_HOME aponta pro Spark que veio dentro do pacote pyspark instalado
# via pip — é lá que ficam os binários que sobem master/worker (bin/spark-class),
# não só o pyspark shell.
ENV SPARK_HOME=/usr/local/lib/python3.11/site-packages/pyspark
ENV PATH="${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}"

WORKDIR /app
COPY test_spark.py /app/test_spark.py

# Portas usadas pelo cluster standalone: 7077 (master RPC), 8080 (UI do master),
# 8081 (UI do worker), 4040 (UI da aplicação/driver enquanto um job roda).
EXPOSE 7077 8080 8081 4040

# Sem CMD fixo: o docker-compose.yml define o comando de cada serviço
# (master, worker ou spark-submit). Rodando a imagem "crua" sem compose,
# cai num shell bash.
CMD ["bash"]