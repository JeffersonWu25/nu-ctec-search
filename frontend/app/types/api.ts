/**
 * Types for Supabase query responses.
 * These types represent the shape of data returned from nested Supabase queries,
 * eliminating the need for inline `as unknown as Type` casts throughout API routes.
 */

// Base entity types (matching database schema)
export interface DepartmentRow {
  id: string;
  code: string;
  name: string;
}

export interface CourseRow {
  id: string;
  code: string;
  title: string;
  description: string | null;
  prerequisites_text: string | null;
}

export interface InstructorRow {
  id: string;
  name: string;
  profile_photo: string | null;
}

export interface RequirementRow {
  id: string;
  name: string;
}

export interface SurveyQuestionRow {
  id: string;
  question: string;
}

// Nested query response types

/** Course with department join */
export interface CourseWithDepartment extends CourseRow {
  department: DepartmentRow | null;
}

/** Course requirement join result */
export interface CourseRequirementJoin {
  requirement: RequirementRow;
}

/** Full course query result with all relations */
export interface CourseDetailQueryResult extends CourseRow {
  department: DepartmentRow | null;
  course_requirements: CourseRequirementJoin[];
}

/** Course offering with instructor join (for instructor detail page) */
export interface OfferingWithCourse {
  id: string;
  quarter: 'Fall' | 'Winter' | 'Spring' | 'Summer';
  year: number;
  section: number | null;
  audience_size: number | null;
  response_count: number | null;
  course: {
    id: string;
    code: string;
    title: string;
  };
}

/** Course offering with instructor join (for course detail page) */
export interface OfferingWithInstructor {
  id: string;
  quarter: 'Fall' | 'Winter' | 'Spring' | 'Summer';
  year: number;
  section: number | null;
  audience_size: number | null;
  response_count: number | null;
  instructor: InstructorRow;
}

/** Rating distribution option from survey_question_options */
export interface RatingOptionRow {
  numeric_value: number | null;
  label: string | null;
  ordinal: number;
}

/** Rating distribution item */
export interface RatingDistributionRow {
  count: number;
  option: RatingOptionRow;
}

/** Full rating query result with nested relations */
export interface RatingQueryResult {
  id: string;
  course_offering_id: string;
  survey_question: SurveyQuestionRow;
  ratings_distribution: RatingDistributionRow[];
}

// API response types (what the routes return)

export interface OfferingWithRatings {
  id: string;
  quarter: string;
  year: number;
  section: number | null;
  instructorId: string;
  instructorName: string;
  overallRating: number | null;
  teachingRating: number | null;
  hoursPerWeek: string | null;
}

export interface InstructorOfferingWithRatings {
  id: string;
  courseCode: string;
  courseName: string;
  courseId: string;
  quarter: string;
  year: number;
  section: number | null;
  overallRating: number | null;
  teachingRating: number | null;
  hoursPerWeek: string | null;
}

export interface CourseDetailResponse {
  id: string;
  code: string;
  title: string;
  description: string | null;
  prerequisitesText: string | null;
  department: DepartmentRow | null;
  requirements: RequirementRow[];
  offerings: OfferingWithRatings[];
  aggregatedRatings: import('./course').Rating[];
  aiSummary: string | null;
}

export interface InstructorDetailResponse {
  id: string;
  name: string;
  profile_photo: string | null;
  offerings: InstructorOfferingWithRatings[];
  aggregatedRatings: import('./course').Rating[];
  aiSummary: string | null;
}
