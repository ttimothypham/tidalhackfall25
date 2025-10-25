import React, { useState, useRef, useEffect } from 'react';
import { X, ChevronDown, Search } from 'lucide-react';

export default function MultiSelectWithSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItems, setSelectedItems] = useState([]);
  const [servingSize, setServingSize] = useState('');
  const dropdownRef = useRef(null);

  const allItems = [
    'Apple', 'Banana', 'Orange', 'Strawberry', 'Blueberry',
    'Mango', 'Pineapple', 'Watermelon', 'Grapes', 'Kiwi',
    'Peach', 'Pear', 'Cherry', 'Plum', 'Raspberry'
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

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(to bottom right, #eff6ff, #e0e7ff)', padding: '2rem' }}>
      <div style={{ maxWidth: '42rem', margin: '0 auto' }}>
        <div style={{ background: 'white', borderRadius: '0.75rem', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)', padding: '2rem' }}>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#1f2937', marginBottom: '2rem' }}>Food Selection</h1>
          
          {/* Multiselect Dropdown */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
              Select Items
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
                    <span style={{ color: '#9ca3af' }}>Choose items...</span>
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
                        placeholder="Search..."
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
              Serving Size
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="number"
                value={servingSize}
                onChange={(e) => setServingSize(e.target.value)}
                placeholder="Enter serving size"
                style={{
                  width: '100%',
                  background: 'white',
                  border: '2px solid #d1d5db',
                  borderRadius: '0.5rem',
                  padding: '0.75rem 5rem 0.75rem 1rem',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
                min="0"
                step="0.1"
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

          {/* Summary */}
          <div style={{ background: '#f9fafb', borderRadius: '0.5rem', padding: '1rem', marginTop: '1.5rem' }}>
            <h3 style={{ fontWeight: '600', color: '#1f2937', marginBottom: '0.5rem' }}>Summary</h3>
            <p style={{ fontSize: '0.875rem', color: '#4b5563' }}>
              <strong>Selected Items:</strong> {selectedItems.length > 0 ? selectedItems.join(', ') : 'None'}
            </p>
            <p style={{ fontSize: '0.875rem', color: '#4b5563', marginTop: '0.25rem' }}>
              <strong>Serving Size:</strong> {servingSize || 'Not specified'}
            </p>
          </div>


          <div></div>
        </div>
      </div>
    </div>
  );
}