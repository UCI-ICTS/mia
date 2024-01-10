import os
from app import create_app

config_type = os.getenv('FLASK_CONFIG', 'Config')
app = create_app(config_type)

if __name__ == "__main__":
    if config_type in 'local':
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0', debug=False)
