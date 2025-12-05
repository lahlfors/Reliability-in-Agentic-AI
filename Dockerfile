# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Install system dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python3 -

# Setup working directory
WORKDIR $PYSETUP_PATH

# Copy project dependency files
COPY financial-advisor/pyproject.toml financial-advisor/poetry.lock ./

# Install runtime dependencies - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --without dev,deployment --no-root

# Copy application code
WORKDIR /app
COPY . .

# Install the project itself
# We need to tell poetry where the pyproject.toml is now relative to code?
# Actually, let's just use the installed venv and run from there.
# We need to install the packages `financial-advisor` and `vacp` and `observability` into the venv.
# Since `pyproject.toml` is in `financial-advisor/`, we should install from there.

# Re-install with root to link the packages
WORKDIR $PYSETUP_PATH
# We need to copy the source code to where poetry expects it if we use `poetry install`.
# But `vacp` and `observability` are outside `financial-advisor`.
# The `pyproject.toml` in `financial-advisor` likely has path dependencies or assumes a structure.
# Let's check `financial-advisor/pyproject.toml`.

# If `vacp` and `observability` are not packages in `pyproject.toml`, we just need them in PYTHONPATH.
# If they are packages, we need to `pip install` them.

# Let's set PYTHONPATH to include /app so `vacp` and `observability` are importable.
ENV PYTHONPATH=/app

# Default port
ENV PORT=8001

# Run the web server
# We use the venv python to run `adk web` from the `financial-advisor` directory.
WORKDIR /app/financial-advisor
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8001"]
