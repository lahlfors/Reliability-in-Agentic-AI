# Dockerfile
FROM python:3.11-slim

# 1. Set up environment
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 2. System dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 3. Install dependencies
# We copy pyproject.toml / requirements.txt first for caching
COPY financial-advisor/pyproject.toml financial-advisor/poetry.lock* /app/
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# 4. Copy the Application Code
# We need both the governance library (vacp) and the agent
COPY vacp /app/vacp
COPY financial-advisor /app/financial-advisor

# 5. Copy the Governance Artifacts (Crucial!)
# The agent.json and its signature must be present for the CardLoader
COPY financial-advisor/agent.json /app/financial-advisor/agent.json
COPY financial-advisor/agent.json.sig /app/financial-advisor/agent.json.sig

# 6. Service Entrypoint
# Pointing to adk web as the entrypoint
WORKDIR /app/financial-advisor
CMD ["sh", "-c", "adk web --host 0.0.0.0 --port ${PORT:-8080}"]
