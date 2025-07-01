<!-- README.md -->
Requirements:
 Python 3
 PIP
 Docker if you want to use it

### Option 1: run it in your terminal
# create and activate venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Running this will create a new file call employees.db, we simulate this as our database
python init_db.py

# Running the api, you should let this run in the back ground. you can then access this api by visiting http://127.0.0.1:8000/ or http://0.0.0.0:8000/
uvicorn main:app --reload 

### Option2: run in docker
docker build -t hr-search-service .
docker run -d --name hr-search -p 8000:8000 hr-search-service

# you can now see the api at http://localhost:8000

# to run uniittest:
pytest tests/test_main.py

# it is best to start from unnittest as it would be how others use this api


I started with a minimal FastAPI and container setup, then added a search endpoint backed by SQLite using prepared statements. The get_db dependancy opens the DB in the event-loop thread, and I enabled dynamic cloumns via a whitelist so callers only see fields they ask for. A naive in-memory rate limiter met the no-external-libs requirement, trading off scale. To prevent data leaks I enforced an X-Organization-ID header on every query. OpenAPI metadata (title, version, description) was added so /docs and /openapi.json are ready to share. init_db.py seeds the database at build time. This approach favors speed of delivery and simplicity over perfromance tweakability or distributed scale.