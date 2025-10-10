from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import tempfile
import os

from agents.dynamic_financial.orchestrator import dynamic_financial_orchestrator
from agents.sequential_financial.utils.file_parser import parse_file

dfr = APIRouter()

@dfr.post("/extract")
async def extract_financial_data(file: UploadFile = File(...)):
    """
    Extract financial data from PDF or Word document
    
    Accepts: .pdf, .docx files
    Returns: JSON with extracted financial data
    """
    
    # Validate file type
    if not file.filename.endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF and Word documents are supported"
        )
    
    try:
        # Saving uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Parse file to text
        text = parse_file(tmp_path)
        
        # Extract financial data
        result = await dynamic_financial_orchestrator.extract(text)
        
        # Cleanup 
        os.unlink(tmp_path)
        
        return {
            "success": True,
            "filename": file.filename,
            "data": result
        }
    
    except Exception as e:
        # Cleanup on error
        if 'tmp_path' in locals():
            os.unlink(tmp_path)
        
        raise HTTPException(status_code=500, detail=str(e))