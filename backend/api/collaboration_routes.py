"""API routes for dashboards, team collaboration, and scheduled reports"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from databases.models import get_db, Dataset, QueryResult
from databases.collaboration_models import (
    Dashboard, Widget, ScheduledReport, User, Team, TeamMember,
    SavedQuery, QueryHistory
)
from agents.follow_up_agent import FollowUpAgent
from api.schemas import (
    DashboardCreate, DashboardUpdate, WidgetCreate, WidgetUpdate,
    ScheduledReportCreate, UserCreate, TeamCreate, SavedQueryCreate
)

router = APIRouter(prefix="/api", tags=["collaboration"])

follow_up_agent = FollowUpAgent()


# ===================== FOLLOW-UP QUESTIONS =====================

@router.post("/queries/{query_id}/follow-ups")
async def get_follow_up_questions(
    query_id: str,
    previous_questions: list = None,
    db: Session = Depends(get_db)
):
    """Get context-aware follow-up questions for a query result"""
    try:
        query_result = db.query(QueryResult).filter(QueryResult.id == query_id).first()
        if not query_result:
            raise HTTPException(status_code=404, detail="Query not found")
        
        dataset = db.query(Dataset).filter(Dataset.id == query_result.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Generate follow-up questions
        suggestions = follow_up_agent.generate_follow_ups(
            original_question=query_result.query,
            results=query_result.rows_data or [],
            columns=dataset.columns or [],
            dataset=dataset,
            previous_questions=previous_questions or []
        )
        
        # Store in query history
        history_record = QueryHistory(
            dataset_id=dataset.id,
            question=query_result.query,
            follow_up_questions=suggestions.get("follow_up_questions", []),
            insights={"suggested_analyses": suggestions.get("available_analyses", [])}
        )
        db.add(history_record)
        db.commit()
        
        return {
            "success": True,
            "data": suggestions
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ===================== DASHBOARDS =====================

@router.post("/dashboards")
async def create_dashboard(
    dashboard: DashboardCreate,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Create a new dashboard"""
    try:
        new_dashboard = Dashboard(
            id=str(uuid.uuid4()),
            name=dashboard.name,
            description=dashboard.description,
            owner_id=user_id,
            dataset_ids=dashboard.dataset_ids or [],
            is_public=dashboard.is_public or False
        )
        db.add(new_dashboard)
        db.commit()
        db.refresh(new_dashboard)
        
        return {
            "success": True,
            "data": {
                "id": new_dashboard.id,
                "name": new_dashboard.name,
                "createdAt": new_dashboard.created_at.isoformat(),
                "owner_id": new_dashboard.owner_id
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/dashboards")
async def list_dashboards(
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """List all dashboards accessible to user"""
    try:
        # Get user's own dashboards and shared dashboards
        dashboards = db.query(Dashboard).filter(
            (Dashboard.owner_id == user_id) | (Dashboard.shared_with.any(User.id == user_id))
        ).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                    "isPublic": d.is_public,
                    "owner_id": d.owner_id,
                    "datasetCount": len(d.dataset_ids or []),
                    "widgetCount": len(d.widgets),
                    "createdAt": d.created_at.isoformat(),
                    "updatedAt": d.updated_at.isoformat()
                }
                for d in dashboards
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str, db: Session = Depends(get_db)):
    """Get dashboard details"""
    try:
        dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        return {
            "success": True,
            "data": {
                "id": dashboard.id,
                "name": dashboard.name,
                "description": dashboard.description,
                "datasetIds": dashboard.dataset_ids or [],
                "layout": dashboard.layout or {},
                "isPublic": dashboard.is_public,
                "owner_id": dashboard.owner_id,
                "widgets": [
                    {
                        "id": w.id,
                        "title": w.title,
                        "type": w.widget_type,
                        "position": {"x": w.position_x, "y": w.position_y},
                        "size": {"width": w.width, "height": w.height},
                        "config": w.config or {},
                        "queryId": w.query_id
                    }
                    for w in dashboard.widgets
                ],
                "createdAt": dashboard.created_at.isoformat(),
                "updatedAt": dashboard.updated_at.isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: str,
    dashboard: DashboardUpdate,
    db: Session = Depends(get_db)
):
    """Update dashboard"""
    try:
        existing = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        if dashboard.name:
            existing.name = dashboard.name
        if dashboard.description is not None:
            existing.description = dashboard.description
        if dashboard.dataset_ids is not None:
            existing.dataset_ids = dashboard.dataset_ids
        if dashboard.layout is not None:
            existing.layout = dashboard.layout
        if dashboard.is_public is not None:
            existing.is_public = dashboard.is_public
        
        existing.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Dashboard updated"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(dashboard_id: str, db: Session = Depends(get_db)):
    """Delete dashboard"""
    try:
        dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        db.delete(dashboard)
        db.commit()
        
        return {
            "success": True,
            "message": "Dashboard deleted"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ===================== DASHBOARD WIDGETS =====================

@router.post("/dashboards/{dashboard_id}/widgets")
async def add_widget(
    dashboard_id: str,
    widget: WidgetCreate,
    db: Session = Depends(get_db)
):
    """Add widget to dashboard"""
    try:
        dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        new_widget = Widget(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard_id,
            title=widget.title,
            widget_type=widget.widget_type,
            position_x=widget.position_x or 0,
            position_y=widget.position_y or 0,
            width=widget.width or 4,
            height=widget.height or 3,
            config=widget.config or {},
            query_id=widget.query_id
        )
        db.add(new_widget)
        db.commit()
        db.refresh(new_widget)
        
        return {
            "success": True,
            "data": {
                "id": new_widget.id,
                "title": new_widget.title,
                "type": new_widget.widget_type
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.put("/widgets/{widget_id}")
async def update_widget(widget_id: str, widget: WidgetUpdate, db: Session = Depends(get_db)):
    """Update widget"""
    try:
        existing = db.query(Widget).filter(Widget.id == widget_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        if widget.title:
            existing.title = widget.title
        if widget.position_x is not None:
            existing.position_x = widget.position_x
        if widget.position_y is not None:
            existing.position_y = widget.position_y
        if widget.width is not None:
            existing.width = widget.width
        if widget.height is not None:
            existing.height = widget.height
        if widget.config is not None:
            existing.config = widget.config
        
        existing.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Widget updated"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/widgets/{widget_id}")
async def delete_widget(widget_id: str, db: Session = Depends(get_db)):
    """Delete widget"""
    try:
        widget = db.query(Widget).filter(Widget.id == widget_id).first()
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        db.delete(widget)
        db.commit()
        
        return {
            "success": True,
            "message": "Widget deleted"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ===================== SCHEDULED REPORTS =====================

@router.post("/dashboards/{dashboard_id}/reports")
async def create_scheduled_report(
    dashboard_id: str,
    report: ScheduledReportCreate,
    db: Session = Depends(get_db)
):
    """Create scheduled report"""
    try:
        dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        new_report = ScheduledReport(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard_id,
            name=report.name,
            description=report.description,
            schedule=report.schedule,
            frequency=report.frequency,
            recipients=report.recipients or [],
            format=report.format or "pdf",
            include_insights=report.include_insights or True,
            is_active=report.is_active or True
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        return {
            "success": True,
            "data": {
                "id": new_report.id,
                "name": new_report.name,
                "frequency": new_report.frequency,
                "isActive": new_report.is_active
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/dashboards/{dashboard_id}/reports")
async def list_dashboard_reports(dashboard_id: str, db: Session = Depends(get_db)):
    """List scheduled reports for dashboard"""
    try:
        reports = db.query(ScheduledReport).filter(ScheduledReport.dashboard_id == dashboard_id).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "name": r.name,
                    "frequency": r.frequency,
                    "recipients": r.recipients,
                    "isActive": r.is_active,
                    "lastRun": r.last_run.isoformat() if r.last_run else None,
                    "nextRun": r.next_run.isoformat() if r.next_run else None
                }
                for r in reports
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.put("/reports/{report_id}")
async def update_scheduled_report(report_id: str, report: ScheduledReportCreate, db: Session = Depends(get_db)):
    """Update scheduled report"""
    try:
        existing = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if report.name:
            existing.name = report.name
        if report.description is not None:
            existing.description = report.description
        if report.schedule:
            existing.schedule = report.schedule
        if report.recipients is not None:
            existing.recipients = report.recipients
        if report.is_active is not None:
            existing.is_active = report.is_active
        
        existing.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Report updated"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/reports/{report_id}")
async def delete_scheduled_report(report_id: str, db: Session = Depends(get_db)):
    """Delete scheduled report"""
    try:
        report = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        db.delete(report)
        db.commit()
        
        return {
            "success": True,
            "message": "Report deleted"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ===================== SAVED QUERIES =====================

@router.post("/queries/save")
async def save_query(
    query: SavedQueryCreate,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Save a query for later use"""
    try:
        saved_query = SavedQuery(
            id=str(uuid.uuid4()),
            name=query.name,
            dataset_id=query.dataset_id,
            owner_id=user_id,
            question=query.question,
            query_result_id=query.query_result_id,
            tags=query.tags or [],
            is_favorite=query.is_favorite or False
        )
        db.add(saved_query)
        db.commit()
        db.refresh(saved_query)
        
        return {
            "success": True,
            "data": {
                "id": saved_query.id,
                "name": saved_query.name,
                "createdAt": saved_query.created_at.isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/queries/saved")
async def list_saved_queries(
    user_id: str = Query(...),
    dataset_id: str = Query(None),
    db: Session = Depends(get_db)
):
    """List saved queries"""
    try:
        query = db.query(SavedQuery).filter(SavedQuery.owner_id == user_id)
        
        if dataset_id:
            query = query.filter(SavedQuery.dataset_id == dataset_id)
        
        queries = query.all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": q.id,
                    "name": q.name,
                    "question": q.question,
                    "datasetId": q.dataset_id,
                    "isFavorite": q.is_favorite,
                    "tags": q.tags or [],
                    "createdAt": q.created_at.isoformat()
                }
                for q in queries
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/queries/saved/{query_id}")
async def delete_saved_query(query_id: str, db: Session = Depends(get_db)):
    """Delete saved query"""
    try:
        query = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        db.delete(query)
        db.commit()
        
        return {
            "success": True,
            "message": "Query deleted"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
