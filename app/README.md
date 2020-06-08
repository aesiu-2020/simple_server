Basic service with a person api and some rudementary versioning

Mainly uses Flask, sqlalchemy, postgres, and alembic


start with `setup.sh`

# PREPEQ have docker downloaded and started
# https://hub.docker.com/editions/community/docker-ce-desktop-mac/
# also have python3, pip3, virtualenv

then `launch.sh` should start the app at location http://127.0.0.1:5000

sample person creation:
curl --location --request POST 'http://127.0.0.1:5000/rest/person' \
--header 'Content-Type: application/json' \
--data-raw '{
	"firstName" : "Homer",
	"lastName" : "Simpson",
	"dateOfBirth" : "1956-05-12",
	"email": "chunkylover53@aol.coms"
}'