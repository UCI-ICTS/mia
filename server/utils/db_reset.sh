#!/bin/bash

# Automatically confirm the flush operation
echo "yes" | python manage.py flush

# Load data from fixtures
# python manage.py loaddata config/fixtures/initial.json
# python manage.py loaddata config/fixtures/form.json
# python manage.py loaddata config/fixtures/test_final.json
# python manage.py loaddata config/fixtures/test.json
# python manage.py loaddata config/fixtures/family.json
# python manage.py loaddata config/fixtures/dump.json
# python manage.py loaddata config/fixtures/U09_dump.json

python manage.py loaddata test/fixtures/link.json
# python manage.py loaddata test/fixtures/first_branch.json
# python manage.py loaddata test/fixtures/consent.json
# python manage.py loaddata test/fixtures/new_consent.json