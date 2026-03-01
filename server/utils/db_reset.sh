#!/bin/bash

# Automatically confirm the flush operation
echo "yes" | python manage.py flush

# CLear Django cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Load data from fixtures
python manage.py loaddata config/fixtures/initial.json
# python manage.py loaddata tests/fixtures/test_data.json