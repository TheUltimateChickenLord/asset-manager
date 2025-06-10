#!/bin/bash

SECRET_KEY=$(openssl rand -hex 32)
> ".env"
cat <<EOF > ".env"
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SQLALCHEMY_DATABASE_URL=sqlite:///./asset_manager.db
LOG_DIR=logs
EOF

pip install poetry
python -m venv .venv
poetry self add poetry-dotenv-plugin
poetry install