# CPU image: runs the whole pipeline (mock and real VLMs), the tests and the reports.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/cache/huggingface \
    MPLBACKEND=Agg

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only torch first (much smaller than the default CUDA build), then the project deps
# pinned to the exact versions the results were produced with (constraints.txt).
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1 torchvision==0.29.1

COPY pyproject.toml README.md constraints.txt ./
COPY src ./src
RUN pip install -c constraints.txt -e ".[vlm,similarity,dev]"

COPY configs ./configs
COPY scripts ./scripts
COPY tests ./tests
COPY Makefile ./

# data/ (nuScenes), outputs/ and the model cache are mounted as volumes.
ENTRYPOINT ["vlm-eval"]
CMD ["--help"]
