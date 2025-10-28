import React, { useState, useEffect } from "react";


// 下拉选择器组件
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

const PropertyProfile = () => {
    // 筛选器状态
    const [rentalType, setRentalType] = useState('For Rent');
    const [peopleCount, setPeopleCount] = useState('Any');
    const [propertyType, setPropertyType] = useState('Any');
    const [roomCount, setRoomCount] = useState('Any');
    
    const [property, setProperty] = useState({
        id: 1,
        name: "Albion At Morrow Park",
        price: "2800",
        bedrooms: "3",
        bathrooms: "2",
        image: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80",
        description: "Welcome to Ruth Gardens in New York, NY! Our apartments offer convenience and comfort with amenities such as a parking garage, gas and water included, on-site laundry facilities, and an intercom system for added security. Located close to shops, bus lines, and universities, Ruth Gardens is the perfect place for those looking for a convenient and hassle-free living experience. Don't miss out on the opportunity to call Ruth Gardens your new home!",
        reviews: [
            {
                id: 1,
                user: "CMUstar",
                avatar: "https://randomuser.me/api/portraits/women/44.jpg",
                rating: 2,
                comment: "It's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaa",
                date: "June 6th 2024"
            },
            {
                id: 2,
                user: "CMUstar",
                avatar: "https://randomuser.me/api/portraits/women/44.jpg",
                rating: 2,
                comment: "It's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaa",
                date: "June 6th 2024"
            },
            {
                id: 3,
                user: "CMUstar",
                avatar: "https://randomuser.me/api/portraits/women/44.jpg",
                rating: 2,
                comment: "It's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaaIt's really noisy!and aaaaaaaaaa",
                date: "June 6th 2024"
            }
        ],
        reviewCount: 288,
        averageRating: 4
    });

    const [comment, setComment] = useState("");
    const [propertyId, setPropertyId] = useState(null);

    useEffect(() => {
        // Extract property ID from URL hash
        const hash = window.location.hash;
        if (hash.startsWith('#profile/')) {
            const id = parseInt(hash.split('/')[1]);
            setPropertyId(id);
            // In a real app, you would fetch property data based on this ID
        }
    }, []);

    const handleBackClick = () => {
        window.location.hash = "#recommendation";
    };

    const handleCommentSubmit = (e) => {
        e.preventDefault();
        if (comment.trim()) {
            // Add the new comment to the reviews list
            setProperty(prevProperty => ({
                ...prevProperty,
                reviews: [
                    {
                        id: Date.now(),
                        user: "You",
                        avatar: "https://randomuser.me/api/portraits/lego/1.jpg",
                        rating: 5,
                        comment: comment,
                        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                    },
                    ...prevProperty.reviews
                ],
                reviewCount: prevProperty.reviewCount + 1
            }));
            setComment("");
        }
    };

    const renderStars = (rating) => {
        const stars = [];
        for (let i = 0; i < 5; i++) {
            if (i < rating) {
                stars.push(<span key={i} className="star-filled">★</span>);
            } else {
                stars.push(<span key={i} className="star-empty">☆</span>);
            }
        }
        return stars;
    };

    const galleryThumbnails = Array(6).fill(property.image);

    return (
        <div className="profile-container">
            <div className="profile-filters">
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
            
            <div className="profile-content">
                <div className="property-detail-section">
                    <button className="back-button" onClick={handleBackClick}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M19 12H5M12 19l-7-7 7-7"></path>
                        </svg>
                    </button>
                    
                    <div className="property-main-image">
                        <img src={property.image} alt={property.name} />
                    </div>
                    
                    <div className="property-thumbnails">
                        {galleryThumbnails.map((img, index) => (
                            <div key={index} className="thumbnail">
                                <img src={img} alt={`Thumbnail ${index + 1}`} />
                            </div>
                        ))}
                    </div>
                    
                    <div className="property-info">
                        <div className="property-price">${property.price} {property.bedrooms}b {property.bathrooms}b</div>
                        <h2 className="section-title">What's special</h2>
                        <p className="property-description">{property.description}</p>
                    </div>
                </div>
                
                <div className="property-review-section">
                    <div className="reviews-header">
                        <div className="review-count">{property.reviewCount} Reviews</div>
                        <div className="review-stars">
                            {renderStars(property.averageRating)}
                        </div>
                    </div>
                    
                    <div className="comment-form-container">
                        <form onSubmit={handleCommentSubmit}>
                            <textarea
                                className="comment-input"
                                placeholder="Add your comment..."
                                value={comment}
                                onChange={(e) => setComment(e.target.value)}
                            ></textarea>
                            <button type="submit" className="comment-submit">Post</button>
                        </form>
                    </div>
                    
                    <div className="reviews-list">
                        {property.reviews.map(review => (
                            <div key={review.id} className="review-item">
                                <div className="review-header">
                                    <div className="reviewer-info">
                                        <img src={review.avatar} alt={review.user} className="reviewer-avatar" />
                                        <div className="reviewer-name">{review.user}</div>
                                    </div>
                                    <div className="review-rating">
                                        {renderStars(review.rating)}
                                    </div>
                                </div>
                                <div className="review-comment">{review.comment}</div>
                                <div className="review-date">{review.date}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PropertyProfile;