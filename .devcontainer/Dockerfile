# ============================================================================
# DMarket Telegram Bot - Development Container Dockerfile
# ============================================================================
# Optimized for GitHub Codespaces and VS Code Dev Containers
# Python 3.12+ with full development toolchain
# Last updated: January 2026
# ============================================================================

# Use official Python 3.12 devcontainer base image
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# ============================================================================
# ARGUMENTS
# ============================================================================
ARG DEBIAN_FRONTEND=noninteractive
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/workspaces \
    # Poetry configuration
    POETRY_VERSION=1.8.4 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    # pip configuration
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    # Virtual environment path
    VIRTUAL_ENV=/workspaces/.venv \
    PATH="/workspaces/.venv/bin:$PATH"

# ============================================================================
# SYSTEM DEPENDENCIES
# ============================================================================
# Remove expired Yarn GPG key/repository from base image
RUN rm -f /etc/apt/sources.list.d/yarn.list 2>/dev/null || true && \
    rm -f /etc/apt/keyrings/yarn.gpg 2>/dev/null || true && \
    rm -f /usr/share/keyrings/yarn-keyring.gpg 2>/dev/null || true

RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    # PostgreSQL client and development files
    libpq-dev \
    postgresql-client \
    # Redis client
    redis-tools \
    # Git and version control
    git \
    git-lfs \
    # Network utilities
    curl \
    wget \
    httpie \
    # Text processing
    jq \
    ripgrep \
    fd-find \
    fzf \
    bat \
    # Process management
    htop \
    # Shell utilities
    zsh \
    zsh-autosuggestions \
    zsh-syntax-highlighting \
    # Locales
    locales \
    # Fonts for terminal
    fonts-powerline \
    # SQLite
    sqlite3 \
    libsqlite3-dev \
    # SSL/TLS
    ca-certificates \
    openssl \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================================
# LOCALE CONFIGURATION
# ============================================================================
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# ============================================================================
# POETRY INSTALLATION
# ============================================================================
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# ============================================================================
# PRE-COMMIT AND DEVELOPMENT TOOLS
# ============================================================================
RUN pip install --no-cache-dir \
    pre-commit \
    pip-tools \
    pipx \
    cookiecutter

# ============================================================================
# ZSH CONFIGURATION FOR USER
# ============================================================================
USER ${USERNAME}

# Oh My Zsh plugins
RUN git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions 2>/dev/null || true && \
    git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting 2>/dev/null || true

# ============================================================================
# SHELL ALIASES AND FUNCTIONS
# ============================================================================
RUN echo '\n\
# DMarket Bot Development Aliases\n\
alias ll="ls -alF"\n\
alias la="ls -A"\n\
alias l="ls -CF"\n\
\n\
# Python aliases\n\
alias py="python"\n\
alias pip="python -m pip"\n\
alias pytest="python -m pytest"\n\
alias mypy="python -m mypy"\n\
alias ruff="python -m ruff"\n\
\n\
# Project aliases\n\
alias bot="python -m src.main"\n\
alias test="make test"\n\
alias lint="make lint"\n\
alias fix="make fix"\n\
alias check="make check"\n\
alias qa="make qa"\n\
\n\
# Docker aliases\n\
alias dc="docker compose"\n\
alias dps="docker ps"\n\
alias dlogs="docker compose logs -f"\n\
\n\
# Git aliases\n\
alias gs="git status"\n\
alias gd="git diff"\n\
alias ga="git add"\n\
alias gc="git commit"\n\
alias gp="git push"\n\
alias gl="git pull"\n\
alias glog="git log --oneline -20"\n\
\n\
# Quick navigation\n\
alias src="cd /workspaces/DMarket-Telegram-Bot/src"\n\
alias tests="cd /workspaces/DMarket-Telegram-Bot/tests"\n\
alias docs="cd /workspaces/DMarket-Telegram-Bot/docs"\n\
\n\
# Safety first - DRY_RUN by default\n\
export DRY_RUN=true\n\
\n\
# Colorful output\n\
export FORCE_COLOR=1\n\
' >> ~/.bashrc

RUN echo '\n\
# DMarket Bot Development Aliases for ZSH\n\
alias ll="ls -alF"\n\
alias la="ls -A"\n\
alias l="ls -CF"\n\
\n\
# Python aliases\n\
alias py="python"\n\
alias pip="python -m pip"\n\
alias pytest="python -m pytest"\n\
alias mypy="python -m mypy"\n\
alias ruff="python -m ruff"\n\
\n\
# Project aliases\n\
alias bot="python -m src.main"\n\
alias test="make test"\n\
alias lint="make lint"\n\
alias fix="make fix"\n\
alias check="make check"\n\
alias qa="make qa"\n\
\n\
# Docker aliases\n\
alias dc="docker compose"\n\
alias dps="docker ps"\n\
alias dlogs="docker compose logs -f"\n\
\n\
# Git aliases\n\
alias gs="git status"\n\
alias gd="git diff"\n\
alias ga="git add"\n\
alias gc="git commit"\n\
alias gp="git push"\n\
alias gl="git pull"\n\
alias glog="git log --oneline -20"\n\
\n\
# Quick navigation\n\
alias src="cd /workspaces/DMarket-Telegram-Bot/src"\n\
alias tests="cd /workspaces/DMarket-Telegram-Bot/tests"\n\
alias docs="cd /workspaces/DMarket-Telegram-Bot/docs"\n\
\n\
# Safety first - DRY_RUN by default\n\
export DRY_RUN=true\n\
\n\
# Colorful output\n\
export FORCE_COLOR=1\n\
' >> ~/.zshrc

# ============================================================================
# SWITCH BACK TO ROOT FOR FINAL SETUP
# ============================================================================
USER root

# ============================================================================
# HEALTHCHECK
# ============================================================================
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD python --version || exit 1

# ============================================================================
# DEFAULT COMMAND
# ============================================================================
CMD ["sleep", "infinity"]
