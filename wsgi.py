import os
from app import create_app

config_type = os.getenv('FLASK_CONFIG', 'Config')
app = create_app(config_type)

if __name__ == "__main__":
    app.run(debug=False)
