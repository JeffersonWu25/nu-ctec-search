'use client';

import { useSearchFilters } from '../../hooks/useSearchFilters';
import { Option } from '../../types/filters';
import MultiSelectDropdown from './MultiSelectDropdown';

const ACADEMIC_SUBJECTS: Option[] = [
  { id: 'comp-sci', label: 'COMP_SCI' },
  { id: 'math', label: 'MATH' },
  { id: 'eecs', label: 'EECS' },
  { id: 'stat', label: 'STAT' },
  { id: 'chem', label: 'CHEM' },
  { id: 'phys', label: 'PHYS' },
  { id: 'bio', label: 'BIOL_SCI' },
  { id: 'psych', label: 'PSYCH' },
  { id: 'econ', label: 'ECON' },
  { id: 'hist', label: 'HISTORY' },
];

const COURSES: Option[] = [
  { id: 'comp-111', label: 'COMP_SCI 111' },
  { id: 'comp-211', label: 'COMP_SCI 211' },
  { id: 'comp-214', label: 'COMP_SCI 214' },
  { id: 'comp-321', label: 'COMP_SCI 321' },
  { id: 'math-230', label: 'MATH 230' },
  { id: 'math-240', label: 'MATH 240' },
  { id: 'stat-202', label: 'STAT 202' },
  { id: 'eecs-111', label: 'EECS 111' },
  { id: 'eecs-211', label: 'EECS 211' },
  { id: 'chem-171', label: 'CHEM 171' },
];

const INSTRUCTORS: Option[] = [
  { id: 'shruti-barg', label: 'Shruti Barg' },
  { id: 'vincent-st-amour', label: 'Vincent St-Amour' },
  { id: 'john-doe', label: 'John Doe' },
  { id: 'jane-smith', label: 'Jane Smith' },
  { id: 'michael-johnson', label: 'Michael Johnson' },
  { id: 'sarah-wilson', label: 'Sarah Wilson' },
  { id: 'david-brown', label: 'David Brown' },
  { id: 'emily-davis', label: 'Emily Davis' },
];

const COURSE_REQUIREMENTS: Option[] = [
  { id: 'cs-core', label: 'CS Core' },
  { id: 'math-req', label: 'Math Requirement' },
  { id: 'science-req', label: 'Science Requirement' },
  { id: 'distro-1', label: 'Distribution 1' },
  { id: 'distro-2', label: 'Distribution 2' },
  { id: 'writing-sem', label: 'Writing Seminar' },
  { id: 'foreign-lang', label: 'Foreign Language' },
  { id: 'capstone', label: 'Capstone' },
];

const SORT_OPTIONS = [
  'Recency',
  'Overall Rating',
  'Teaching Rating',
  'Workload Rating',
  'Course Number'
];

export default function SearchFilters() {
  const { filters, updateFilter, updateSortBy, clearFilters } = useSearchFilters();

  return (
    <div className="w-80 flex-shrink-0">
      <div className="bg-white border border-gray-200 rounded-lg p-6 sticky top-24">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Filters</h2>
        
        <div className="space-y-6">
          <MultiSelectDropdown
            label="Academic Subject"
            placeholder="Select subjects..."
            options={ACADEMIC_SUBJECTS}
            selectedOptions={filters.subjects}
            onSelectionChange={(value) => updateFilter('subjects', value)}
          />

          <MultiSelectDropdown
            label="Course"
            placeholder="Select courses..."
            options={COURSES}
            selectedOptions={filters.courses}
            onSelectionChange={(value) => updateFilter('courses', value)}
          />

          <MultiSelectDropdown
            label="Instructor"
            placeholder="Select instructors..."
            options={INSTRUCTORS}
            selectedOptions={filters.instructors}
            onSelectionChange={(value) => updateFilter('instructors', value)}
          />

          <MultiSelectDropdown
            label="Course Requirements"
            placeholder="Select requirements..."
            options={COURSE_REQUIREMENTS}
            selectedOptions={filters.requirements}
            onSelectionChange={(value) => updateFilter('requirements', value)}
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sort by
            </label>
            <div className="relative">
              <select
                value={filters.sortBy}
                onChange={(e) => updateSortBy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white appearance-none text-sm"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <button
            onClick={clearFilters}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Clear all filters
          </button>
        </div>
      </div>
    </div>
  );
}