from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import os

from app.database import get_db
from app.models import LandlordProfile, User
from app.services.rapidapi_fetcher import RapidAPIFetcher
from app.services.realtor16_fetcher import Realtor16Fetcher

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

@router.post("/admin/fetch-real-properties", response_model=dict)
async def admin_fetch_real_properties_with_landlords(
    property_count: int = 20,
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    获取真实房源并自动创建对应的真实房东
    
    使用方法:
    curl -X POST "http://3.14.150.166:8000/api/v1/admin/fetch-real-properties?property_count=15" \
      -H "X-Admin-Key: Admin123456"
    """
    
    # 检查API密钥
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="RapidAPI key not configured"
        )
    
    # 限制单次获取数量
    if property_count > 50:
        property_count = 50
    
    try:
        # 使用新的获取器
        fetcher = Realtor16Fetcher(api_key)
        
        # 获取房源并自动创建房东
        result = fetcher.get_real_properties_with_landlords(
            db=db,
            limit=property_count
        )
        
        return {
            "success": result['success'],
            "total_fetched": result.get('total_fetched', 0),
            "saved_count": result.get('saved_count', 0),
            "created_landlords": result.get('created_landlords', 0),
            "api_calls_used": result.get('api_calls_used', 1),
            "message": result.get('message', ''),
            "properties_preview": result.get('properties', [])[:3]  # 显示前3个
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during real property fetch: {str(e)}"
        )

@router.get("/admin/real-landlords")
async def list_real_landlords(
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    列出所有通过API自动创建的真实房东
    
    使用方法:
    curl -X GET "http://3.14.150.166:8000/api/v1/admin/real-landlords" \
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
    
    
@router.delete("/admin/reset-database")
async def reset_database(
    confirm: str = "RESET_ALL_DATA",
    admin_verified: bool = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    清空所有房源和房东数据（保留用户账户）
    
    使用方法:
    curl -X DELETE "http://3.14.150.166:8000/api/v1/admin/reset-database?confirm=RESET_ALL_DATA" \
      -H "X-Admin-Key: Admin123456"
    """
    
    if confirm != "RESET_ALL_DATA":
        raise HTTPException(
            status_code=400,
            detail="Must provide confirm=RESET_ALL_DATA to reset database"
        )
    
    try:
        # 删除所有房源
        properties_deleted = db.query(Property).delete()
        
        # 删除所有房东资料
        landlords_deleted = db.query(LandlordProfile).delete()
        
        # 删除所有房东用户账户（邮箱包含realtor16.auto的）
        auto_users_deleted = db.query(User).filter(
            User.email.like('%realtor16.auto%')
        ).delete(synchronize_session=False)
        
        # 可选：删除所有用户（如果您想完全重置）
        # all_users_deleted = db.query(User).delete()
        
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