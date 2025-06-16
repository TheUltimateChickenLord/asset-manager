# Asset Manager
This is a backend api for an asset management system. It is written in python.

## Prerequisites
- Python at least version `3.9` but `3.13` is recommended
- This repo cloned

## Installation
This project uses [poetry](https://python-poetry.org/) for packaging and dependency management.

### Automatic
Run the following command to set up the repo for you
```bash
bash setup.sh
```

### Manual
1. Install poetry (requires administrator terminal)
```bash
pip install poetry
```
2. Create a virtual environment (do not activate it)
```bash
python -m venv .venv
```
3. Install poetry dotenv plugin (required for loading environment files into your poetry code)
```bash
poetry self add poetry-dotenv-plugin
```
4. Install all python dependencies (using poetry not pip)
```bash
poetry install
```
5. Create a file called `.env` in the root of the repo with the following information
```
SECRET_KEY=<SECRET_KEY>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SQLALCHEMY_DATABASE_URL=sqlite:///./asset_manager.db
LOG_DIR=logs
```
6. Replace the placeholder `<SECRET_KEY>` above with the output from the following command (this is your JWT secret and should never be shared)
```bash
openssl rand -hex 32
```

## Optional Setup
You can reset the database with new random values by running the following command
```bash
poetry run seed
```
To see the new users, you will need to manually open the database with an sqlite3 viewing tool (there are vscode plugins to do this like qwtel.sqlite-viewer), the first user is the `admin` who can do anything including user management, the second is a `manager` who can do anything related to assets but not users, everyone else is a standard `user` with standard permissions.

## Usage
To actually run the FastAPI app, use the following command (your app will run at http://localhost:8000)
```bash
poetry run start
```
To view the OpenAPI docs, visit http://localhost:8000/docs

## Testing and Linting
Unit tests are run with the following command
```bash
poetry run test
```
Pylint (checking code conforms to PEP standards) is run with the following command
```bash
poetry run lint
```

## Current Credentials
With the database in its current state, the usernames can be seen in the following list, all passwords are set to `Password123!`

| Email                      | Roles                                            |
| -------------------------- | ------------------------------------------------ |
| kim62@example.net          | Admin (All roles)                                |
| yparker@example.org        | Manager (All roles except User management roles) |
| ymccarthy@example.org      | User (ReadAsset, RequestAsset)                   |
| davidsoto@example.org      | User (ReadAsset, RequestAsset)                   |
| rebeccashields@example.org | User (ReadAsset, RequestAsset)                   |
| carolwells@example.com     | User (ReadAsset, RequestAsset)                   |
| itravis@example.org        | User (ReadAsset, RequestAsset)                   |
| kathrynhall@example.com    | User (ReadAsset, RequestAsset)                   |
| dianaparks@example.org     | User (ReadAsset, RequestAsset)                   |
| zimmermansusan@example.com | User (ReadAsset, RequestAsset)                   |
