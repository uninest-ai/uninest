# HorizonHome: AI-Powered Architectural Analysis & Recommendation System

> **Project Highlight**: This project bridges architectural knowledge with advanced AI techniques to deliver intelligent floor plan analysis, architectural style classification, and ML-ready data pipelines, demonstrating expertise at the intersection of architecture and emerging AI.

![Architecture AI Banner](https://placehold.co/800x200?text=Architecture+%2B+AI)

## 🏗️ Project Overview

HorizonHome is an innovative housing recommendation platform enhanced with architectural intelligence capabilities. It demonstrates how AI can transform residential construction through intelligent spatial analysis, style classification, and data-driven decision making.

### Core Architectural AI Features

1. **Intelligent Floor Plan Analysis**
   - Comprehensive spatial efficiency scoring and optimization
   - Room function identification and relationship mapping
   - Traffic flow pattern analysis for improved circulation
   - Natural light optimization recommendations
   - Construction cost impact assessment

2. **Architectural Style Classification Engine**
   - Multi-style recognition (Modern, Contemporary, Craftsman, etc.)
   - Material identification with sustainability ratings
   - Style comparison and compatibility analysis
   - Historical context and construction period estimation

3. **ML-Ready Architectural Data Pipeline**
   - Structured annotation system for floor plans
   - Feature vector generation for architectural elements
   - Data quality auditing and validation workflows
   - Preference extraction for personalized recommendations

## 🔍 Technical Implementation

### Floor Plan Analysis Service

```python
class FloorPlanAnalysisService:
    """Service for analyzing floor plan images using AI"""
    
    def analyze_floor_plan(self, image_bytes: bytes) -> Dict[str, Any]:
        """Analyze a floor plan image to extract key architectural information"""
        # Implementation details...
        
    def generate_optimization_suggestions(self, floor_plan_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate architectural optimization suggestions based on floor plan analysis"""
        # Implementation details...
        
    def analyze_construction_materials(self, image_bytes: bytes) -> Dict[str, Any]:
        """Analyze construction materials visible in property images"""
        # Implementation details...
```

The floor plan analysis service leverages computer vision models to understand spatial relationships, identify rooms and circulation paths, and evaluate design efficiency. It demonstrates both architectural spatial reasoning and AI implementation capabilities.

### Architectural Style Classifier

```python
class ArchitecturalStyleClassifier:
    """Service for analyzing and classifying architectural styles in property images"""
    
    def classify_architectural_style(self, image_bytes: bytes) -> Dict[str, Any]:
        """Classify the architectural style of a building in an image"""
        # Implementation details...
        
    def compare_architectural_styles(self, image_bytes1: bytes, image_bytes2: bytes) -> Dict[str, Any]:
        """Compare architectural styles between two buildings"""
        # Implementation details...
        
    def generate_style_guidelines(self, style_name: str) -> Dict[str, Any]:
        """Generate detailed architectural style guidelines"""
        # Implementation details...
```

This service demonstrates understanding of architectural aesthetics, historical styles, and their defining characteristics. It showcases the ability to encode complex architectural knowledge into machine-understandable models.

### ML Data Pipeline Service

```python
class MLDataPipelineService:
    """Service for preparing architectural data for machine learning pipelines"""
    
    def extract_property_features_dataset(self) -> pd.DataFrame:
        """Extract property features for ML model training"""
        # Implementation details...
    
    def prepare_floor_plan_training_data(self, labeled_data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, str]:
        """Prepare floor plan annotations for ML model training"""
        # Implementation details...
    
    def generate_architectural_feature_vectors(self) -> np.ndarray:
        """Generate feature vectors for architectural style classification"""
        # Implementation details...
    
    def audit_training_data(self) -> Dict[str, Any]:
        """Audit training data for quality and completeness"""
        # Implementation details...
```

This service showcases expertise in preparing architectural data for machine learning applications, including annotation workflows, feature engineering, and data quality control - essential skills for bridging architectural design and ML systems.

## 🚀 API Implementation

### Floor Plan Analysis Endpoints

```python
@router.post("/floor-plans/analyze", response_model=Dict[str, Any])
async def analyze_floor_plan(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze a floor plan image to extract architectural features"""
    # Process floor plan image and return detailed analysis
```

### Architectural Style Analysis Endpoints

```python
@router.post("/architectural-styles/classify", response_model=Dict[str, Any])
async def classify_architectural_style(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Classify the architectural style of a building in an image"""
    # Process building image and return style classification
```

### ML Data Pipeline Endpoints

```python
@router.post("/ml-pipeline/prepare-floor-plan-data", response_model=Dict[str, Any])
def prepare_floor_plan_data(
    labeled_data: List[Dict[str, Any]] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Prepare floor plan annotations for ML model training"""
    # Process annotations and prepare ML-ready datasets
```

## 📊 System Architecture

The system follows a modular architecture that separates concerns while maintaining cohesive architectural intelligence capabilities:

```
HorizonHome/
├── API Layer
│   ├── Property APIs
│   ├── User Management APIs
│   ├── Architectural Analysis APIs 
│   └── ML Data Pipeline APIs
├── Service Layer
│   ├── Recommendation Services
│   ├── Authentication Services
│   ├── Floor Plan Analysis Service
│   ├── Architectural Style Classification Service
│   └── ML Data Pipeline Service
└── Data Layer
    ├── User Data
    ├── Property Data
    ├── Interaction Data
    └── Architectural Feature Data
```

## 💡 Real-World Applications

### For Residential Construction

- **Design Optimization**: AI-assisted layout refinement for improved efficiency
- **Material Selection**: Data-driven material recommendations with sustainability metrics
- **Cost Analysis**: Identifying design factors impacting construction costs
- **Style Consistency**: Ensuring architectural coherence across developments

### For Architectural Data Processing

- **Annotation Systems**: Structured approach to labeling architectural elements
- **ML Training Data**: Preparation of high-quality datasets for model training
- **Quality Assurance**: Auditing workflows for architectural data integrity
- **Feature Engineering**: Transforming architectural knowledge into machine-readable features

## 🔄 Sample Response: Floor Plan Analysis

```json
{
  "status": "success",
  "analysis": {
    "total_square_footage": "Approximately 1,450 sq ft",
    "rooms": [
      {"type": "Bedroom", "count": 3},
      {"type": "Bathroom", "count": 2},
      {"type": "Kitchen", "count": 1},
      {"type": "Living Room", "count": 1}
    ],
    "layout_efficiency_score": 8.2,
    "spatial_relationships": "Good separation between private and public spaces",
    "traffic_flow_patterns": "Clear circulation paths with minimal corridor waste",
    "natural_light_optimization": "Southern exposure maximized for main living areas",
    "construction_challenges": "Complex roof junction may increase costs"
  },
  "optimization_suggestions": [
    {
      "description": "Reconfigure bathroom plumbing layout to reduce material costs",
      "difficulty": 3,
      "potential_impact": 4,
      "cost_impact": "-4.5%"
    }
  ]
}
```

## 🔄 Sample Response: Architectural Style Classification

```json
{
  "status": "success",
  "classification": {
    "primary_architectural_style": "Mid-Century Modern",
    "confidence_score": 0.92,
    "secondary_influences": ["Contemporary"],
    "key_architectural_features": [
      "Flat planes",
      "Large glass windows",
      "Changes in elevation",
      "Integration with nature"
    ],
    "primary_building_materials": [
      "Wood",
      "Glass",
      "Steel"
    ],
    "distinctive_elements": "Cantilevered overhangs with minimal supports",
    "approximate_construction_period": "1950s-1960s",
    "design_efficiency_observations": "Excellent natural light utilization"
  }
}
```

## Recommendation logic:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────►│  Auth Service   │────►│  User Profile   │
│   & Request     │     │  Verification   │     │  Retrieval      │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  User/Property  │     │ User Preference │     │  Tenant/Landlord│
│    Database     │◄───►│    Extraction   │◄────│  Profile Check  │
└────────┬────────┘     └────────┬────────┘     └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Score Calculator│     │Feature Matching │     │ Property/User   │
│ PROPERTY:       │     │ROOMMATE:        │     │   Collection    │
│ • Budget (30%)  │────►│ • Budget (30%)  │────►│                 │
│ • Location (30%)│     │ • Location (30%)│     │                 │
│ • Type (20%)    │     │ • Lifestyle(40%)│     │                 │
│ • Bed/Bath (20%)│     │                 │     │                 │
└────────┬────────┘     └─────────────────┘     └────────┬────────┘
        │                                                │
        └────────────────────┬───────────────────────────┘
                             │
                             ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Sort Results   │     │ Top-N Selection │     │   API Response  │
│  by Score       │────►│ (Limit Filter)  │────►│   Formatting    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🔧 Technical Skills Demonstrated

- **Architectural Data Structure Understanding**: Implementation of specialized data structures for floor plans, spatial relationships, and style characteristics
- **Spatial Semantic Modeling**: Encoding spatial relationships and architectural meaning into computational models
- **Annotation Systems & Pipelines**: Development of structured annotation workflows for architectural data
- **AI/ML Method Proficiency**: Application of computer vision, classification algorithms, and recommendation systems to architectural problems
- **Software System Construction**: Development of a complete API-based system with modular architecture and clean separation of concerns

## 🔮 Future Enhancements

- 3D model generation from 2D floor plans
- Building code compliance checking
- Energy efficiency simulation and optimization
- Regional style adaptation recommendations
