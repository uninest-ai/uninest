# spring slides
https://docs.google.com/presentation/d/1R7pGIgPN4ENUksizxR_w3W0k_0s4b9ZjSzzBdaYyFX0/edit?usp=sharing
# s25_team_1
Repository for s25_team_1


# Reference:
    - Due to we are using FastAPI to be achieve a real-time websocket and AI application, we need some external 3rd party extension to complete the functions, including Pydantic, sqlalchemy etc. Here are some reference we are looking at.
        - https://github.com/fastapi/fastapi/issues/214 
        - https://github.com/tiangolo/pydantic-sqlalchemy 
        - https://stackoverflow.com/questions/71570607/sqlalchemy-models-vs-pydantic-models 
        - https://docs.pydantic.dev/latest/examples/orms/ 
        - https://realpython.com/pytest-python-testing/
    SQL:
        - port: 5432
        - pw: 123456
        - Installation Directory: D:\Program Files\PostgreSQL\17

## Project Structure
```markdown
/
├── frontend/          # Next.js frontend application
├── backend/          # FastAPI backend application
├── docs/            # Project documentation