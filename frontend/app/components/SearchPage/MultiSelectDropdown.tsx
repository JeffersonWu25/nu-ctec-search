'use client';

import { useState, useRef, useEffect } from 'react';

interface Option {
  id: string;
  label: string;
}

interface MultiSelectDropdownProps {
  label: string;
  placeholder: string;
  options: Option[];
  selectedOptions: Option[];
  onSelectionChange: (selected: Option[]) => void;
  maxResults?: number;
}

export default function MultiSelectDropdown({
  label,
  placeholder,
  options,
  selectedOptions,
  onSelectionChange,
  maxResults = 4
}: MultiSelectDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredOptions = options
    .filter(option => 
      !selectedOptions.some(selected => selected.id === option.id) &&
      option.label.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .slice(0, maxResults);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
        setFocusedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (value: string) => {
    setSearchTerm(value);
    setIsOpen(true);
    setFocusedIndex(-1);
  };

  const handleOptionSelect = (option: Option) => {
    onSelectionChange([...selectedOptions, option]);
    setSearchTerm('');
    setFocusedIndex(-1);
    inputRef.current?.focus();
  };

  const handleRemoveOption = (optionToRemove: Option) => {
    onSelectionChange(selectedOptions.filter(option => option.id !== optionToRemove.id));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusedIndex(prev => (prev + 1) % filteredOptions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocusedIndex(prev => prev <= 0 ? filteredOptions.length - 1 : prev - 1);
    } else if (e.key === 'Enter' && focusedIndex >= 0) {
      e.preventDefault();
      handleOptionSelect(filteredOptions[focusedIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setSearchTerm('');
      setFocusedIndex(-1);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
      
      <div className="min-h-[42px] w-full px-3 py-2 border border-gray-300 rounded-md focus-within:ring-2 focus-within:ring-purple-500 focus-within:border-transparent bg-white">
        <div className="flex flex-wrap gap-1 items-center">
          {selectedOptions.map((option) => (
            <span
              key={option.id}
              className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded-md"
            >
              {option.label}
              <button
                type="button"
                onClick={() => handleRemoveOption(option)}
                className="text-purple-600 hover:text-purple-800 ml-1"
                aria-label={`Remove ${option.label}`}
              >
                ×
              </button>
            </span>
          ))}
          
          <input
            ref={inputRef}
            type="text"
            value={searchTerm}
            onChange={(e) => handleInputChange(e.target.value)}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            placeholder={selectedOptions.length === 0 ? placeholder : ''}
            className="flex-1 min-w-[120px] outline-none text-sm"
          />
        </div>
      </div>

      {isOpen && filteredOptions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
          {filteredOptions.map((option, index) => (
            <button
              key={option.id}
              type="button"
              className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-50 focus:bg-gray-50 ${
                index === focusedIndex ? 'bg-purple-50 text-purple-900' : 'text-gray-900'
              }`}
              onClick={() => handleOptionSelect(option)}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}