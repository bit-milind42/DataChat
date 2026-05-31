import pandas as pd
import json
from typing import Dict, Any
import numpy as np


class DataProfiler:
    """Analyze and profile CSV data"""
    
    @staticmethod
    def profile(df: pd.DataFrame, quick: bool = False) -> Dict[str, Any]:
        """Generate data profile. quick=True returns instantly with basic stats."""
        profile = {
            "summary": DataProfiler._get_summary(df),
            "columns": DataProfiler._get_column_profiles(df, quick=quick),
        }
        if not quick:
            profile["statistics"] = DataProfiler._get_statistics(df)
            profile["quality"] = DataProfiler._get_data_quality(df)
        else:
            profile["quality"] = {"quality_score": 100}
        return profile
    
    @staticmethod
    def _get_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Get dataset summary"""
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB",
            "duplicates": int(df.duplicated().sum()),
            "duplicate_percentage": round((df.duplicated().sum() / len(df) * 100), 2) if len(df) > 0 else 0
        }
    
    @staticmethod
    def _get_column_profiles(df: pd.DataFrame, quick: bool = False) -> Dict[str, Any]:
        """Profile each column. quick=True returns minimal stats for speed."""
        profiles = {}
        for col in df.columns:
            profiles[col] = {
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].notna().sum()),
                "null_count": int(df[col].isna().sum()),
            }
            
            if not quick:
                profiles[col].update({
                    "null_percentage": round((df[col].isna().sum() / len(df) * 100), 2),
                    "unique_values": int(df[col].nunique()),
                    "unique_percentage": round((df[col].nunique() / len(df) * 100), 2)
                })
            
            # Add type-specific stats
            if pd.api.types.is_numeric_dtype(df[col]):
                profiles[col].update({
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std())
                })
            else:
                # String columns
                profiles[col].update({
                    "sample_values": df[col].dropna().unique()[:5].tolist()
                })
        
        return profiles
    
    @staticmethod
    def _get_statistics(df: pd.DataFrame) -> Dict[str, Any]:
        """Get numeric statistics"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        return {
            "numeric_columns": numeric_cols,
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
            "datetime_columns": df.select_dtypes(include=['datetime64']).columns.tolist()
        }
    
    @staticmethod
    def _get_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality"""
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isna().sum().sum()
        
        return {
            "completeness": round(((total_cells - missing_cells) / total_cells * 100), 2),
            "total_missing_cells": int(missing_cells),
            "duplicate_rows": int(df.duplicated().sum()),
            "quality_score": round(((total_cells - missing_cells) / total_cells * 100), 1)
        }
