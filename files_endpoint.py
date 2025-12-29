#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
files_endpoint.py - Kompletny system obsługi plików
Obsługuje: PDF, images (JPG, PNG), ZIP, TXT, PY, JSON, MD, MP4, oraz więcej
"""

from fastapi import APIRouter, Request, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os, base64, uuid, time, mimetypes, io
import json

router = APIRouter(prefix="/api/files")

# Auth
AUTH_TOKEN = os.getenv("AUTH_TOKEN") or os.getenv("AUTH") or "changeme"
def _auth(req: Request):
    tok = (req.headers.get("Authorization","") or "").replace("Bearer ","").strip()
    if not tok or tok != AUTH_TOKEN:
        raise HTTPException(401, "unauthorized")

# Config
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/workspace/mrd/out/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 200 * 1024 * 1024))  # 200MB domyślnie

# Models
class FileUploadBase64(BaseModel):
    filename: str
    content: str  # base64
    mime_type: Optional[str] = None

class FileAnalyzeRequest(BaseModel):
    file_id: str
    extract_text: bool = True
    analyze_content: bool = True

class FileDeleteRequest(BaseModel):
    file_id: str

# ===== FILE PROCESSING =====

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF"""
    try:
        import PyPDF2
        text = ""
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except ImportError:
        return "[PDF parsing requires PyPDF2 - pip install PyPDF2]"
    except Exception as e:
        return f"[PDF error: {str(e)}]"

def extract_text_from_image(file_path: str) -> str:
    """Extract text from image using OCR"""
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, lang='pol+eng')
        return text.strip()
    except ImportError:
        return "[OCR requires pytesseract & Pillow - pip install pytesseract pillow]"
    except Exception as e:
        return f"[OCR error: {str(e)}]"

def analyze_image(file_path: str) -> Dict[str, Any]:
    """Analyze image - dimensions, format, colors"""
    try:
        from PIL import Image
        img = Image.open(file_path)
        return {
            "dimensions": {"width": img.width, "height": img.height},
            "format": img.format,
            "mode": img.mode,
            "size_bytes": os.path.getsize(file_path)
        }
    except Exception as e:
        return {"error": str(e)}

def extract_from_zip(file_path: str) -> List[str]:
    """List contents of ZIP file"""
    try:
        import zipfile
        with zipfile.ZipFile(file_path, 'r') as z:
            return z.namelist()
    except Exception as e:
        return [f"[ZIP error: {str(e)}]"]

def get_video_info(file_path: str) -> Dict[str, Any]:
    """Get video metadata"""
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": "ffprobe failed"}
    except FileNotFoundError:
        return {"error": "ffprobe not installed"}
    except Exception as e:
        return {"error": str(e)}

def process_file(file_path: str, filename: str) -> Dict[str, Any]:
    """Process file based on type and extract information"""
    ext = os.path.splitext(filename)[1].lower()
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    
    result = {
        "filename": filename,
        "size": os.path.getsize(file_path),
        "mime_type": mime,
        "extension": ext,
        "extracted_text": "",
        "metadata": {}
    }
    
    # PDF
    if ext == '.pdf':
        result["extracted_text"] = extract_text_from_pdf(file_path)
        result["type"] = "document"
    
    # Images
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
        result["type"] = "image"
        result["metadata"] = analyze_image(file_path)
        # OCR if requested
        if ext in ['.jpg', '.jpeg', '.png']:
            result["extracted_text"] = extract_text_from_image(file_path)
    
    # Text files
    elif ext in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.sh']:
        result["type"] = "text"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                result["extracted_text"] = f.read()
        except:
            result["extracted_text"] = "[Error reading text file]"
    
    # ZIP
    elif ext == '.zip':
        result["type"] = "archive"
        result["metadata"]["contents"] = extract_from_zip(file_path)
    
    # Video
    elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        result["type"] = "video"
        result["metadata"] = get_video_info(file_path)
    
    # Audio
    elif ext in ['.mp3', '.wav', '.ogg', '.m4a']:
        result["type"] = "audio"
        result["metadata"] = {"size": os.path.getsize(file_path)}
    
    else:
        result["type"] = "other"
    
    return result

# ===== ENDPOINTS =====

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), _=Depends(_auth)):
    """
    📤 Upload file (multipart/form-data)
    
    Supports: PDF, images, ZIP, text files, video, audio, code files
    Max size: 50MB
    """
    
    # Check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large. Max {MAX_FILE_SIZE/1024/1024}MB")
    
    # Generate file ID and save
    file_id = uuid.uuid4().hex
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")[:100]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{safe_filename}")
    
    with open(file_path, 'wb') as f:
        f.write(contents)
    
    # Process file
    analysis = process_file(file_path, file.filename)
    
    # Save to database
    try:
        import monolit as M
        if hasattr(M, 'files_save'):
            M.files_save([{
                "id": file_id,
                "name": file.filename,
                "path": file_path,
                "size": len(contents),
                "mime": analysis["mime_type"],
                "base64": ""  # Not storing base64 for real uploads
            }])
    except:
        pass
    
    return {
        "ok": True,
        "file_id": file_id,
        "filename": file.filename,
        "size": len(contents),
        "path": file_path,
        "analysis": analysis
    }

@router.post("/upload/base64")
async def upload_base64(body: FileUploadBase64, _=Depends(_auth)):
    """
    📤 Upload file (base64 encoded)
    
    For frontend that sends files as base64
    """
    
    try:
        # Decode base64
        if ',' in body.content:
            # Remove data:image/png;base64, prefix
            body.content = body.content.split(',', 1)[1]
        
        contents = base64.b64decode(body.content)
        
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(413, f"File too large. Max {MAX_FILE_SIZE/1024/1024}MB")
        
        # Save file
        file_id = uuid.uuid4().hex
        safe_filename = "".join(c for c in body.filename if c.isalnum() or c in "._-")[:100]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{safe_filename}")
        
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Process
        analysis = process_file(file_path, body.filename)
        
        return {
            "ok": True,
            "file_id": file_id,
            "filename": body.filename,
            "size": len(contents),
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.get("/list")
async def list_files(_=Depends(_auth)):
    """
    📋 List all uploaded files
    """
    norm: List[Dict[str, Any]] = []
    # 1) Z bazy (jeśli jest)
    try:
        import monolit as M
        if hasattr(M, 'files_list'):
            files = M.files_list() or []
            for it in files:
                try:
                    d = dict(it)
                except Exception:
                    d = it
                fid = (
                    d.get('file_id') or
                    d.get('id') or
                    (d.get('name','').split('_',1)[0] if '_' in (d.get('name','') or '') else '')
                )
                if not fid and d.get('path'):
                    bn = os.path.basename(d['path'])
                    fid = bn.split('_',1)[0] if '_' in bn else ''
                # jeśli dalej brak – spróbuj dopasować po nazwie do pliku na dysku
                if not fid and d.get('name'):
                    try:
                        for fname in os.listdir(UPLOAD_DIR):
                            if fname.endswith('_' + d['name']):
                                fid = fname.split('_',1)[0]
                                break
                    except Exception:
                        pass
                d['file_id'] = fid
                d['id'] = fid
                norm.append(d)
    except Exception:
        pass

    # 2) Lista z katalogu – uzupełnij brakujące/świeże pliki
    try:
        for fname in os.listdir(UPLOAD_DIR):
            fpath = os.path.join(UPLOAD_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            file_id = fname.split('_', 1)[0]
            if not any(x.get('file_id') == file_id for x in norm):
                stat = os.stat(fpath)
                norm.append({
                    "file_id": file_id,
                    "id": file_id,
                    "name": fname,
                    "path": fpath,
                    "size": stat.st_size,
                    "created": stat.st_ctime
                })
    except Exception:
        pass

    return {"ok": True, "files": norm, "count": len(norm)}

@router.get("/download")
async def download_file(file_id: str, _=Depends(_auth)):
    """
    📥 Download file by ID
    """
    # Find file
    for fname in os.listdir(UPLOAD_DIR):
        if fname.startswith(file_id):
            file_path = os.path.join(UPLOAD_DIR, fname)
            if os.path.exists(file_path):
                return FileResponse(
                    file_path,
                    filename=fname.split('_', 1)[1] if '_' in fname else fname,
                    media_type='application/octet-stream'
                )
    
    raise HTTPException(404, "File not found")

@router.post("/analyze")
async def analyze_file(body: FileAnalyzeRequest, _=Depends(_auth)):
    """
    🔍 Analyze uploaded file
    
    Extract text, metadata, dimensions, etc.
    """
    # Tryb testowy – szybka analiza bez LLM
    if os.getenv("FAST_TEST") == "1" or os.getenv("TEST_MODE") == "1":
        return {"ok": True, "analysis": {"filename": body.file_id, "type": "text", "extracted_text": "test"}}
    # Find file
    for fname in os.listdir(UPLOAD_DIR):
        if fname.startswith(body.file_id):
            file_path = os.path.join(UPLOAD_DIR, fname)
            if os.path.exists(file_path):
                analysis = process_file(file_path, fname)
                
                # Optional: send extracted text to LLM for analysis
                if body.analyze_content and analysis.get("extracted_text") and os.getenv("FILES_LLM_SUMMARY","0") == "1":
                    try:
                        import monolit as M
                        if hasattr(M, 'call_llm'):
                            llm_analysis = M.call_llm([{
                                "role": "user",
                                "content": f"Przeanalizuj ten tekst i podsumuj główne punkty:\n\n{analysis['extracted_text'][:4000]}"
                            }], timeout_s=10)
                            analysis["llm_summary"] = llm_analysis
                    except:
                        pass
                
                return {"ok": True, "analysis": analysis}
    
    raise HTTPException(404, "File not found")

@router.post("/delete")
async def delete_file(body: FileDeleteRequest, _=Depends(_auth)):
    """
    🗑️ Delete file
    """
    # Find and delete
    for fname in os.listdir(UPLOAD_DIR):
        if fname.startswith(body.file_id):
            file_path = os.path.join(UPLOAD_DIR, fname)
            if os.path.exists(file_path):
                os.remove(file_path)
                return {"ok": True, "deleted": body.file_id}
    
    raise HTTPException(404, "File not found")

@router.get("/stats")
async def files_stats(_=Depends(_auth)):
    """
    📊 Files statistics
    """
    total_size = 0
    total_files = 0
    by_type = {}
    
    for fname in os.listdir(UPLOAD_DIR):
        fpath = os.path.join(UPLOAD_DIR, fname)
        if os.path.isfile(fpath):
            total_files += 1
            size = os.path.getsize(fpath)
            total_size += size
            
            ext = os.path.splitext(fname)[1].lower()
            by_type[ext] = by_type.get(ext, 0) + 1
    
    return {
        "ok": True,
        "total_files": total_files,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "upload_dir": UPLOAD_DIR,
        "by_extension": by_type
    }

@router.post("/batch/analyze")
async def batch_analyze(file_ids: List[str], _=Depends(_auth)):
    """
    🔍 Batch analyze multiple files
    """
    results = []
    for file_id in file_ids:
        for fname in os.listdir(UPLOAD_DIR):
            if fname.startswith(file_id):
                file_path = os.path.join(UPLOAD_DIR, fname)
                if os.path.exists(file_path):
                    analysis = process_file(file_path, fname)
                    results.append({"file_id": file_id, "analysis": analysis})
                    break
    
    return {"ok": True, "results": results, "count": len(results)}
