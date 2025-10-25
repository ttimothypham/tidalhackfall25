import React, { useState, useRef, useEffect } from 'react';
import { X, ChevronDown, Search, Loader2 } from 'lucide-react';

export default function MultiSelectWithSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItems, setSelectedItems] = useState([]);
  const [servingSize, setServingSize] = useState('');
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const dropdownRef = useRef(null);

  const allItems = [
  // Grains & Starches
  'Rice', 'White Rice', 'Brown Rice', 'Pasta', 'Spaghetti', 'Macaroni', 
  'Noodles', 'Flour', 'All-Purpose Flour', 'Bread', 'Cornmeal', 'Oats',
  'Rolled Oats', 'Quinoa', 'Couscous', 'Barley',
  
  // Proteins
  'Beans', 'Black Beans', 'Kidney Beans', 'Pinto Beans', 'Navy Beans',
  'Lentils', 'Red Lentils', 'Green Lentils', 'Chickpeas', 'Split Peas',
  'Canned Chicken', 'Canned Tuna',
  
  // Vegetables (Canned/Shelf-Stable)
  'Tomato Sauce', 'Tomato Paste', 'Canned Tomatoes', 'Diced Tomatoes',
  'Crushed Tomatoes', 'Canned Corn', 'Canned Peas', 'Canned Green Beans',
  'Canned Carrots', 'Canned Beets', 'Canned Mushrooms',
  
  // Fresh Vegetables (Long Shelf Life)
  'Onion', 'Garlic', 'Potato', 'Sweet Potato', 'Carrot', 'Cabbage',
  'Bell Pepper', 'Celery',
  
  // Oils & Fats
  'Oil', 'Vegetable Oil', 'Olive Oil', 'Canola Oil', 'Cooking Spray',
  
  // Seasonings & Basics
  'Salt', 'Black Pepper', 'Pepper', 'Sugar', 'Brown Sugar', 'Honey',
  'Vinegar', 'White Vinegar', 'Apple Cider Vinegar', 'Soy Sauce',
  'Hot Sauce', 'Ketchup', 'Mustard',
  
  // Spices & Herbs (Dried)
  'Cumin', 'Chili Powder', 'Paprika', 'Oregano', 'Basil', 'Thyme',
  'Garlic Powder', 'Onion Powder', 'Cinnamon', 'Italian Seasoning',
  'Bay Leaves', 'Curry Powder', 'Red Pepper Flakes',
  
  // Canned Fruits
  'Canned Peaches', 'Canned Pears', 'Canned Pineapple', 'Applesauce',
  'Raisins', 'Dried Cranberries',
  
  // Baking Essentials
  'Baking Powder', 'Baking Soda', 'Vanilla Extract', 'Cornstarch',
  
  // Broths & Soups
  'Chicken Broth', 'Vegetable Broth', 'Beef Broth', 'Bouillon Cubes',
  
  // Miscellaneous
  'Rice Vinegar', 'Worcestershire Sauce', 'Molasses', 'Jam', 'Jelly',
  'Peanut Butter Alternative', 'Sunflower Seed Butter', 'Crackers'
  ];

  const filteredItems = allItems.filter(item =>
    item.toLowerCase().includes(searchTerm.toLowerCase()) &&
    !selectedItems.includes(item)
  );

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleItem = (item) => {
    setSelectedItems(prev =>
      prev.includes(item)
        ? prev.filter(i => i !== item)
        : [...prev, item]
    );
  };

  const removeItem = (item) => {
    setSelectedItems(prev => prev.filter(i => i !== item));
  };

  const generateRecipes = async () => {
    if (selectedItems.length === 0) {
      setError('Please select at least one ingredient');
      return;
    }

    setLoading(true);
    setError(null);
    setRecipes([]);

    try {
      console.log('Sending request with ingredients:', selectedItems);
      
      const response = await fetch('http://127.0.0.1:5000/api/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          selected_ingredients: selectedItems,
          serving_size: servingSize || 4
        })
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `API Error: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received data:', data);
      
      setRecipes(data.recommendations || []);
      
      if (data.recommendations && data.recommendations.length === 0) {
        setError('No recipes found with those ingredients. Try adding more common items like Rice, Beans, or Pasta!');
      }
    } catch (err) {
      console.error('Error fetching recipes:', err);
      setError(`Failed to get recipes: ${err.message}. Make sure Flask server is running on port 5000.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(to bottom right, #eff6ff, #e0e7ff)', padding: '2rem' }}>
      <div style={{ maxWidth: '56rem', margin: '0 auto' }}>
        <div style={{ background: 'white', borderRadius: '0.75rem', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)', padding: '2rem' }}>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#1f2937', marginBottom: '0.5rem' }}>
            🍲 Food Bank Recipe Finder
          </h1>
          <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
            Select your available ingredients and we'll find recipes you can make!
          </p>
          
          {/* Multiselect Dropdown */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
              Available Ingredients *
            </label>
            <div ref={dropdownRef} style={{ position: 'relative' }}>
              <div
                onClick={() => setIsOpen(!isOpen)}
                style={{
                  width: '100%',
                  background: 'white',
                  border: '2px solid #d1d5db',
                  borderRadius: '0.5rem',
                  padding: '0.75rem 1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  minHeight: '3rem',
                  boxSizing: 'border-box'
                }}
              >
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', flex: 1, overflow: 'hidden' }}>
                  {selectedItems.length === 0 ? (
                    <span style={{ color: '#9ca3af' }}>Choose ingredients...</span>
                  ) : (
                    selectedItems.map(item => (
                      <span
                        key={item}
                        style={{
                          background: '#e0e7ff',
                          color: '#4338ca',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '9999px',
                          fontSize: '0.875rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {item}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            removeItem(item);
                          }}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '0.125rem',
                            borderRadius: '9999px',
                            display: 'flex',
                            alignItems: 'center'
                          }}
                        >
                          <X size={14} />
                        </button>
                      </span>
                    ))
                  )}
                </div>
                <ChevronDown
                  size={20}
                  style={{
                    color: '#9ca3af',
                    transform: isOpen ? 'rotate(180deg)' : 'rotate(0)',
                    transition: 'transform 0.2s',
                    flexShrink: 0,
                    marginLeft: '0.5rem'
                  }}
                />
              </div>

              {isOpen && (
                <div style={{
                  position: 'absolute',
                  zIndex: 10,
                  width: '100%',
                  marginTop: '0.5rem',
                  background: 'white',
                  border: '2px solid #e5e7eb',
                  borderRadius: '0.5rem',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
                }}>
                  <div style={{ padding: '0.75rem', borderBottom: '1px solid #e5e7eb' }}>
                    <div style={{ position: 'relative' }}>
                      <Search style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af', pointerEvents: 'none' }} size={18} />
                      <input
                        type="text"
                        placeholder="Search ingredients..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{
                          width: '100%',
                          paddingLeft: '2.5rem',
                          paddingRight: '1rem',
                          paddingTop: '0.5rem',
                          paddingBottom: '0.5rem',
                          border: '1px solid #d1d5db',
                          borderRadius: '0.5rem',
                          outline: 'none',
                          boxSizing: 'border-box'
                        }}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  </div>
                  <div style={{ maxHeight: '15rem', overflowY: 'auto' }}>
                    {filteredItems.length === 0 ? (
                      <div style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>No items found</div>
                    ) : (
                      filteredItems.map(item => (
                        <div
                          key={item}
                          onClick={() => toggleItem(item)}
                          style={{
                            padding: '0.75rem 1rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between'
                          }}
                          onMouseEnter={(e) => e.currentTarget.style.background = '#eef2ff'}
                          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                        >
                          <span style={{ color: '#374151' }}>{item}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Serving Size Input */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
              Serving Size (Optional)
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="number"
                value={servingSize}
                onChange={(e) => setServingSize(e.target.value)}
                placeholder="4"
                style={{
                  width: '100%',
                  background: 'white',
                  border: '2px solid #d1d5db',
                  borderRadius: '0.5rem',
                  padding: '0.75rem 5rem 0.75rem 1rem',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
                min="1"
                step="1"
              />
              <span style={{
                position: 'absolute',
                right: '1rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#6b7280',
                pointerEvents: 'none'
              }}>
                servings
              </span>
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={generateRecipes}
            disabled={loading || selectedItems.length === 0}
            style={{
              width: '100%',
              background: selectedItems.length === 0 ? '#d1d5db' : '#4f46e5',
              color: 'white',
              padding: '0.875rem 1.5rem',
              borderRadius: '0.5rem',
              border: 'none',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: selectedItems.length === 0 ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              transition: 'background 0.2s',
              marginBottom: '1.5rem'
            }}
            onMouseEnter={(e) => {
              if (selectedItems.length > 0 && !loading) {
                e.currentTarget.style.background = '#4338ca';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedItems.length > 0) {
                e.currentTarget.style.background = '#4f46e5';
              }
            }}
          >
            {loading ? (
              <>
                <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
                Finding Recipes...
              </>
            ) : (
              '🔍 Generate Recipes'
            )}
          </button>

          {/* Error Message */}
          {error && (
            <div style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '0.5rem',
              padding: '1rem',
              marginBottom: '1.5rem',
              color: '#991b1b'
            }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Recipe Results */}
          {recipes.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1f2937', marginBottom: '1rem' }}>
                Found {recipes.length} Recipe{recipes.length !== 1 ? 's' : ''}! 🎉
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {recipes.map((recipe, index) => (
                  <div
                    key={index}
                    style={{
                      background: '#f9fafb',
                      border: '2px solid #e5e7eb',
                      borderRadius: '0.75rem',
                      padding: '1.5rem',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#4f46e5';
                      e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#e5e7eb';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.75rem' }}>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', flex: 1 }}>
                        {recipe.title}
                      </h3>
                      <span style={{
                        background: '#dcfce7',
                        color: '#166534',
                        padding: '0.25rem 0.75rem',
                        borderRadius: '9999px',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        whiteSpace: 'nowrap',
                        marginLeft: '1rem'
                      }}>
                        ✓ {recipe.match_score} match{recipe.match_score !== 1 ? 'es' : ''}
                      </span>
                    </div>
                    
                    <div style={{ marginBottom: '1rem' }}>
                      <p style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151', marginBottom: '0.5rem' }}>
                        📝 Ingredients:
                      </p>
                      <div style={{ 
                        fontSize: '0.875rem', 
                        color: '#6b7280', 
                        lineHeight: '1.5',
                        background: 'white',
                        padding: '0.75rem',
                        borderRadius: '0.5rem',
                        border: '1px solid #e5e7eb'
                      }}>
                        {recipe.ingredients}
                      </div>
                    </div>

                    <div>
                      <p style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151', marginBottom: '0.5rem' }}>
                        👨‍🍳 Directions:
                      </p>
                      <div style={{ 
                        fontSize: '0.875rem', 
                        color: '#6b7280', 
                        lineHeight: '1.6',
                        background: 'white',
                        padding: '0.75rem',
                        borderRadius: '0.5rem',
                        border: '1px solid #e5e7eb'
                      }}>
                        {recipe.directions}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary */}
          <div style={{ background: '#f9fafb', borderRadius: '0.5rem', padding: '1rem', marginTop: '1.5rem' }}>
            <h3 style={{ fontWeight: '600', color: '#1f2937', marginBottom: '0.5rem' }}>Summary</h3>
            <p style={{ fontSize: '0.875rem', color: '#4b5563' }}>
              <strong>Selected Ingredients:</strong> {selectedItems.length > 0 ? selectedItems.join(', ') : 'None'}
            </p>
            <p style={{ fontSize: '0.875rem', color: '#4b5563', marginTop: '0.25rem' }}>
              <strong>Serving Size:</strong> {servingSize || '4 (default)'}
            </p>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}