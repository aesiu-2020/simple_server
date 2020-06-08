# start the postgres container (can give it a real password)
docker run -d -p 5433:5433 -e POSTGRES_PASSWORD=password postgres
# set connection string, again password can change
# this will be used by the app, for conveniance it's the root user and base db, probably shouldn't for a real service
export DB_CONNECTION=postgresql://postgres:password@localhost:5433/postgres

# start virtual env
python3 -m venv person_server