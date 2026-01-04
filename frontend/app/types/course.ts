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
  };
  instructor: {
    id: string;
    name: string;
    profilePhoto?: string;
  };
  quarter: 'Fall' | 'Winter' | 'Spring' | 'Summer';
  year: number;
  section: number;
  audienceSize: number;
  responseCount: number;
  ratings: Rating[];
  comments: Comment[];
  requirements: Requirement[];
  aiSummary?: string;
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