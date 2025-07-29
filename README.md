
python-technical-test
======================

This project manages data related to **Sites** and **Groups**, allowing flexible associations and country-specific business logic.

Overview
--------

Sites represent individual installations with technical parameters, while Groups organize these sites by shared characteristics. Each group can contain multiple sites or subgroups (recursive). Country-specific logic applies to sites in France and Italy, with extendibility for more.

Project Structure
-----------------

- FastAPI app with modular routers (`/sites`, `/groups`, `/group_types`, `/auth`)
- SQLAlchemy models with Alembic migrations
- JWT-based authentication
- Full CRUD, filtering, and sorting
- Test suite with Pytest
- Seed scripts for initial data
- Docker-ready setup

Business Rules
--------------

- **French Sites**:
  - Only one can be installed per day.
- **Italian Sites**:
  - Must be installed on weekends.
  - Use `efficiency` instead of `useful_energy_at_1_megawatt`.
- **Sites cannot be added to groups of type `group3`**

Setup & Installation
--------------------

### Via Uvicorn (local dev)

1. Create virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```
   alembic upgrade head
   ```

4. Seed initial data:
   ```
   python app/seed_user.py
   python app/seed_group_types.py
   ```

5. Run the API:
   ```
   uvicorn app.main:app --reload
   ```

### Via Docker

```
docker compose build --no-cache
```

```
docker compose up
```

API will be available at: `http://localhost:8000/docs`

Deleting pycache
------------------

```
find . -type d -name "__pycache__" -exec rm -r {} +
```

Running Migrations
------------------

Create:
```
alembic revision --autogenerate -m "migration message"
```

Apply:
```
alembic upgrade head
```

Reset:
```
rm app/infrastructure/migrations/versions/*.py
```

Testing
-------

Run all tests:
```
pytest
```

Test coverage includes:
- French/Italian site creation & validation
- Filtering, sorting, updating, and deleting sites/groups/group_types
- Auth and token validation
- Error handling for invalid inputs or constraints

Endpoints Summary
-----------------

### /auth
- `POST /auth/login` – Get token with username/password

### /sites
- `GET` – List sites (with filters/sorting)
- `POST` – Create site with validations
- `PATCH` – Update a site
- `DELETE` – Delete a site

### /groups
- `GET` – List groups (filter by name, sort)
- `POST` – Create group
- `PUT` – Update group
- `DELETE` – Delete group

### /group_types
- `GET` – List types
- `POST` – Create type (no duplicates)
- `PUT` – Update
- `DELETE` – Remove

Good Practices
--------------

- Structured modular layout (`routers`, `models`, `utils`, `db`)
- Pydantic validation at request layer
- Async SQLAlchemy sessions with FastAPI dependencies
- JWT token with expiration for security
- Clear naming & business logic encapsulation
- Strict test coverage before deployment

Developer Shortcuts
-------------------

- Run API: `make run` or `uvicorn app.main:app --reload`
- Seed DB: `python app/seed_user.py`, `app/seed_group_types.py`
- Format: `black . && isort .`
- Lint: `flake8 .`
- Test: `pytest`

Author
------

Developed as part of a technical test demonstrating best practices, robustness, and adaptability for future extensions.
