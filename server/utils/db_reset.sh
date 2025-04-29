#!/bin/bash

# Automatically confirm the flush operation
echo "yes" | python manage.py flush

# Load data from fixtures
python manage.py loaddata config/fixtures/initial.json
# python manage.py loaddata config/fixtures/start_consent.json
# python manage.py loaddata test/fixtures/family.json
# python manage.py loaddata test/fixtures/new_consent.json