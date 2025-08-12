from flask import Flask
import os

app = Flask(__name__)

# Import and register the document Blueprint
from api.document import document_bp
from api.RAG_pipeline import rag_pipeline_bp
from api.genai_hub import genai_bp

cf_port = os.getenv("PORT")

app.register_blueprint(document_bp)
app.register_blueprint(rag_pipeline_bp)
app.register_blueprint(genai_bp)


@app.route("/")
def home():
    return "home"

if __name__ == '__main__':
	if cf_port is None:
		app.run(host='0.0.0.0', port=5000, debug=True)
	else:
		app.run(host='0.0.0.0', port=int(cf_port), debug=True)



