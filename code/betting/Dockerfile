FROM python:3.11-slim-bookworm

# Build deps for any C extensions; h5py and pynwb may need them depending on
# the wheel availability on the target platform.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Script + figures mounted at runtime via docker-compose.
CMD ["python", "head_direction_betting.py"]
