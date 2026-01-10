"""
Centralized AI prompts for summary generation.

All prompts are defined here for easy modification and consistency.
"""

# Course Offering Summary Prompt
COURSE_OFFERING_PROMPT = """You are analyzing student feedback for a specific course offering to create a comprehensive summary.

Your task: Create a 2-3 paragraph summary of this course offering based on the student comments provided.

Your summary should cover:
1. Overall student sentiment and satisfaction level
2. Specific strengths mentioned by students (teaching quality, course content, assignments, etc.)
3. Areas for improvement or common concerns raised by students
4. Notable themes or patterns in the feedback

Guidelines:
- Be objective and factual
- Only include information that is directly supported by the comments
- Do not make assumptions or add information not present in the feedback
- If there are too few comments to draw meaningful conclusions, state this clearly
- Use specific examples from comments when possible
- Maintain a neutral, analytical tone

Student Comments:
{comments_text}

Summary:"""

# Instructor Summary Prompt
INSTRUCTOR_SUMMARY_PROMPT = """You are analyzing student feedback for an instructor across multiple course offerings to create a concise teaching profile.

Your task: Create a 2-3 paragraph summary (maximum 1400 characters) of this instructor's teaching effectiveness based on student comments from various courses they have taught.

Your summary should cover:
1. Overall teaching effectiveness and student satisfaction patterns
2. Key strengths mentioned consistently across courses
3. Main areas for improvement or common concerns
4. Notable teaching style characteristics

Guidelines:
- Be concise and focus only on the most important patterns
- Focus on patterns that appear across multiple course offerings
- Be objective and evidence-based - only include what is supported by the comments
- Do not hallucinate or assume information not present in the feedback
- Keep under 1400 characters total
- Use clear, direct language

Student Comments by Course Offering:
{comments_text}

Summary:"""

# Course Summary Prompt  
COURSE_SUMMARY_PROMPT = """You are analyzing summaries from different course offerings to create an overall course profile.

Your task: Create a 2-3 paragraph summary of this course based on summaries from different course offerings taught by various instructors over multiple terms.

Your summary should cover:
1. Overall course quality and student satisfaction patterns across different offerings
2. Common strengths of the course content and structure across instructors/terms
3. Consistent challenges or areas for improvement mentioned across offerings
4. How the course experience varies by instructor, term, or other factors (if applicable)

Guidelines:
- Focus on patterns that emerge across different course offerings and instructors
- Be objective and evidence-based - only include what is supported by the offering summaries
- Do not add information not present in the provided summaries
- Identify both consistent positive and negative aspects of the course
- Note any significant variations in course quality or student experience
- Maintain an analytical, neutral tone

Course Offering Summaries:
{summaries_text}

Summary:"""

# System prompts for different summary types
SYSTEM_PROMPTS = {
    'course_offering': "You are an expert educational analyst specializing in course evaluation and student feedback analysis.",
    'instructor': "You are an expert educational analyst specializing in teaching effectiveness evaluation and instructor assessment.",
    'course': "You are an expert educational analyst specializing in curriculum evaluation and course quality assessment."
}

def get_prompt(entity_type: str, content: str) -> tuple[str, str]:
    """
    Get the appropriate system and user prompts for a given entity type.
    
    Args:
        entity_type: Type of entity ('course_offering', 'instructor', 'course')
        content: The content to be analyzed (comments or summaries)
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    prompts = {
        'course_offering': COURSE_OFFERING_PROMPT.format(comments_text=content),
        'instructor': INSTRUCTOR_SUMMARY_PROMPT.format(comments_text=content),
        'course': COURSE_SUMMARY_PROMPT.format(summaries_text=content)
    }
    
    system_prompt = SYSTEM_PROMPTS.get(entity_type, SYSTEM_PROMPTS['course_offering'])
    user_prompt = prompts.get(entity_type, prompts['course_offering'])
    
    return system_prompt, user_prompt