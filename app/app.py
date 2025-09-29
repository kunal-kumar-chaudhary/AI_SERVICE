from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Creating FastAPI app instance
app = FastAPI(
    title="AI Service",
    description="AI-powered document processing and RAG pipeline",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# from api.routes.document import routes as document_router
from api.routes.RAG_pipeline import rag_pipeline_router
from api.routes.genai_hub import genai_router

# Including routers with their prefixes
# app.include_router(document_router, prefix="/api/documents", tags=["documents"])
app.include_router(rag_pipeline_router, prefix="/api/rag-pipeline", tags=["rag"])
app.include_router(genai_router, prefix="/api/genai", tags=["genai"])

# Root endpoint
@app.get("/")
async def home():
    return {"message": "home"}

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == '__main__':
    
    cf_port = os.getenv("PORT")
    port = int(cf_port) if cf_port else 5000
    
    uvicorn.run(
        "__main__:app",  
        host='0.0.0.0',
        port=port,
        reload=True,
        log_level="info"
    )