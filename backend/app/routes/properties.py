from app import schemas
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Property, PropertyImage, LandlordProfile, User
from app.schemas import PropertyCreate, PropertyResponse, PropertyUpdate
from app.auth import get_current_user
from app.services.storage_service import S3ImageService
from app.services.image_analysis import SimpleImageAnalysisService

router = APIRouter()
image_service = SimpleImageAnalysisService()
storage_service = S3ImageService()

@router.post("/", response_model=schemas.PropertyResponse)
def create_property(
    property_data: schemas.PropertyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new property listing"""
    # 检查用户是否为房东
    if current_user.user_type != "landlord":
        raise HTTPException(status_code=403, detail="Only landlords can create properties")
    
    # 获取房东资料
    landlord_profile = db.query(LandlordProfile).filter(
        LandlordProfile.user_id == current_user.id
    ).first()
    
    if not landlord_profile:
        raise HTTPException(status_code=404, detail="Landlord profile not found")
    
    # 创建新房产
    new_property = Property(
        **property_data.dict(),
        landlord_id=landlord_profile.id
    )
    
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    
    return new_property

@router.get("/", response_model=List[PropertyResponse], summary="Get All Properties")
def get_properties(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all property listings with pagination"""
    properties = db.query(Property).offset(skip).limit(limit).all()
    return properties

@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific property by ID with all its images and landlord information"""
    property = db.query(Property).filter(Property.id == property_id).first()
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Refresh to load images
    db.refresh(property)
    
    # Load landlord information
    if property.landlord_id:
        landlord = db.query(LandlordProfile).filter(LandlordProfile.id == property.landlord_id).first()
        property.landlord = landlord
    
    return property

@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a property listing"""
    property = db.query(Property).filter(Property.id == property_id).first()
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Get landlord profile
    landlord_profile = db.query(LandlordProfile).filter(
        LandlordProfile.user_id == current_user.id
    ).first()
    
    # Check case: Instead of checking property.owner_id which doesn't exist
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this property")
    
    # Update property fields
    for key, value in property_data.dict(exclude_unset=True).items():
        setattr(property, key, value)
    
    db.commit()
    db.refresh(property)
    return property

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a property listing"""
    property = db.query(Property).filter(Property.id == property_id).first()
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Get landlord profile
    landlord_profile = db.query(LandlordProfile).filter(
        LandlordProfile.user_id == current_user.id
    ).first()
    
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this property")
    
    db.delete(property)
    db.commit()
    return None

@router.post("/{property_id}/images", response_model=dict)
async def upload_property_images(
    property_id: int,
    files: List[UploadFile] = File(...),
    is_primary: bool = Form(False),  # 是否将第一张设为主图
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload multiple property images"""
    # 验证用户是否为房东
    if current_user.user_type != "landlord":
        raise HTTPException(status_code=403, detail="Only landlord can upload images")
    
    # 验证房产是否存在且属于当前房东
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail= f"Property {property_id} not exists")
    
    landlord_profile = current_user.landlord_profile
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="You are not the landlord of this properties")
    
    uploaded_images = []
    
    # 处理多张图片上传
    for i, file in enumerate(files):
        try:
            # 读取图片数据用于分析
            image_data = await file.read()
            await file.seek(0)  # 重置文件指针
            
            # 分析图片特征
            analysis_result = image_service.analyze_property_listing_image(image_data)
            
            # 上传到S3
            image_url = await storage_service.upload_image(file, property_id, landlord_profile.id)
            
            # 如果是第一张图片且is_primary为True，或者这是房产的第一张图片，则设为主图
            set_as_primary = False
            if i == 0 and is_primary:  # 第一张图片且要求设为主图
                # 将之前的主图(如果有)设为非主图
                existing_primary = db.query(PropertyImage).filter(
                    PropertyImage.property_id == property_id,
                    PropertyImage.is_primary == True
                ).first()
                
                if existing_primary:
                    existing_primary.is_primary = False
                    
                set_as_primary = True
            elif db.query(PropertyImage).filter(PropertyImage.property_id == property_id).count() == 0:
                # 如果这是房产的第一张图片，自动设为主图
                set_as_primary = True
            
            # 创建新的图片记录
            property_image = PropertyImage(
                property_id=property_id,
                image_url=image_url,
                is_primary=set_as_primary,
                labels=analysis_result.get("features", [])
            )
            
            db.add(property_image)
            db.flush()  # 获取ID但不提交
            
            # 如果是主图，更新房产的主图URL
            if set_as_primary:
                property.image_url = image_url
            
            uploaded_images.append({
                "id": property_image.id,
                "image_url": image_url,
                "is_primary": set_as_primary,
                "analysis": analysis_result.get("features", [])
            })
        
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"上传图片失败: {str(e)}"
            )
    
    # 提交所有更改
    db.commit()
    
    return {
        "status": "success",
        "message": f"{len(uploaded_images)} of images uploaded",
        "images": uploaded_images
    }

# 添加一个端点来获取房产的所有图片
@router.get("/{property_id}/images", response_model=List[dict])
async def get_property_images(
    property_id: int,
    db: Session = Depends(get_db)
):
    """获取房产的所有图片"""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail= f"Property {property_id} not exists")
    
    images = db.query(PropertyImage).filter(
        PropertyImage.property_id == property_id
    ).all()
    
    return [
        {
            "id": image.id,
            "image_url": image.image_url,
            "is_primary": image.is_primary,
            "labels": image.labels
        }
        for image in images
    ]

# 添加一个端点来删除房产图片
@router.delete("/{property_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property_image(
    property_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete property images"""
    # 验证用户是否为房东
    if current_user.user_type != "landlord":
        raise HTTPException(status_code=403, detail="Only landlord can delete properties images")
    
    # 验证房产是否存在且属于当前房东
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not exists")
    
    landlord_profile = current_user.landlord_profile
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete images (you are not the landlord of this properties)")
    
    # 查找要删除的图片
    image = db.query(PropertyImage).filter(
        PropertyImage.id == image_id,
        PropertyImage.property_id == property_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail=f"Property {image_id} not exists")
    
    # 如果删除的是主图，需要选择另一张作为主图
    if image.is_primary:
        # 查找其他图片
        other_image = db.query(PropertyImage).filter(
            PropertyImage.property_id == property_id,
            PropertyImage.id != image_id
        ).first()
        
        if other_image:
            other_image.is_primary = True
            property.image_url = other_image.image_url
        else:
            property.image_url = None
    
    # 删除图片记录
    db.delete(image)
    db.commit()
    
    return None

# 添加一个端点来设置主图
@router.put("/{property_id}/images/{image_id}/primary", response_model=dict)
async def set_primary_image(
    property_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set certain image to be primary images"""
    # 验证用户是否为房东
    if current_user.user_type != "landlord":
        raise HTTPException(status_code=403, detail="Only landlord can set primary image")
    
    # 验证房产是否存在且属于当前房东
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not exists")
    
    landlord_profile = current_user.landlord_profile
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="Not authorize to set property primary images")
    
    # 找到要设置为主图的图片
    new_primary = db.query(PropertyImage).filter(
        PropertyImage.id == image_id,
        PropertyImage.property_id == property_id
    ).first()
    
    if not new_primary:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not exists")
    
    # 将当前的主图设置为非主图
    current_primary = db.query(PropertyImage).filter(
        PropertyImage.property_id == property_id,
        PropertyImage.is_primary == True
    ).first()
    
    if current_primary:
        current_primary.is_primary = False
    
    # 设置新的主图
    new_primary.is_primary = True
    property.image_url = new_primary.image_url
    
    db.commit()
    
    return {
        "status": "success",
        "message": "primary image set successfully",
        "image": {
            "id": new_primary.id,
            "image_url": new_primary.image_url,
            "is_primary": True
        }
    }