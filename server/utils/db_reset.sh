#!/bin/bash

# Automatically confirm the flush operation
echo "yes" | python manage.py flush

# Load data from fixtures
# python manage.py loaddata tests/fixtures/initial.json
# python manage.py loaddata tests/fixtures/test_fixture.json
python manage.py loaddata config/fixtures/initial.json
# python manage.py loaddata config/fixtures/test.json
# python manage.py loaddata config/fixtures/dump.json
# python manage.py loaddata config/fixtures/U09_dump.json