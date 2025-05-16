import React, { useState, useEffect } from "react";

// dropdown filter component
const DropdownFilter = ({ title, options, selectedOption, onSelect }) => {
    const [isOpen, setIsOpen] = useState(false);
    
    const toggleDropdown = () => setIsOpen(!isOpen);
    
    const handleSelect = (option) => {
        onSelect(option);
        setIsOpen(false);
    };
    
    return (
        <div className="dropdown-filter">
            <button className="filter-button" onClick={toggleDropdown}>
                {title}: {selectedOption} ▼
            </button>
            
            {isOpen && (
                <div className="dropdown-menu">
                    {options.map((option) => (
                        <div 
                            key={option} 
                            className={`dropdown-item ${selectedOption === option ? 'selected' : ''}`}
                            onClick={() => handleSelect(option)}
                        >
                            {option}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// star rating component
const StarRating = ({ rating, reviewCount }) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    
    for (let i = 0; i < 5; i++) {
        if (i < fullStars) {
            stars.push(<span key={i}>★</span>);
        } else if (i === fullStars && hasHalfStar) {
            stars.push(<span key={i}>✮</span>);
        } else {
            stars.push(<span key={i}>☆</span>);
        }
    }
    
    return (
        <div className="property-rating">
            {stars}
            <span className="rating-count">{reviewCount}</span>
        </div>
    );
};

// property card component
const PropertyCard = ({ property }) => {
    return (
        <div className="property-card">
            <div className="property-image-container">
                <img src={property.image} alt={property.name} />
                <div className="property-price-tag">
                    ${property.price} / {property.bedrooms}b {property.bathrooms}b
                </div>
            </div>
            <div className="property-info">
                <h3>{property.name}</h3>
                <StarRating rating={property.rating} reviewCount={property.reviewCount} />
                <div className="user-review">
                    <div className="user-avatar">
                        <img src={property.userImage} alt="User" />
                    </div>
                    <p className="property-description">"{property.description}"</p>
                </div>
            </div>
        </div>
    );
};

// homepage component
const HomePage = () => {
    // filter state
    const [rentalType, setRentalType] = useState('For Rent');
    const [peopleCount, setPeopleCount] = useState('Any');
    const [propertyType, setPropertyType] = useState('Any');
    const [roomCount, setRoomCount] = useState('Any');
    
    // property data
    const [properties] = useState([
        {
            id: 1,
            name: "Albion At Morrow Park",
            price: "2800",
            bedrooms: "3",
            bathrooms: "2",
            image: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80",
            rating: 4.3,
            reviewCount: "92",
            userImage: "https://randomuser.me/api/portraits/women/44.jpg",
            description: "Fitness facilities are new, lots of bus stops downstairs."
        },
        {
            id: 2,
            name: "Albion At Morrow Park",
            price: "2800",
            bedrooms: "3",
            bathrooms: "2",
            image: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80",
            rating: 4.3,
            reviewCount: "92",
            userImage: "https://randomuser.me/api/portraits/women/44.jpg",
            description: "Fitness facilities are new, lots of bus stops downstairs."
        },
        {
            id: 3,
            name: "Albion At Morrow Park",
            price: "2800",
            bedrooms: "3",
            bathrooms: "2",
            image: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80",
            rating: 4.3,
            reviewCount: "92",
            userImage: "https://randomuser.me/api/portraits/women/44.jpg",
            description: "Fitness facilities are new, lots of bus stops downstairs."
        },
        {
            id: 4,
            name: "Albion At Morrow Park",
            price: "2800",
            bedrooms: "3",
            bathrooms: "2",
            image: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80",
            rating: 4.3,
            reviewCount: "92",
            userImage: "https://randomuser.me/api/portraits/women/44.jpg",
            description: "Fitness facilities are new, lots of bus stops downstairs."
        },
        {
            id: 5,
            name: "Albion At Morrow Park",
            price: "2800",
            bedrooms: "3",
            bathrooms: "2",
            image: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80",
            rating: 4.3,
            reviewCount: "92",
            userImage: "https://randomuser.me/api/portraits/women/44.jpg",
            description: "Fitness facilities are new, lots of bus stops downstairs."
        },
        {
            id: 6,
            name: "Albion At Morrow Park",
            price: "2800",
            bedrooms: "3",
            bathrooms: "2",
            image: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80",
            rating: 4.3,
            reviewCount: "92",
            userImage: "https://randomuser.me/api/portraits/women/44.jpg",
            description: "Fitness facilities are new, lots of bus stops downstairs."
        }
    ]);

    const navigateToLogin = () => {
        window.location.hash = "#login";
    };

    const navigate = (path) => {
        window.location.href = path;
    };

    return (
        <div className="home-container">
            <header>
                <div 
                    onClick={() => navigate("/recommendation")}
                    className="logo cursor-pointer text-2xl font-bold hover:text-gray-700 transition-colors"
                >
                    UniNest
                </div>
                <div className="search-bar">
                    <input type="text" placeholder="Search..." />
                    <button className="search-button">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                    </button>
                </div>
                <button className="profile-button" onClick={navigateToLogin}>👤</button>
            </header>
            
            <div className="filters">
                <DropdownFilter 
                    title="For Rent"
                    options={['For Rent', 'Short Term', 'Long Term']}
                    selectedOption={rentalType}
                    onSelect={setRentalType}
                />
                
                <DropdownFilter 
                    title="People"
                    options={['Any', '1+', '2+', '3+', '4+']}
                    selectedOption={peopleCount}
                    onSelect={setPeopleCount}
                />
                
                <DropdownFilter 
                    title="Type"
                    options={['Any', 'Apartment', 'House', 'Studio', 'Condo']}
                    selectedOption={propertyType}
                    onSelect={setPropertyType}
                />
                
                <DropdownFilter 
                    title="Rooms"
                    options={['Any', '1+', '2+', '3+', '4+']}
                    selectedOption={roomCount}
                    onSelect={setRoomCount}
                />
            </div>
            
            <div className="property-list">
                {properties.map(property => 
                    <PropertyCard key={property.id} property={property} />
                )}
            </div>
        </div>
    );
};

export default HomePage;