# Word Wizards - container for Hugging Face Spaces (Docker SDK)
FROM python:3.11-slim

# xgboost needs the OpenMP runtime
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

# run as a normal user (works on Render, Hugging Face, Docker)
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

COPY --chown=user requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

COPY --chown=user . .
USER user

EXPOSE 7860
# Render sets $PORT; default 7860 elsewhere
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
