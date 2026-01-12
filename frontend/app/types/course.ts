export interface Course {
  id: string;
  courseCode: string;
  courseName: string;
  instructor: string;
  term: string;
  overallRating: number;
  workloadRating: number;
  teachingRating: number;
}

export interface CourseOffering {
  id: string;
  course: {
    id: string;
    code: string;
    title: string;
    description?: string | null;
    prerequisitesText?: string | null;
    department?: {
      id: string;
      code: string;
      name: string;
    } | null;
  };
  instructor: {
    id: string;
    name: string;
    profile_photo?: string | null;
  };
  quarter: 'Fall' | 'Winter' | 'Spring' | 'Summer';
  year: number;
  section: number;
  audienceSize: number;
  responseCount: number;
  ratings: Rating[];
  comments: Comment[];
  requirements: Requirement[];
  aiSummary?: string | null;
}

export interface Rating {
  id: string;
  surveyQuestion: {
    id: string;
    question: string;
  };
  distribution: RatingDistribution[];
  mean: number;
  responseCount: number;
}

export interface RatingDistribution {
  ratingValue: number;
  label?: string;
  count: number;
  percentage: number;
}

export interface Comment {
  id: string;
  content: string;
}

export interface Requirement {
  id: string;
  name: string;
}