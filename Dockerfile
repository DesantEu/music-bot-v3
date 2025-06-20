FROM python:3.13 AS base
WORKDIR /app

# install deps
COPY reqs.txt .
RUN pip install -r reqs.txt

# get ffmpeg
RUN command -v ffmpeg >/dev/null || \
    apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# copy source
COPY src ./

# default run
ENTRYPOINT ["python", "-u", "main.py"]