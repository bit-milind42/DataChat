import pandas as pd
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, inspect
from .models import Dataset
from agents.data_profiler import DataProfiler
import os

UPLOAD_DIRECTORY = Path(__file__).parent.parent / "uploads"
UPLOAD_DIRECTORY.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./datachat.db")


class DatasetManager:
    @staticmethod
    def upload_csv(file_path: str, db: Session) -> dict:
        """Upload and process CSV file with optimized chunked loading"""
        try:
            dataset_id = f"dataset_{uuid.uuid4().hex[:12]}"
            filename = Path(file_path).name
            table_name = f"{dataset_id}_datachat_sample_sales"
            
            # Store CSV file directory
            uploads_dir = UPLOAD_DIRECTORY / dataset_id
            uploads_dir.mkdir(exist_ok=True)
            csv_path = uploads_dir / filename
            
            # Read CSV metadata first (headers only)
            df_meta = pd.read_csv(file_path, nrows=0)
            columns = df_meta.columns.tolist()
            
            # Create engine for fast bulk insert
            engine = create_engine(
                DATABASE_URL,
                connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
            )
            
            # Load and insert data in chunks for better performance
            chunk_size = 5000
            total_rows = 0
            df_full = None
            
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                # Convert data types per chunk
                for col in chunk.columns:
                    try:
                        chunk[col] = pd.to_numeric(chunk[col])
                    except (ValueError, TypeError):
                        pass
                
                if df_full is None:
                    df_full = chunk
                else:
                    df_full = pd.concat([df_full, chunk], ignore_index=True)
                
                total_rows += len(chunk)
            
            # Save processed CSV and load to database
            if df_full is not None:
                df_full.to_csv(csv_path, index=False)
                
                with engine.begin() as conn:
                    df_full.to_sql(table_name, conn, if_exists='replace', index=False, method='multi')
            
            # Quick profile (instant - analyzes sample only)
            df_sample = df_full.iloc[:min(10000, len(df_full))] if df_full is not None else pd.DataFrame()
            profile = DataProfiler.profile(df_sample, quick=True)
            
            # Create dataset record
            dataset = Dataset(
                id=dataset_id,
                name=filename.replace(".csv", ""),
                filename=filename,
                row_count=total_rows,
                columns=columns,
                profile=profile,
                created_at=datetime.utcnow(),
            )
            
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
            
            return {
                "success": True,
                "data": {
                    "id": dataset.id,
                    "name": dataset.name,
                    "filename": dataset.filename,
                    "rowCount": dataset.row_count,
                    "columns": dataset.columns,
                    "profile": dataset.profile,
                    "uploadedAt": dataset.created_at.isoformat(),
                }
            }
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_dataset(dataset_id: str, db: Session) -> dict:
        """Get dataset information"""
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                return {
                    "success": False,
                    "error": "Dataset not found"
                }
            
            return {
                "success": True,
                "data": {
                    "id": dataset.id,
                    "name": dataset.name,
                    "filename": dataset.filename,
                    "rowCount": dataset.row_count,
                    "columns": dataset.columns,
                    "profile": dataset.profile,
                    "uploadedAt": dataset.created_at.isoformat(),
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def list_datasets(db: Session) -> dict:
        """List all datasets"""
        try:
            datasets = db.query(Dataset).all()
            
            return {
                "success": True,
                "data": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "filename": d.filename,
                        "rowCount": d.row_count,
                        "columns": d.columns,
                        "profile": d.profile,
                        "uploadedAt": d.created_at.isoformat(),
                    }
                    for d in datasets
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def delete_dataset(dataset_id: str, db: Session) -> dict:
        """Delete dataset"""
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                return {
                    "success": False,
                    "error": "Dataset not found"
                }
            
            db.delete(dataset)
            db.commit()
            
            return {
                "success": True,
                "message": "Dataset deleted successfully"
            }
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
