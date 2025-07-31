from flask import Flask

app = Flask(__name__)

# Import and register the document Blueprint
from api.document import document_bp
app.register_blueprint(document_bp)

@app.route("/")
def home():
    return "home"



if __name__=="__main__":
    app.run(debug=True)



