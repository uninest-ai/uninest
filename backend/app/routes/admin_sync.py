from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import os
from datetime import datetime
from sqlalchemy import text 

from app.database import get_db
from app.models import LandlordProfile, User, Property, PropertyImage  
from app.services.rapidapi_fetcher import RapidAPIFetcher
from app.services.realtor16_fetcher import Realtor16Fetcher
from app.services.multi_source_fetcher import MultiSourceFetcher
from app.services.sync_scheduler import get_scheduler_status, manual_sync, start_property_sync, stop_property_sync

router = APIRouter()

# 管理员密钥验证
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "horizon-admin-2024")

def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    """验证管理员密钥"""
    if not x_admin_key or x_admin_key != ADMIN_SECRET:
        raise HTTPException(
            status_code=403, 
            detail="Invalid or missing admin key. Use X-Admin-Key header."
        )
    return True

class AdminFetchResponse(BaseModel):
    success: bool
    landlord_id: int
    total_fetched: int
    saved_count: int
    api_calls_used: int
    message: str
    properties_preview: List[dict] = []

class BatchFetchResponse(BaseModel):
    total_landlords: int
    total_properties_saved: int
    total_api_calls_used: int
    successful_landlords: int
    failed_landlords: int
    results: List[dict]

@router.get("/admin/status")
async def admin_status(
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    检查系统状态
    
    使用方法:
    curl -X GET "http://localhost:8000/api/v1/admin/status" \
      -H "X-Admin-Key: your-admin-secret"
    """
    
    # 检查API配置
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    api_configured = bool(rapidapi_key and len(rapidapi_key) > 10)
    
    # 统计房东数量
    total_landlords = db.query(LandlordProfile).count()
    
    # 统计房源数量
    from app.models import Property
    total_properties = db.query(Property).count()
    
    return {
        "system_status": "healthy",
        "api_configured": api_configured,
        "admin_authenticated": True,
        "total_landlords": total_landlords,
        "total_properties": total_properties,
        "rapidapi_key_length": len(rapidapi_key) if rapidapi_key else 0
    }

@router.get("/admin/landlords")
async def list_landlords(
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    列出所有房东
    
    使用方法:
    curl -X GET "http://localhost:8000/api/v1/admin/landlords" \
      -H "X-Admin-Key: your-admin-secret"
    """
    
    landlords = db.query(LandlordProfile).all()
    
    landlords_info = []
    for landlord in landlords:
        # 统计该房东的房源数量
        from app.models import Property
        property_count = db.query(Property).filter(
            Property.landlord_id == landlord.id
        ).count()
        
        landlords_info.append({
            "id": landlord.id,
            "user_id": landlord.user_id,
            "company_name": landlord.company_name,
            "contact_phone": landlord.contact_phone,
            "property_count": property_count,
            "created_at": landlord.created_at
        })
    
    return {
        "total_landlords": len(landlords),
        "landlords": landlords_info
    }

@router.post("/admin/fetch-properties/{landlord_id}", response_model=AdminFetchResponse)
async def admin_fetch_properties(
    landlord_id: int,
    property_count: int = 20,
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    为指定房东获取房源
    
    使用方法:
    curl -X POST "http://localhost:8000/api/v1/admin/fetch-properties/1?property_count=15" \
      -H "X-Admin-Key: your-admin-secret"
    """
    
    # 检查房东是否存在
    landlord = db.query(LandlordProfile).filter(
        LandlordProfile.id == landlord_id
    ).first()
    
    if not landlord:
        raise HTTPException(
            status_code=404, 
            detail=f"Landlord with ID {landlord_id} not found"
        )
    
    # 检查API密钥
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="RapidAPI key not configured. Add RAPIDAPI_KEY to .env file"
        )
    
    # 限制单次获取数量
    if property_count > 50:
        property_count = 50
    
    try:
        # 初始化获取器
        # fetcher = RapidAPIFetcher(api_key)
        fetcher = Realtor16Fetcher(api_key)
        
        # 获取房源
        result = fetcher.get_real_properties(
            db=db,
            landlord_id=landlord_id,
            limit=property_count
        )
        
        if result['success']:
            return AdminFetchResponse(
                success=True,
                landlord_id=landlord_id,
                total_fetched=result.get('total_fetched', 0),
                saved_count=result.get('saved_count', 0),
                api_calls_used=result.get('api_calls_used', 1),
                message=f"Successfully fetched properties for landlord {landlord_id}",
                properties_preview=result.get('properties', [])[:3]  # 显示前3个
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch properties: {result.get('error', 'Unknown error')}"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during property fetch: {str(e)}"
        )

@router.post("/admin/fetch-all-landlords", response_model=BatchFetchResponse)
async def admin_fetch_for_all_landlords(
    property_count_per_landlord: int = 10,
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    为所有房东批量获取房源
    
    使用方法:
    curl -X POST "http://localhost:8000/api/v1/admin/fetch-all-landlords?property_count_per_landlord=15" \
      -H "X-Admin-Key: your-admin-secret"
    """
    
    # 获取所有房东
    landlords = db.query(LandlordProfile).all()
    
    if not landlords:
        raise HTTPException(
            status_code=404, 
            detail="No landlords found in the system"
        )
    
    # 检查API密钥
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="RapidAPI key not configured"
        )
    
    # 限制单个房东的获取数量
    if property_count_per_landlord > 30:
        property_count_per_landlord = 30
    
    results = []
    total_saved = 0
    total_api_calls = 0
    successful_count = 0
    failed_count = 0
    
    fetcher = RapidAPIFetcher(api_key)
    
    for landlord in landlords:
        try:
            result = fetcher.get_real_properties(
                db=db,
                landlord_id=landlord.id,
                limit=property_count_per_landlord
            )
            
            if result['success']:
                successful_count += 1
                saved_count = result.get('saved_count', 0)
                total_saved += saved_count
                total_api_calls += result.get('api_calls_used', 1)
                
                results.append({
                    "landlord_id": landlord.id,
                    "success": True,
                    "saved_count": saved_count,
                    "total_fetched": result.get('total_fetched', 0),
                    "message": f"Successfully processed {saved_count} properties"
                })
            else:
                failed_count += 1
                results.append({
                    "landlord_id": landlord.id,
                    "success": False,
                    "saved_count": 0,
                    "error": result.get('error', 'Unknown error')
                })
                
        except Exception as e:
            failed_count += 1
            results.append({
                "landlord_id": landlord.id,
                "success": False,
                "saved_count": 0,
                "error": str(e)
            })
    
    return BatchFetchResponse(
        total_landlords=len(landlords),
        total_properties_saved=total_saved,
        total_api_calls_used=total_api_calls,
        successful_landlords=successful_count,
        failed_landlords=failed_count,
        results=results
    )

@router.delete("/admin/cleanup-properties/{landlord_id}")
async def admin_cleanup_properties(
    landlord_id: int,
    older_than_days: int = 30,
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    清理指定房东的旧房源
    
    使用方法:
    curl -X DELETE "http://localhost:8000/api/v1/admin/cleanup-properties/1?older_than_days=30" \
      -H "X-Admin-Key: your-admin-secret"
    """
    
    from app.models import Property
    from datetime import datetime, timedelta
    
    # 检查房东是否存在
    landlord = db.query(LandlordProfile).filter(
        LandlordProfile.id == landlord_id
    ).first()
    
    if not landlord:
        raise HTTPException(
            status_code=404,
            detail=f"Landlord with ID {landlord_id} not found"
        )
    
    # 计算截止日期
    cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
    
    # 查找要清理的房源
    old_properties = db.query(Property).filter(
        Property.landlord_id == landlord_id,
        Property.created_at < cutoff_date,
        Property.is_active == True
    ).all()
    
    # 标记为非活跃而不是删除
    cleanup_count = 0
    for prop in old_properties:
        prop.is_active = False
        cleanup_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "landlord_id": landlord_id,
        "cleaned_count": cleanup_count,
        "cutoff_date": cutoff_date,
        "message": f"Cleaned up {cleanup_count} properties older than {older_than_days} days"
    }

@router.post("/admin/fetch-real-properties")
async def admin_fetch_real_properties_with_landlords(
    property_count: int = 20,
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """获取真实房源并自动创建对应的真实房东"""
    
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="RapidAPI key not configured")
    
    if property_count > 50:
        property_count = 50
    
    try:
        fetcher = Realtor16Fetcher(api_key)
        result = fetcher.get_real_properties_with_landlords(db=db, limit=property_count)
        
        return {
            "success": result['success'],
            "total_fetched": result.get('total_fetched', 0),
            "saved_count": result.get('saved_count', 0),
            "created_landlords": result.get('created_landlords', 0),
            "api_calls_used": result.get('api_calls_used', 1),
            "message": result.get('message', ''),
            "properties_preview": result.get('properties', [])[:3]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/admin/real-landlords")
async def list_real_landlords(
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    列出所有通过API自动创建的真实房东
    
    使用方法:
    curl -X GET "http://3.145.189.113:8000/api/v1/admin/real-landlords" \
      -H "X-Admin-Key: Admin123456"
    """
    
    # 查询所有验证状态为True的房东（表示来自真实API）
    real_landlords = db.query(LandlordProfile).filter(
        LandlordProfile.verification_status == True
    ).all()
    
    landlords_info = []
    for landlord in real_landlords:
        # 统计房源数量
        property_count = db.query(Property).filter(
            Property.landlord_id == landlord.id
        ).count()
        
        landlords_info.append({
            "id": landlord.id,
            "company_name": landlord.company_name,
            "contact_phone": landlord.contact_phone,
            "property_count": property_count,
            "created_at": landlord.created_at,
            "is_real_landlord": True
        })
    
    return {
        "total_real_landlords": len(real_landlords),
        "landlords": landlords_info
    }
    

@router.post("/admin/fetch-multi-source-properties")
async def admin_fetch_multi_source_properties(
    property_count: int = 30,
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Fetch comprehensive property data from multiple real estate APIs
    
    This endpoint combines data from:
    - Realtor16 API (primary source)
    - Realty Mole API (secondary source) 
    - Custom Pittsburgh neighborhood data (tertiary source)
    
    Usage:
    curl -X POST "http://3.145.189.113:8000/api/v1/admin/fetch-multi-source-properties?property_count=50" \
      -H "X-Admin-Key: Admin123456"
    """
    
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="RapidAPI key not configured"
        )
    
    if property_count > 100:
        property_count = 100
    
    try:
        fetcher = MultiSourceFetcher(api_key)
        result = fetcher.get_comprehensive_property_data(db=db, limit=property_count)
        
        if result['success']:
            return {
                "success": True,
                "total_fetched": result.get('total_fetched', 0),
                "saved_count": result.get('saved_count', 0),
                "created_landlords": result.get('created_landlords', 0),
                "api_sources_used": result.get('api_sources_used', []),
                "properties_preview": result.get('properties', [])[:5],
                "errors": result.get('errors', []),
                "message": f"Successfully fetched {result.get('saved_count', 0)} properties from {len(result.get('api_sources_used', []))} different sources"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch properties: {result.get('errors', ['Unknown error'])}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during multi-source fetch: {str(e)}"
        )

@router.get("/admin/property-sources")
async def get_property_sources_stats(
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Get statistics about property sources and data quality
    
    Usage:
    curl -X GET "http://3.145.189.113:8000/api/v1/admin/property-sources" \
      -H "X-Admin-Key: Admin123456"
    """
    
    try:
        # Count properties by source (based on description patterns)
        all_properties = db.query(Property).filter(Property.is_active == True).all()
        
        source_stats = {
            'realtor16': 0,
            'realty_mole': 0,
            'custom_pittsburgh': 0,
            'other': 0
        }
        
        neighborhood_stats = {}
        price_ranges = {'under_1000': 0, '1000_1500': 0, '1500_2000': 0, 'over_2000': 0}
        property_types = {}
        
        for prop in all_properties:
            # Categorize by source
            desc = prop.description.lower() if prop.description else ''
            if 'realtor16' in desc or 'realtor.com' in desc:
                source_stats['realtor16'] += 1
            elif 'realty mole' in desc or 'realty-mole' in desc:
                source_stats['realty_mole'] += 1
            elif 'pittsburgh' in desc and ('neighborhood' in desc or 'property management' in desc):
                source_stats['custom_pittsburgh'] += 1
            else:
                source_stats['other'] += 1
            
            # Neighborhood stats
            if prop.address:
                for neighborhood in ['Oakland', 'Shadyside', 'Squirrel Hill', 'Greenfield', 
                                   'Point Breeze', 'Regent Square', 'Bloomfield', 'Friendship']:
                    if neighborhood in prop.address:
                        neighborhood_stats[neighborhood] = neighborhood_stats.get(neighborhood, 0) + 1
                        break
            
            # Price ranges
            if prop.price < 1000:
                price_ranges['under_1000'] += 1
            elif prop.price < 1500:
                price_ranges['1000_1500'] += 1
            elif prop.price < 2000:
                price_ranges['1500_2000'] += 1
            else:
                price_ranges['over_2000'] += 1
                
            # Property types
            prop_type = prop.property_type or 'unknown'
            property_types[prop_type] = property_types.get(prop_type, 0) + 1
        
        return {
            "total_active_properties": len(all_properties),
            "source_breakdown": source_stats,
            "neighborhood_distribution": neighborhood_stats,
            "price_range_distribution": price_ranges,
            "property_type_distribution": property_types,
            "data_quality_metrics": {
                "properties_with_coordinates": len([p for p in all_properties if p.latitude and p.longitude]),
                "properties_with_photos": len([p for p in all_properties if p.image_url]),
                "average_price": sum(p.price for p in all_properties) / len(all_properties) if all_properties else 0,
                "properties_created_today": len([p for p in all_properties if p.created_at and 
                                               p.created_at.date() == datetime.now().date()])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting property statistics: {str(e)}"
        )

@router.delete("/admin/reset-database")
async def reset_database(
    confirm: str = "RESET_ALL_DATA",
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """清空所有房源和房东数据"""
    
    if confirm != "RESET_ALL_DATA":
        raise HTTPException(
            status_code=400,
            detail="Must provide confirm=RESET_ALL_DATA to reset database"
        )
    
    try:
        # 使用text()包装所有SQL语句
        
        # 1. 删除关联表数据
        db.execute(text("DELETE FROM property_preferences"))
        db.execute(text("DELETE FROM roommate_preferences"))
        
        # 2. 删除房源相关数据
        db.execute(text("DELETE FROM property_images"))
        db.execute(text("DELETE FROM comments"))
        db.execute(text("DELETE FROM interactions"))
        db.execute(text("DELETE FROM messages"))
        db.execute(text("DELETE FROM user_preferences"))
        
        # 3. 删除房源
        properties_deleted = db.query(Property).delete()
        
        # 4. 删除房东资料
        landlords_deleted = db.query(LandlordProfile).delete()
        
        # 5. 删除自动生成的用户
        auto_users_deleted = db.query(User).filter(
            User.email.like('%realtor16.auto%')
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Database reset completed",
            "properties_deleted": properties_deleted,
            "landlords_deleted": landlords_deleted,
            "auto_users_deleted": auto_users_deleted
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting database: {str(e)}"
        )

@router.get("/admin/sync/status")
async def get_sync_scheduler_status(
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    Get the status of the automatic property synchronization scheduler
    
    Usage:
    curl -X GET "http://3.145.189.113:8000/api/v1/admin/sync/status" \
      -H "X-Admin-Key: Admin123456"
    """
    
    try:
        status = get_scheduler_status()
        return {
            "scheduler_status": status,
            "api_configured": bool(os.getenv("RAPIDAPI_KEY")),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting scheduler status: {str(e)}"
        )

@router.post("/admin/sync/start")
async def start_sync_scheduler(
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    Start the automatic property synchronization scheduler
    
    Usage:
    curl -X POST "http://3.145.189.113:8000/api/v1/admin/sync/start" \
      -H "X-Admin-Key: Admin123456"
    """
    
    try:
        start_property_sync()
        return {
            "success": True,
            "message": "Property sync scheduler started",
            "status": get_scheduler_status()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting scheduler: {str(e)}"
        )

@router.post("/admin/sync/stop")
async def stop_sync_scheduler(
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    Stop the automatic property synchronization scheduler
    
    Usage:
    curl -X POST "http://3.145.189.113:8000/api/v1/admin/sync/stop" \
      -H "X-Admin-Key: Admin123456"
    """
    
    try:
        stop_property_sync()
        return {
            "success": True,
            "message": "Property sync scheduler stopped"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping scheduler: {str(e)}"
        )

@router.post("/admin/sync/manual")
async def trigger_manual_sync(
    sync_type: str = "incremental",  # incremental, comprehensive, cleanup
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    Manually trigger a property synchronization
    
    Types:
    - incremental: Quick sync with latest properties
    - comprehensive: Full sync from all sources  
    - cleanup: Remove old inactive properties
    
    Usage:
    curl -X POST "http://3.145.189.113:8000/api/v1/admin/sync/manual?sync_type=comprehensive" \
      -H "X-Admin-Key: Admin123456"
    """
    
    if sync_type not in ['incremental', 'comprehensive', 'cleanup']:
        raise HTTPException(
            status_code=400,
            detail="sync_type must be one of: incremental, comprehensive, cleanup"
        )
    
    try:
        result = manual_sync(sync_type)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during manual sync: {str(e)}"
        )

@router.get("/admin/property-links")
async def get_property_links_report(
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Get detailed report of property links and data sources
    
    Usage:
    curl -X GET "http://3.145.189.113:8000/api/v1/admin/property-links" \
      -H "X-Admin-Key: Admin123456"
    """
    
    try:
        # Get all active properties with their landlords
        properties_with_landlords = db.query(Property).join(LandlordProfile).filter(
            Property.is_active == True
        ).all()
        
        link_report = {
            "total_properties": len(properties_with_landlords),
            "properties_with_links": [],
            "landlord_link_summary": {},
            "link_statistics": {
                "realtor_com_links": 0,
                "zillow_links": 0,
                "apartments_com_links": 0,
                "mls_ids": 0,
                "office_websites": 0
            }
        }
        
        for prop in properties_with_landlords:
            property_info = {
                "property_id": prop.id,
                "title": prop.title,
                "price": prop.price,
                "address": prop.address,
                "landlord_company": prop.landlord.company_name if prop.landlord else "N/A",
                "links_found": []
            }
            
            # Check property description for links
            if prop.description:
                desc = prop.description.lower()
                
                # Count different types of links
                if 'realtor.com' in desc or 'realtor16' in desc:
                    property_info["links_found"].append("Realtor.com")
                    link_report["link_statistics"]["realtor_com_links"] += 1
                
                if 'zillow.com' in desc:
                    property_info["links_found"].append("Zillow")
                    link_report["link_statistics"]["zillow_links"] += 1
                    
                if 'apartments.com' in desc:
                    property_info["links_found"].append("Apartments.com") 
                    link_report["link_statistics"]["apartments_com_links"] += 1
                    
                if 'mls id:' in desc:
                    property_info["links_found"].append("MLS ID")
                    link_report["link_statistics"]["mls_ids"] += 1
            
            # Check landlord description for office websites
            if prop.landlord and prop.landlord.description:
                landlord_desc = prop.landlord.description.lower()
                if 'website:' in landlord_desc or 'http' in landlord_desc:
                    property_info["links_found"].append("Landlord Website")
                    link_report["link_statistics"]["office_websites"] += 1
                    
                    # Add to landlord summary
                    company = prop.landlord.company_name
                    if company not in link_report["landlord_link_summary"]:
                        link_report["landlord_link_summary"][company] = {
                            "description": prop.landlord.description,
                            "contact_phone": prop.landlord.contact_phone,
                            "property_count": 0
                        }
                    link_report["landlord_link_summary"][company]["property_count"] += 1
            
            # Only include properties with links
            if property_info["links_found"]:
                link_report["properties_with_links"].append(property_info)
        
        # Calculate percentages
        total = len(properties_with_landlords)
        link_report["coverage_stats"] = {
            "properties_with_any_links": len(link_report["properties_with_links"]),
            "coverage_percentage": round((len(link_report["properties_with_links"]) / total * 100), 2) if total > 0 else 0,
            "realtor_coverage": round((link_report["link_statistics"]["realtor_com_links"] / total * 100), 2) if total > 0 else 0
        }
        
        return link_report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating links report: {str(e)}"
        )

@router.get("/admin/property-details/{property_id}")
async def get_property_details(
    property_id: int,
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific property including all links
    
    Usage:
    curl -X GET "http://3.145.189.113:8000/api/v1/admin/property-details/123" \
      -H "X-Admin-Key: Admin123456"
    """
    
    try:
        property_details = db.query(Property).filter(Property.id == property_id).first()
        
        if not property_details:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Get landlord details
        landlord = db.query(LandlordProfile).filter(
            LandlordProfile.id == property_details.landlord_id
        ).first()
        
        return {
            "property": {
                "id": property_details.id,
                "title": property_details.title,
                "price": property_details.price,
                "description": property_details.description,
                "address": property_details.address,
                "property_type": property_details.property_type,
                "bedrooms": property_details.bedrooms,
                "bathrooms": property_details.bathrooms,
                "area": property_details.area,
                "latitude": property_details.latitude,
                "longitude": property_details.longitude,
                "created_at": property_details.created_at.isoformat() if property_details.created_at else None,
                "is_active": property_details.is_active
            },
            "landlord": {
                "id": landlord.id if landlord else None,
                "company_name": landlord.company_name if landlord else None,
                "contact_phone": landlord.contact_phone if landlord else None,
                "description": landlord.description if landlord else None,
                "verification_status": landlord.verification_status if landlord else None,
                "created_at": landlord.created_at.isoformat() if landlord and landlord.created_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting property details: {str(e)}"
        )

@router.post("/admin/migrate-images")
async def migrate_api_images_to_property_images(
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Migrate API images from api_images field to PropertyImage records
    
    This fixes the issue where scraped images are stored in api_images JSON field
    but not displayed on the frontend because they're not in PropertyImage table.
    
    Usage:
    curl -X POST "http://3.145.189.113:8000/api/v1/admin/migrate-images" \
      -H "X-Admin-Key: Admin123456"
    """
    
    try:
        import json
        
        print("Starting API images migration...")
        
        # Get all properties with api_images
        properties_with_images = db.query(Property).filter(
            Property.api_images.is_not(None),
            Property.api_images != "[]",
            Property.api_images != ""
        ).all()
        
        if not properties_with_images:
            return {
                "success": True,
                "message": "No properties with API images found",
                "migrated_properties": 0,
                "total_images_created": 0,
                "skipped_properties": 0,
                "errors": []
            }
        
        migrated_count = 0
        skipped_count = 0
        total_images = 0
        errors = []
        
        for prop in properties_with_images:
            try:
                # Check if images already exist for this property
                existing_images = db.query(PropertyImage).filter(
                    PropertyImage.property_id == prop.id
                ).count()
                
                if existing_images > 0:
                    skipped_count += 1
                    continue
                
                # Parse api_images JSON
                api_images = prop.api_images
                if isinstance(api_images, str):
                    try:
                        api_images = json.loads(api_images)
                    except json.JSONDecodeError:
                        errors.append(f"Property {prop.id}: Invalid JSON in api_images")
                        continue
                
                if not api_images or not isinstance(api_images, list):
                    continue
                
                # Create PropertyImage records
                images_created = 0
                for i, image_url in enumerate(api_images):
                    if not image_url or not isinstance(image_url, str):
                        continue
                        
                    # Create PropertyImage record
                    property_image = PropertyImage(
                        property_id=prop.id,
                        image_url=image_url,
                        is_primary=(i == 0),  # First image is primary
                        labels=None,
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(property_image)
                    images_created += 1
                    total_images += 1
                
                if images_created > 0:
                    # Update property's main image_url if it's null
                    if not prop.image_url:
                        prop.image_url = api_images[0]
                    
                    migrated_count += 1
                
            except Exception as e:
                errors.append(f"Property {prop.id}: {str(e)}")
                db.rollback()
                continue
        
        # Commit all changes
        if migrated_count > 0:
            db.commit()
        
        # Add fallback images for properties without any images
        fallback_added = 0
        try:
            # Fallback image URLs (using Unsplash for realistic property photos)
            fallback_images = [
                "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Modern house
                "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Beautiful home
                "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Contemporary house
                "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Apartment building
                "https://images.unsplash.com/photo-1519452465094-7d23f0b4a4b1?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Studio apartment
            ]
            
            # Find properties without images
            properties_without_images = db.query(Property).outerjoin(PropertyImage).filter(
                PropertyImage.id.is_(None),
                Property.is_active == True
            ).all()
            
            for prop in properties_without_images:
                # Choose fallback image based on property type
                if prop.property_type == 'apartment':
                    fallback_url = fallback_images[3]  # Apartment building
                elif prop.property_type == 'studio':
                    fallback_url = fallback_images[4]  # Studio
                elif prop.property_type == 'house':
                    fallback_url = fallback_images[0]  # Modern house
                elif prop.property_type == 'condo':
                    fallback_url = fallback_images[2]  # Contemporary house
                else:
                    fallback_url = fallback_images[1]  # Default beautiful home
                
                try:
                    # Create fallback PropertyImage
                    property_image = PropertyImage(
                        property_id=prop.id,
                        image_url=fallback_url,
                        is_primary=True,
                        labels=["fallback_image"],
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(property_image)
                    
                    # Update property's main image_url if it's null
                    if not prop.image_url:
                        prop.image_url = fallback_url
                    
                    fallback_added += 1
                    
                except Exception as e:
                    errors.append(f"Fallback for Property {prop.id}: {str(e)}")
            
            if fallback_added > 0:
                db.commit()
                
        except Exception as e:
            errors.append(f"Fallback images error: {str(e)}")
        
        # Verification
        total_properties = db.query(Property).filter(Property.is_active == True).count()
        properties_with_property_images = db.query(Property).join(PropertyImage).filter(Property.is_active == True).distinct().count()
        total_property_images = db.query(PropertyImage).count()
        
        return {
            "success": True,
            "message": "Image migration completed successfully",
            "migrated_properties": migrated_count,
            "total_images_created": total_images,
            "fallback_images_added": fallback_added,
            "skipped_properties": skipped_count,
            "errors": errors,
            "verification": {
                "total_active_properties": total_properties,
                "properties_with_images": properties_with_property_images,
                "total_property_images": total_property_images,
                "coverage_percentage": round((properties_with_property_images / total_properties * 100), 2) if total_properties > 0 else 0
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error during image migration: {str(e)}"
        )