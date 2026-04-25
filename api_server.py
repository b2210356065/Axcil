"""
ExcelAI FastAPI Backend Server
Flutter Windows Desktop için REST API

Tüm backend iş mantığını korur, sadece HTTP layer ekler.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import base64
import json
import os
import tempfile
from datetime import datetime
from io import BytesIO

# Core imports
from core.config import load_config, save_config
from core.models import APIConfig, TaskType
from core.database import (
    init_db, get_active_business, set_active_business, create_business,
    get_functionalities, get_functionality_by_id,
    save_functionality, update_functionality, delete_functionality,
    get_all_data_types, create_data_type, delete_data_type,
    get_history,
)
from core.enrichment import enrich_functionality, confirm_enrichment
from core.algorithm_generator import generate_algorithm

# AI imports
from ai.router import ModelRouter

# Excel Engine
from excel_engine.builder import ExcelBuilder

# ============================================================================
# FastAPI App Initialization
# ============================================================================

app = FastAPI(
    title="ExcelAI API",
    description="AI-Powered Excel Generation Backend for Flutter Desktop",
    version="1.0.0",
)

# CORS Middleware (Flutter desktop için gerekli)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik origin eklenebilir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global router instance (config yüklendikten sonra başlatılır)
_router_instance: Optional[ModelRouter] = None

def get_router() -> Optional[ModelRouter]:
    """Global router instance'ı döndür."""
    return _router_instance

def init_router(config: APIConfig) -> None:
    """Router'ı yeniden başlat."""
    global _router_instance
    if config.available_providers():
        _router_instance = ModelRouter(config)
    else:
        _router_instance = None

# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================

class ConfigRequest(BaseModel):
    """API Config kaydetme request'i."""
    gemini_key: Optional[str] = None
    claude_key: Optional[str] = None
    openai_key: Optional[str] = None
    gemini_model: str = "models/gemini-3-flash-preview"
    claude_model: str = "claude-sonnet-4-20250514"
    openai_model: str = "gpt-4o-mini"
    confidence_high: float = 0.90
    confidence_low: float = 0.70

class ConfigResponse(BaseModel):
    """API Config response."""
    gemini_key: Optional[str]
    claude_key: Optional[str]
    openai_key: Optional[str]
    gemini_model: str
    claude_model: str
    openai_model: str
    confidence_high: float
    confidence_low: float
    available_providers: List[str]

class BusinessProfileRequest(BaseModel):
    """Business Profile request."""
    business_name: str
    business_description: str
    sector: Optional[str] = None
    is_active: bool = True

class BusinessProfileResponse(BaseModel):
    """Business Profile response."""
    id: int
    business_name: str
    business_description: str
    sector: Optional[str]
    is_active: bool
    created_at: str

class FunctionalityRequest(BaseModel):
    """Functionality oluşturma/güncelleme request'i."""
    business_id: int
    name: str
    description: str
    input_fields: List[Dict[str, Any]] = Field(default_factory=lambda: [{"name": "data", "type": "any"}])
    excel_template: Dict[str, Any] = Field(default_factory=lambda: {"type": "general"})
    system_prompt: Optional[str] = None
    data_type_ids: List[int] = Field(default_factory=list)

class FunctionalityResponse(BaseModel):
    """Functionality response."""
    id: int
    business_id: int
    name: str
    description: str
    enriched_definition: Optional[Dict[str, Any]]
    algorithm_path: Optional[str]
    algorithm_version: int
    data_type_ids: List[int]

class EnrichmentResponse(BaseModel):
    """Enrichment response."""
    success: bool
    enriched: Optional[Dict[str, Any]] = None
    attempt_id: Optional[int] = None
    error: Optional[str] = None

class AlgorithmResponse(BaseModel):
    """Algorithm generation response."""
    success: bool
    code: Optional[str] = None
    version: Optional[int] = None
    test_results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DataTypeRequest(BaseModel):
    """Data type oluşturma request'i."""
    name: str
    description: str
    icon: str = "📊"

class DataTypeResponse(BaseModel):
    """Data type response."""
    id: int
    name: str
    description: str
    icon: str
    is_default: bool

class ToolProcessResponse(BaseModel):
    """Tool processing response."""
    success: bool
    excel_base64: Optional[str] = None
    preview_data: Optional[Dict[str, Any]] = None
    cost_usd: float = 0.0
    latency_ms: int = 0
    message: str = ""
    errors: List[str] = Field(default_factory=list)

class HistoryResponse(BaseModel):
    """History entry response."""
    id: int
    functionality_name: str
    output_file: str
    file_size: int
    created_at: str

class DebugLogResponse(BaseModel):
    """Debug log response."""
    logs: List[Dict[str, Any]]
    total_count: int

# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında veritabanı ve router'ı başlat."""
    init_db()

    # Config yükle ve router başlat
    try:
        config = load_config()
        init_router(config)
    except Exception:
        # Config yoksa varsayılan oluştur
        pass

# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """API server sağlık kontrolü."""
    router = get_router()
    return {
        "status": "healthy",
        "router_initialized": router is not None,
        "database": "connected",
        "timestamp": datetime.now().isoformat(),
    }

# ============================================================================
# Config Endpoints
# ============================================================================

@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """API config'i yükle."""
    try:
        config = load_config()
        return ConfigResponse(
            gemini_key=config.gemini_key,
            claude_key=config.claude_key,
            openai_key=config.openai_key,
            gemini_model=config.gemini_model,
            claude_model=config.claude_model,
            openai_model=config.openai_model,
            confidence_high=config.confidence_high,
            confidence_low=config.confidence_low,
            available_providers=[p.value for p in config.available_providers()],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config yükleme hatası: {str(e)}")

@app.post("/api/config")
async def save_config_endpoint(config_req: ConfigRequest):
    """API config'i kaydet."""
    try:
        config = APIConfig(
            gemini_key=config_req.gemini_key,
            claude_key=config_req.claude_key,
            openai_key=config_req.openai_key,
            gemini_model=config_req.gemini_model,
            claude_model=config_req.claude_model,
            openai_model=config_req.openai_model,
            confidence_high=config_req.confidence_high,
            confidence_low=config_req.confidence_low,
        )
        save_config(config)

        # Router'ı yeniden başlat
        init_router(config)

        return {"success": True, "message": "Config kaydedildi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config kaydetme hatası: {str(e)}")

# ============================================================================
# Business Profile Endpoints
# ============================================================================

@app.get("/api/business", response_model=Optional[BusinessProfileResponse])
async def get_business():
    """Aktif business profile'ı getir."""
    try:
        business = get_active_business()
        if not business:
            return None

        return BusinessProfileResponse(
            id=business["id"],
            business_name=business["business_name"],
            business_description=business["business_description"],
            sector=business.get("sector"),
            is_active=bool(business["is_active"]),
            created_at=business["created_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Business getirme hatası: {str(e)}")

@app.post("/api/business")
async def create_or_update_business(business_req: BusinessProfileRequest):
    """Business profile oluştur veya güncelle."""
    try:
        business_id = create_business(
            name=business_req.business_name,
            description=business_req.business_description,
            sector=business_req.sector or "",
        )

        if business_req.is_active:
            set_active_business(business_id)

        return {"success": True, "business_id": business_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Business kaydetme hatası: {str(e)}")

# ============================================================================
# Functionalities Endpoints
# ============================================================================

@app.get("/api/functionalities", response_model=List[FunctionalityResponse])
async def list_functionalities(business_id: Optional[int] = None):
    """Tüm functionalities'i listele."""
    try:
        if business_id is None:
            active_business = get_active_business()
            if not active_business:
                return []
            business_id = active_business["id"]

        funcs = get_functionalities(business_id)

        results = []
        for func in funcs:
            # data_type_ids parse
            data_type_ids = []
            if func.get("data_type_ids"):
                try:
                    data_type_ids = json.loads(func["data_type_ids"])
                except:
                    pass

            # enriched_definition parse
            enriched = None
            if func.get("enriched_definition"):
                try:
                    enriched = json.loads(func["enriched_definition"])
                except:
                    pass

            results.append(FunctionalityResponse(
                id=func["id"],
                business_id=func["business_id"],
                name=func["name"],
                description=func["description"],
                enriched_definition=enriched,
                algorithm_path=func.get("algorithm_path"),
                algorithm_version=func.get("algorithm_version", 0),
                data_type_ids=data_type_ids,
            ))

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Functionalities listeleme hatası: {str(e)}")

@app.get("/api/functionalities/{func_id}", response_model=FunctionalityResponse)
async def get_functionality(func_id: int):
    """Tek bir functionality getir."""
    try:
        func = get_functionality_by_id(func_id)
        if not func:
            raise HTTPException(status_code=404, detail="Functionality bulunamadı")

        # Parse JSON fields
        data_type_ids = []
        if func.get("data_type_ids"):
            try:
                data_type_ids = json.loads(func["data_type_ids"])
            except:
                pass

        enriched = None
        if func.get("enriched_definition"):
            try:
                enriched = json.loads(func["enriched_definition"])
            except:
                pass

        return FunctionalityResponse(
            id=func["id"],
            business_id=func["business_id"],
            name=func["name"],
            description=func["description"],
            enriched_definition=enriched,
            algorithm_path=func.get("algorithm_path"),
            algorithm_version=func.get("algorithm_version", 0),
            data_type_ids=data_type_ids,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Functionality getirme hatası: {str(e)}")

@app.post("/api/functionalities")
async def create_functionality(func_req: FunctionalityRequest):
    """Yeni functionality oluştur."""
    try:
        system_prompt = func_req.system_prompt or f"İş: {func_req.name}\n{func_req.description}"

        func_id = save_functionality(
            business_id=func_req.business_id,
            name=func_req.name,
            description=func_req.description,
            input_fields=func_req.input_fields,
            excel_template=func_req.excel_template,
            system_prompt=system_prompt,
            data_type_ids=func_req.data_type_ids,
        )

        return {"success": True, "functionality_id": func_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Functionality oluşturma hatası: {str(e)}")

@app.put("/api/functionalities/{func_id}")
async def update_functionality_endpoint(func_id: int, func_req: FunctionalityRequest):
    """Functionality güncelle."""
    try:
        system_prompt = func_req.system_prompt or f"İş: {func_req.name}\n{func_req.description}"

        update_functionality(
            func_id=func_id,
            name=func_req.name,
            description=func_req.description,
            input_fields=func_req.input_fields,
            excel_template=func_req.excel_template,
            system_prompt=system_prompt,
            data_type_ids=func_req.data_type_ids,
        )

        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Functionality güncelleme hatası: {str(e)}")

@app.delete("/api/functionalities/{func_id}")
async def delete_functionality_endpoint(func_id: int):
    """Functionality sil."""
    try:
        delete_functionality(func_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Functionality silme hatası: {str(e)}")

# ============================================================================
# Enrichment & Algorithm Endpoints
# ============================================================================

@app.post("/api/functionalities/{func_id}/enrich", response_model=EnrichmentResponse)
async def enrich_functionality_endpoint(func_id: int, user_feedback: Optional[str] = None):
    """Functionality'i AI ile zenginleştir."""
    router = get_router()
    if not router:
        raise HTTPException(status_code=400, detail="Router başlatılmamış. Lütfen API anahtarlarını kaydedin.")

    try:
        result = enrich_functionality(func_id, router, user_feedback)

        if result["success"]:
            return EnrichmentResponse(
                success=True,
                enriched=result.get("enriched"),
                attempt_id=result.get("attempt_id"),
            )
        else:
            return EnrichmentResponse(
                success=False,
                error=result.get("error", "Bilinmeyen hata"),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrichment hatası: {str(e)}")

@app.post("/api/functionalities/{func_id}/enrich/confirm")
async def confirm_enrichment_endpoint(func_id: int, attempt_id: int):
    """Enrichment'ı onayla ve veritabanına kaydet."""
    try:
        success = confirm_enrichment(func_id, attempt_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrichment onaylama hatası: {str(e)}")

@app.post("/api/functionalities/{func_id}/generate_algo", response_model=AlgorithmResponse)
async def generate_algorithm_endpoint(func_id: int, user_feedback: Optional[str] = None):
    """Functionality için algoritma oluştur."""
    router = get_router()
    if not router:
        raise HTTPException(status_code=400, detail="Router başlatılmamış. Lütfen API anahtarlarını kaydedin.")

    try:
        result = generate_algorithm(func_id, router, user_feedback)

        if result["success"]:
            return AlgorithmResponse(
                success=True,
                code=result.get("code"),
                version=result.get("version"),
                test_results=result.get("test_results"),
            )
        else:
            return AlgorithmResponse(
                success=False,
                error=result.get("error", "Bilinmeyen hata"),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Algorithm generation hatası: {str(e)}")

# ============================================================================
# Data Types Endpoints
# ============================================================================

@app.get("/api/data_types", response_model=List[DataTypeResponse])
async def list_data_types():
    """Tüm data type'ları listele."""
    try:
        data_types = get_all_data_types()

        results = []
        for dt in data_types:
            results.append(DataTypeResponse(
                id=dt["id"],
                name=dt["name"],
                description=dt.get("description", ""),
                icon=dt.get("icon", "📊"),
                is_default=bool(dt.get("is_default", 0)),
            ))

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data types listeleme hatası: {str(e)}")

@app.post("/api/data_types")
async def create_data_type_endpoint(dt_req: DataTypeRequest):
    """Yeni data type oluştur."""
    try:
        dt_id = create_data_type(
            name=dt_req.name,
            description=dt_req.description,
            icon=dt_req.icon,
        )
        if dt_id is None:
            raise HTTPException(status_code=400, detail="Aynı isimde veri tipi zaten var")
        return {"success": True, "data_type_id": dt_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data type oluşturma hatası: {str(e)}")

@app.delete("/api/data_types/{dt_id}")
async def delete_data_type_endpoint(dt_id: int):
    """Data type sil (sadece custom olanlar)."""
    try:
        delete_data_type(dt_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data type silme hatası: {str(e)}")

# ============================================================================
# Tools Processing Endpoint (EN ÖNEMLİ)
# ============================================================================

@app.post("/api/tools/process", response_model=ToolProcessResponse)
async def process_tool(
    file: Optional[UploadFile] = File(None),
    text_input: Optional[str] = Form(None),
    func_id: Optional[int] = Form(None),
    mode: str = Form("create"),
):
    """
    Tool processing endpoint (multipart).

    Supports:
    - Image upload (jpg, png, pdf)
    - Text input
    - PDF upload
    - Voice upload
    - Excel upload

    Mode:
    - create: Yeni Excel oluştur
    - append: Mevcut Excel'e ekle
    - delete: Mevcut Excel'den sil
    - edit: Mevcut Excel'i düzenle
    """
    router = get_router()
    if not router:
        raise HTTPException(status_code=400, detail="Router başlatılmamış.")

    try:
        # Burada tools/ klasörünü kullanarak işleme yapılacak
        # Şimdilik basit bir mock response dönüyoruz
        # Gerçek implementasyon: ImageToExcelTool, TextToExcelTool vs. kullanacak

        # TODO: Implement full tool processing logic
        # Bu endpoint'i gerçek tools ile entegre edeceğiz

        return ToolProcessResponse(
            success=True,
            excel_base64="",  # Gerçek Excel base64
            preview_data={},
            message="Tool processing endpoint hazır, implementasyon devam ediyor",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool processing hatası: {str(e)}")

# ============================================================================
# History Endpoints
# ============================================================================

@app.get("/api/history", response_model=List[HistoryResponse])
async def list_history(limit: int = 50):
    """Generation history listele."""
    try:
        history = get_history(limit=limit)

        results = []
        for entry in history:
            file_size = 0
            if entry.get("output_file") and os.path.exists(entry["output_file"]):
                file_size = os.path.getsize(entry["output_file"])

            results.append(HistoryResponse(
                id=entry["id"],
                functionality_name=entry.get("func_name", "Bilinmiyor"),
                output_file=entry.get("output_file", ""),
                file_size=file_size,
                created_at=entry["created_at"],
            ))

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History listeleme hatası: {str(e)}")

@app.delete("/api/history/{history_id}")
async def delete_history(history_id: int):
    """History entry sil."""
    try:
        # History silme fonksiyonu şu an database.py'de yok, basit silme yapıyoruz
        from core.database import get_connection
        conn = get_connection()
        conn.execute("DELETE FROM generation_history WHERE id=?", (history_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History silme hatası: {str(e)}")

# ============================================================================
# Debug Logs Endpoint
# ============================================================================

@app.get("/api/debug/logs", response_model=DebugLogResponse)
async def get_debug_logs(limit: int = 200, source: str = "file"):
    """Debug loglarını getir."""
    try:
        logs = []

        if source == "file":
            # logs/ klasöründen son dosyayı oku
            log_dir = os.path.join(os.path.dirname(__file__), "logs")
            if os.path.exists(log_dir):
                log_files = sorted([f for f in os.listdir(log_dir) if f.startswith("ai_debug_")])
                if log_files:
                    latest_log = os.path.join(log_dir, log_files[-1])
                    with open(latest_log, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                logs.append(json.loads(line.strip()))
                            except:
                                pass

        # Limit uygula
        logs = logs[-limit:] if len(logs) > limit else logs

        return DebugLogResponse(
            logs=logs,
            total_count=len(logs),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug logs hatası: {str(e)}")

# ============================================================================
# Main (Development Server)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Development mode
    )
