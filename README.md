<!-- README.md -->
Requirements:
 Python 3
 PIP
 Docker if you want to use it

# create and activate venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Running this will create a new file call employees.db, we simulate this as our database
python init_db.py

# Running the api, you should let this run in the back ground. you can then access this api by visiting http://127.0.0.1:8000/ or http://0.0.0.0:8000/
uvicorn main:app --reload 

# to run uniittest:
pytest tests/test_main.py