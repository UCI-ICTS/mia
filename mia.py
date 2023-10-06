import app.main
from app import app, db
#from app.models import User, UserChatUrl, ChatScriptVersion, Chat

if __name__ == "__main__":
    app.run(debug=True)
