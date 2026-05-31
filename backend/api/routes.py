from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid
from datetime import datetime
import os

from databases.models import get_db, Dataset, ChatMessage, QueryResult
from databases.dataset_manager import DatasetManager, UPLOAD_DIRECTORY
from databases.config import DatabaseConfig
from agents.sql_agent import get_sql_agent_for_dataset
from agents.export_handler import ExportHandler
from agents.query_cache import query_cache
from api.schemas import (
    DatasetResponse,
    QueryResultResponse,
    ChatHistoryResponse,
    MessageResponse,
    QueryRequest,
)

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload CSV file"""
    try:
        # Save file
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = UPLOAD_DIRECTORY / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process with dataset manager
        result = DatasetManager.upload_csv(str(file_path), db)
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/query")
async def query_dataset(request: QueryRequest, db: Session = Depends(get_db)):
    """Execute natural language query"""
    try:
        agent = get_sql_agent_for_dataset(request.datasetId, db)
        
        if not agent:
            return {
                "success": False,
                "error": "Dataset not found"
            }
        
        result = agent.query(request.question, request.datasetId, db)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/datasets")
async def list_datasets(db: Session = Depends(get_db)):
    """List all datasets"""
    result = DatasetManager.list_datasets(db)
    return result


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Get dataset information"""
    result = DatasetManager.get_dataset(dataset_id, db)
    return result


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Delete dataset"""
    result = DatasetManager.delete_dataset(dataset_id, db)
    return result


@router.get("/chat-history/{dataset_id}")
async def get_chat_history(dataset_id: str, db: Session = Depends(get_db)):
    """Get chat history for dataset"""
    try:
        messages = db.query(ChatMessage).filter(ChatMessage.dataset_id == dataset_id).all()
        
        if not messages:
            return {
                "success": True,
                "data": {
                    "messages": [],
                    "datasetId": dataset_id,
                    "createdAt": datetime.utcnow().isoformat(),
                    "updatedAt": datetime.utcnow().isoformat(),
                }
            }
        
        return {
            "success": True,
            "data": {
                "messages": [
                    {
                        "id": m.id,
                        "content": m.content,
                        "sender": m.sender,
                        "timestamp": m.timestamp.isoformat(),
                    }
                    for m in messages
                ],
                "datasetId": dataset_id,
                "createdAt": messages[0].timestamp.isoformat() if messages else datetime.utcnow().isoformat(),
                "updatedAt": messages[-1].timestamp.isoformat() if messages else datetime.utcnow().isoformat(),
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/export/results/{query_id}")
async def export_results(query_id: str, format: str = Query("csv", pattern="^(csv|json|pdf)$"), db: Session = Depends(get_db)):
    """Export query results in specified format"""
    try:
        # Get query result
        query_result = db.query(QueryResult).filter(QueryResult.id == query_id).first()
        if not query_result:
            raise HTTPException(status_code=404, detail="Query result not found")
        
        rows = query_result.rows_data
        title = f"Results for: {query_result.query}"
        
        if format == "csv":
            content = ExportHandler.export_to_csv(rows)
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            media_type = "text/csv"
        elif format == "json":
            content = ExportHandler.export_to_json(rows)
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            media_type = "application/json"
        elif format == "pdf":
            content = ExportHandler.export_to_pdf(rows, title=title)
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            media_type = "application/pdf"
        
        return FileResponse(
            content=content,
            filename=filename,
            media_type=media_type
        )
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/export/results")
async def export_results_inline(request: QueryRequest, format: str = Query("csv", pattern="^(csv|json|pdf)$"), db: Session = Depends(get_db)):
    """Export last query results"""
    try:
        # Get latest result for dataset
        query_result = db.query(QueryResult).filter(
            QueryResult.dataset_id == request.datasetId
        ).order_by(QueryResult.created_at.desc()).first()
        
        if not query_result:
            raise HTTPException(status_code=404, detail="No query results found")
        
        rows = query_result.rows_data
        
        if format == "csv":
            content = ExportHandler.export_to_csv(rows)
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            media_type = "text/csv"
        elif format == "json":
            content = ExportHandler.export_to_json(rows)
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            media_type = "application/json"
        elif format == "pdf":
            title = f"Results for: {query_result.query}"
            content = ExportHandler.export_to_pdf(rows, title=title)
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            media_type = "application/pdf"
        
        return FileResponse(
            content=content,
            filename=filename,
            media_type=media_type
        )
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/database/info")
async def get_database_info():
    """Get current database configuration info"""
    try:
        current_db = os.getenv("DATABASE_URL", DatabaseConfig.DEFAULT_DATABASE_URL)
        db_info = DatabaseConfig.get_database_info(current_db)
        
        return {
            "success": True,
            "data": {
                "current_database": db_info,
                "supported_databases": [
                    {
                        "driver": "sqlite",
                        "name": "SQLite",
                        "description": "Default local database (no setup required)",
                        "example": "sqlite:///./datachat.db"
                    },
                    {
                        "driver": "postgresql",
                        "name": "PostgreSQL",
                        "description": "Enterprise-grade relational database",
                        "example": "postgresql://user:password@localhost:5432/datachat"
                    },
                    {
                        "driver": "mysql",
                        "name": "MySQL / MariaDB",
                        "description": "Popular open-source database",
                        "example": "mysql+pymysql://user:password@localhost:3306/datachat"
                    }
                ]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/database/test-connection")
async def test_database_connection(connection_string: str = Query(...)):
    """Test if a database connection string is valid"""
    try:
        if not DatabaseConfig.validate_connection_string(connection_string):
            return {
                "success": False,
                "error": "Invalid connection string format",
                "details": "Connection string must start with: sqlite://, postgresql://, mysql+pymysql://, or mysql+mysqlconnector://"
            }
        
        # Try to create engine and connect
        test_engine = DatabaseConfig.create_engine_for_db(connection_string)
        with test_engine.connect() as conn:
            conn.execute("SELECT 1")
        
        db_info = DatabaseConfig.get_database_info(connection_string)
        
        return {
            "success": True,
            "message": "Connection successful",
            "data": db_info
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Connection failed: {str(e)}",
            "details": "Check your connection string and ensure the database is running"
        }


@router.get("/query-history/{dataset_id}")
async def get_query_history(
    dataset_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get query history for a dataset with pagination"""
    try:
        # Get total count
        total = db.query(QueryResult).filter(
            QueryResult.dataset_id == dataset_id
        ).count()
        
        # Get paginated results, most recent first
        queries = db.query(QueryResult).filter(
            QueryResult.dataset_id == dataset_id
        ).order_by(
            QueryResult.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        return {
            "success": True,
            "data": {
                "queries": [
                    {
                        "id": q.id,
                        "query": q.query,
                        "sql_query": q.sql_query,
                        "execution_time": q.execution_time,
                        "row_count": len(q.rows_data) if q.rows_data else 0,
                        "created_at": q.created_at.isoformat()
                    }
                    for q in queries
                ],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/query/{query_id}/replay")
async def replay_query(query_id: str, db: Session = Depends(get_db)):
    """Get a specific query to replay"""
    try:
        query_result = db.query(QueryResult).filter(
            QueryResult.id == query_id
        ).first()
        
        if not query_result:
            return {
                "success": False,
                "error": "Query not found"
            }
        
        return {
            "success": True,
            "data": {
                "id": query_result.id,
                "query": query_result.query,
                "sql_query": query_result.sql_query,
                "rows": query_result.rows_data,
                "execution_time": query_result.execution_time,
                "created_at": query_result.created_at.isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/query/{query_id}")
async def delete_query(query_id: str, db: Session = Depends(get_db)):
    """Delete a specific query from history"""
    try:
        query_result = db.query(QueryResult).filter(
            QueryResult.id == query_id
        ).first()
        
        if not query_result:
            return {
                "success": False,
                "error": "Query not found"
            }
        
        db.delete(query_result)
        db.commit()
        
        return {
            "success": True,
            "message": "Query deleted"
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


# Cache Management Endpoints

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = query_cache.get_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/cache/dataset/{dataset_id}")
async def clear_dataset_cache(dataset_id: str):
    """Clear cache for a specific dataset"""
    try:
        cleared_count = query_cache.clear_dataset(dataset_id)
        return {
            "success": True,
            "message": f"Cleared {cleared_count} cached queries",
            "clearedCount": cleared_count
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/cache/all")
async def clear_all_cache():
    """Clear entire cache"""
    try:
        cleared_count = query_cache.clear_all()
        return {
            "success": True,
            "message": f"Cleared {cleared_count} cached queries",
            "clearedCount": cleared_count
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/cache/dataset/{dataset_id}/size")
async def get_dataset_cache_size(dataset_id: str):
    """Get number of cached queries for a dataset"""
    try:
        size = query_cache.get_dataset_cache_size(dataset_id)
        return {
            "success": True,
            "data": {
                "datasetId": dataset_id,
                "cachedQueries": size
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
