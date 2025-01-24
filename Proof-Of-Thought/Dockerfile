FROM ubuntu:22.04

# python 3.10
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get install -y python3.10 python3.10-venv python3.10-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# python3 points to python3.10
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1

# pip
RUN apt-get update && apt-get install -y \
    python3-pip

# dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    libffi-dev \
    python3-dev \
    xinetd \
    && rm -rf /var/lib/apt/lists/*

# ollama
# RUN curl -fsSL https://ollama.ai/install.sh | sh


# solver user
RUN useradd -d /home/pot -u 8888 -m pot
USER pot

COPY --chown=pot:pot xinetd /etc/xinetd.d/xinetd
COPY --chown=pot:pot . /home/pot

# working dir
WORKDIR /home/pot
RUN chmod +x ./run.sh

# ollama
USER root
RUN curl -fsSL https://ollama.com/install.sh | sh

# ollama model
USER pot
RUN (ollama serve &) && sleep 10 && ollama pull llama3.1:latest

# dependencies
RUN pip install --no-cache-dir -r ./requirements.txt

# pre-download datasets
RUN python3 -c "from datasets import load_dataset; load_dataset('gsm8k', 'main'); load_dataset('cais/mmlu', 'all')"

# start
CMD (ollama serve &) && /usr/sbin/xinetd -dontfork