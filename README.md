# python-technical-test

In this project, we manage data related to `sites` and `groups`. Sites represent individual installations, each with its own unique characteristics and attributes. On the other hand, groups serve as organizational units, grouping together sites based on common characteristics or functionalities.

By effectively managing both sites and groups within our system, we can efficiently organize and analyze data, enabling better decision-making and optimization of operations.

**Candidates are encouraged to feel free to use libraries of their choice and are welcome to include any additional enhancements they deem necessary or beneficial, such as unit tests, documentation, or performance optimizations. All additions that improve the overall quality and maintainability of the codebase are highly appreciated.**

## Project Description

### 1. Create the necessary models

**At least** two models are required:

#### Sites
- `id` (integer)
- `name` (string)
- `installation_date` (date)
- `max_power_megawatt` (float)
- `min_power_megawatt` (float)
- `useful_energy_at_1_megawatt` (float)

#### Groups
- `id` (integer)
- `name` (string)
- `type` (enum [group1, group2, group3])


A site can belong to multiple groups.  
A group can contain multiple sites.  
A group can contain multiple groups.

### 2. Create the necessary CRUD routes

We require the follwing routes:
- GET / POST / PATCH / DELETE `/sites`
- GET / POST / PATCH / DELETE `/groups`

Candidates are encouraged to implement filtering and sorting options in these routes to enhance the usability and flexibility of the API.

### 3. Additional Requirements

Currently, we only have french sites, but we want to add italian sites. These italian sites do not use the field `useful_energy_at_1_megawatt`. Instead, they have a field `efficiency` (float) specific to Italy.

Integrate these new Italian sites. (Many new countries with specific fields might be added in the future).

### 4. Integrate Business Logics
- Only one French site can be installed per day.
- Italian sites must be installed on weekends.
- No site can be associated with `group.type == "group3"`.

## Development

### Prerequisites
- `docker` for installation
- `poetry` (https://python-poetry.org/) can be useful to manage dependencies (but not mandatory) 


### Run the project

Create the `.env` file in the root folder then run:
```
docker compose up
```

The project should be available at `http://localhost:8000/docs`.

You can find some other useful commands in the Makefile.


---

rm app/infrastructure/migrations/versions/*.py

find . -type d -name "__pycache__" -exec rm -r {} +

alembic -c alembic.ini upgrade head 

alembic revision --autogenerate -m ""

poetry run uvicorn app.main:app --reload