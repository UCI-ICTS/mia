#!/bin/bash

# Automatically confirm the flush operation
echo "yes" | python manage.py flush

# Load data from fixtures
# python manage.py loaddata startTest.json
# python manage.py loaddata badTest.json
# python manage.py loaddata goodTest.json
# python manage.py loaddata config/fixtures/initial.json
# python manage.py loaddata config/fixtures/start_consent.json
# python manage.py loaddata test/fixtures/family.json
python manage.py loaddata tests/fixtures/test_data.json