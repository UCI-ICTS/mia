from app import create_app, db
from app.models.members import *
from app.models.chat import *
from app.models.user import *
from app.utils.utils import *
from app.utils.utils import _replace_db_script_with_json

app = create_app()
app.app_context().push()

print("IPython setup complete. Your Flask app and DB are now accessible.")
