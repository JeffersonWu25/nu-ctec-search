export interface Option {
  id: string;
  label: string;
  searchTerms?: string; // Additional terms to match against (e.g., department name)
}

export interface SearchFilters {
  subjects: Option[];
  courses: Option[];
  instructors: Option[];
  requirements: Option[];
  sortBy: string;
}

export const initialFilters: SearchFilters = {
  subjects: [],
  courses: [],
  instructors: [],
  requirements: [],
  sortBy: 'Recency'
};

export type FilterKey = keyof Omit<SearchFilters, 'sortBy'>;