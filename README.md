# MAAMS (PBL Plus)

[![Production](https://gitlab.cs.ui.ac.id/maams-ppl/maams-be/badges/main/pipeline.svg?key_text=production&key_width=75)](https://gitlab.cs.ui.ac.id/maams-ppl/maams-be/-/pipelines?ref=main)
[![Staging](https://gitlab.cs.ui.ac.id/maams-ppl/maams-be/badges/ci-cd/pipeline.svg?key_text=staging)](https://gitlab.cs.ui.ac.id/maams-ppl/maams-be/-/pipelines?ref=staging)
[![Code Coverage](https://sonarcloud.io/api/project_badges/measure?project=maams-ppl_maams-be&metric=coverage)](https://sonarcloud.io/summary/new_code?id=maams-ppl_maams-be)

**Kelompok-2 PPL C**

[[_TOC_]]

---

## Members

1. 2106752306 Adly Renadi Raksanagara
2. 2106638324 Naila Shafirni Hidayat
3. 2106750313 Raditya Aditama
4. 2106708904 Bagas Shalahuddin Wahid
5. 2106752294 Nicholas Sidharta
6. 2106650222 Rania Maharani Narendra
7. 2106705644 Rayhan Putra Randi

## About

- Metode untuk menelusuri sebab-musabab paling awal/dalam suatu masalah dan memberikan solusi yang mendasar. (Terutama keadaan bermasalah yang akan dipulihkan atau dinormalkan, bukan dilipatgandakan).
- Sejenis Root Cause Analysis
- Inspirasi konseptual menyusun MAAMS ini berasal dari analisis Aristoteles tentang kekhususan filsafat yakni “mencari sebab-sebab yang terdalam dari seluruh realitas” (Lorens Bagus, 1991).

## Links

- [API Staging](https://staging.maams-be-staging.com/)
- [API Prod](http://34.143.155.67/)

## Environment Setup

1. Create and activate virtual environment (Python 3.8, 3.9, 3.10, 3.11)

    ```pwsh
    python -m venv .venv
    .venv\Scripts\activate.bat
    ```

2. Install required packages

    ```pwsh
    pip install -r requirements.txt  ```

4. Create new database in local PostgreSQL server either through pgAdmin4 or CLI

5. Create `.env` and `.env.dev` file to specify active development environment variables.

    `.env`:

    ```.env
    # ACTIVE ENVIRONMENT
    ENVIRONMENT=LOCAL
    ```

    `.env.dev`:

    ```.env.dev
    # Settings
    ALLOWED_HOSTS="localhost,127.0.0.1"
    SECRET_KEY=
    DEBUG=True
    HOST_FE="http://localhost:3000"

    # Database credentials
    DB_HOST=<your local DB Host>
    DB_PORT=<your local DB port>
    DB_USER=<your local DB username>
    DB_PASSWORD=<your local DB password>
    DB_NAME=<your local DB name>

    GROQ_API_KEY=<your CLAUDE API token>
    SENTRY_DSN=<your sentry dsn>
    ```

5. Initialize database tables

    ```pwsh
    python manage.py makemigrations
    python manage.py migrate
    ```

6. Run local server

    ```pwsh
    python manage.py runserver
    ```

## Testing

1. Run `coverage` package testing library

    ```pwsh
    coverage run manage.py test
    ```

2. See coverage report

    ```pwsh
    coverage report
    ```

3. Export testing results to HTML/XML

    ```pwsh
    coverage html
    # or
    coverage xml
    ```

## API Documentation (OAS 3.0)

### Postman

1. Download OpenAPI YAML schema by accessing the following endpoint:

    ```url
    localhost:8000/api/v1/schema/
    ```

2. Import downloaded YAML schema into Postman workspace.

3. For endpoints that require authorization, make sure to get access token first by logging in and input token to Bearer Token auth type.

### Swagger

1. Directly access the following endpoint:

   ```url
   localhost:8000/api/v1/schema/swagger-ui/
   ```

2. For endpoints that require authorization, log in first then input access token into the authorization setting at the top right corner of the page.
