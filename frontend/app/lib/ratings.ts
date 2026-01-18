/**
 * Shared rating calculation utilities for course and instructor aggregations.
 * Used by /api/courses/[id] and /api/instructors/[id] routes.
 */

// Question patterns to identify rating types from survey questions
export const QUESTION_PATTERNS = {
  overall: 'overall rating of the course',
  teaching: 'overall rating of the instruction',
  learning: 'how much you learned',
  challenge: 'challenging you intellectually',
  stimulating: 'stimulating your interest',
  hours: 'average number of hours per week',
} as const;

export type QuestionPatternKey = keyof typeof QUESTION_PATTERNS;

// Rating distribution types
export interface RatingDistributionOption {
  numeric_value: number | null;
  label: string | null;
  ordinal: number;
}

export interface RatingDistributionItem {
  count: number;
  option: RatingDistributionOption | null;
}

export interface OfferingRatings {
  overall: number | null;
  teaching: number | null;
  hours: string | null;
}

export interface HoursDistributionItem {
  ratingValue: number;
  label: string;
  count: number;
  percentage: number;
}

export interface AggregatedRating {
  id: string;
  surveyQuestion: { id: string; question: string };
  distribution: HoursDistributionItem[];
  mean: number;
  responseCount: number;
}

/**
 * Calculate weighted average from a rating distribution.
 * Used for Likert-scale questions (1-6 ratings).
 */
export function calculateWeightedAverage(distribution: RatingDistributionItem[]): number | null {
  let totalCount = 0;
  let weightedSum = 0;

  for (const d of distribution) {
    if (d.option?.numeric_value) {
      totalCount += d.count;
      weightedSum += d.count * d.option.numeric_value;
    }
  }

  return totalCount > 0 ? Math.round((weightedSum / totalCount) * 100) / 100 : null;
}

/**
 * Find the mode (most common label) from a distribution.
 * Used for categorical questions like hours per week.
 */
export function calculateMode(distribution: RatingDistributionItem[]): string | null {
  let maxCount = 0;
  let maxLabel: string | null = null;

  for (const d of distribution) {
    if (d.count > maxCount && d.option?.label) {
      maxCount = d.count;
      maxLabel = d.option.label;
    }
  }

  return maxLabel;
}

/**
 * Aggregate hours distribution across multiple offerings.
 * Groups by label, sums counts, and calculates percentages.
 */
export function calculateAggregatedHoursDistribution(
  distributions: RatingDistributionItem[]
): HoursDistributionItem[] {
  const labelCounts: Record<string, { count: number; ordinal: number }> = {};

  for (const d of distributions) {
    if (d.option?.label) {
      const label = d.option.label;
      if (!labelCounts[label]) {
        labelCounts[label] = { count: 0, ordinal: d.option.ordinal };
      }
      labelCounts[label].count += d.count;
    }
  }

  const totalCount = Object.values(labelCounts).reduce((sum, lc) => sum + lc.count, 0);

  return Object.entries(labelCounts)
    .sort((a, b) => a[1].ordinal - b[1].ordinal)
    .map(([label, data]) => ({
      ratingValue: 0,
      label,
      count: data.count,
      percentage: totalCount > 0 ? (data.count / totalCount) * 100 : 0,
    }));
}

/**
 * Initialize empty aggregated distributions for all question patterns.
 */
export function createEmptyAggregatedDistributions(): Record<QuestionPatternKey, RatingDistributionItem[]> {
  return {
    overall: [],
    teaching: [],
    learning: [],
    challenge: [],
    stimulating: [],
    hours: [],
  };
}

/**
 * Process a single rating and update both offering-level and aggregated distributions.
 */
export function processRating(
  question: string,
  distribution: RatingDistributionItem[],
  offeringRatings: OfferingRatings,
  aggregatedDistributions: Record<QuestionPatternKey, RatingDistributionItem[]>
): void {
  const lowerQuestion = question.toLowerCase();

  if (lowerQuestion.includes(QUESTION_PATTERNS.overall)) {
    offeringRatings.overall = calculateWeightedAverage(distribution);
    aggregatedDistributions.overall.push(...distribution);
  } else if (lowerQuestion.includes(QUESTION_PATTERNS.teaching)) {
    offeringRatings.teaching = calculateWeightedAverage(distribution);
    aggregatedDistributions.teaching.push(...distribution);
  } else if (lowerQuestion.includes(QUESTION_PATTERNS.hours)) {
    offeringRatings.hours = calculateMode(distribution);
    aggregatedDistributions.hours.push(...distribution);
  } else if (lowerQuestion.includes(QUESTION_PATTERNS.learning)) {
    aggregatedDistributions.learning.push(...distribution);
  } else if (lowerQuestion.includes(QUESTION_PATTERNS.challenge)) {
    aggregatedDistributions.challenge.push(...distribution);
  } else if (lowerQuestion.includes(QUESTION_PATTERNS.stimulating)) {
    aggregatedDistributions.stimulating.push(...distribution);
  }
}

/**
 * Build the final aggregated ratings array from accumulated distributions.
 */
export function buildAggregatedRatings(
  distributions: Record<QuestionPatternKey, RatingDistributionItem[]>
): AggregatedRating[] {
  return [
    {
      id: 'agg-teaching',
      surveyQuestion: { id: 'q-teaching', question: 'Provide an overall rating of the instruction' },
      distribution: [],
      mean: calculateWeightedAverage(distributions.teaching) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-overall',
      surveyQuestion: { id: 'q-overall', question: 'Provide an overall rating of the course' },
      distribution: [],
      mean: calculateWeightedAverage(distributions.overall) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-learning',
      surveyQuestion: { id: 'q-learning', question: 'Estimate how much you learned in the course' },
      distribution: [],
      mean: calculateWeightedAverage(distributions.learning) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-challenge',
      surveyQuestion: { id: 'q-challenge', question: 'Rate the effectiveness of the course in challenging you intellectually' },
      distribution: [],
      mean: calculateWeightedAverage(distributions.challenge) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-stimulating',
      surveyQuestion: { id: 'q-stimulating', question: 'Rate the effectiveness of the instructor in stimulating your interest in the subject' },
      distribution: [],
      mean: calculateWeightedAverage(distributions.stimulating) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-hours',
      surveyQuestion: { id: 'q-hours', question: 'Estimate the average number of hours per week you spent on this course outside of class and lab time' },
      distribution: calculateAggregatedHoursDistribution(distributions.hours),
      mean: 0,
      responseCount: 0,
    },
  ];
}

/**
 * Create initial offering ratings object.
 */
export function createEmptyOfferingRatings(): OfferingRatings {
  return { overall: null, teaching: null, hours: null };
}
