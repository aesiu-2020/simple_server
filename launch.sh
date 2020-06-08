# ensure virtual env exists
source person_server/bin/activate
# install dependencies
pip3 install -r requirements.txt

# run migrations
alembic upgrade head
# run app
python3 app.py