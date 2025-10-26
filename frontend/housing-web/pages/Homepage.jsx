import React, { useState, useEffect } from "react";
import { hybridSearchProperties } from "../src/api";

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
    // Get the first image URL or use a placeholder
    const imageUrl = property.images && property.images.length > 0
        ? property.images[0].url
        : "https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80";

    return (
        <div className="property-card">
            <div className="property-image-container">
                <img src={imageUrl} alt={property.title} />
                <div className="property-price-tag">
                    ${property.price} / {property.bedrooms}b {property.bathrooms}b
                </div>
            </div>
            <div className="property-info">
                <h3>{property.title}</h3>
                <p className="property-address">{property.address}, {property.city}</p>
                <p className="property-description">{property.description}</p>
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

    // search and property state
    const [searchQuery, setSearchQuery] = useState('');
    const [properties, setProperties] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Handle search
    const handleSearch = async () => {
        if (!searchQuery.trim()) {
            setError('Please enter a search term');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const results = await hybridSearchProperties(searchQuery, 20);
            setProperties(results);
            if (results.length === 0) {
                setError('No properties found');
            }
        } catch (err) {
            console.error('Search error:', err);
            setError('Failed to search properties. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    // Handle Enter key in search input
    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    // Load default properties on mount
    useEffect(() => {
        const loadDefaultProperties = async () => {
            setLoading(true);
            try {
                // Search for "apartment" by default to show some results
                const results = await hybridSearchProperties('apartment', 20);
                setProperties(results);
            } catch (err) {
                console.error('Error loading properties:', err);
                setError('Failed to load properties');
            } finally {
                setLoading(false);
            }
        };

        loadDefaultProperties();
    }, []);

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
                    <input
                        type="text"
                        placeholder="Search properties..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyPress={handleKeyPress}
                    />
                    <button className="search-button" onClick={handleSearch}>
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
                {loading && (
                    <div className="text-center py-8">
                        <p>Loading properties...</p>
                    </div>
                )}

                {error && !loading && (
                    <div className="text-center py-8 text-red-600">
                        <p>{error}</p>
                    </div>
                )}

                {!loading && !error && properties.length === 0 && (
                    <div className="text-center py-8">
                        <p>No properties found. Try a different search term.</p>
                    </div>
                )}

                {!loading && properties.length > 0 && properties.map(property =>
                    <PropertyCard key={property.id} property={property} />
                )}
            </div>
        </div>
    );
};

export default HomePage;