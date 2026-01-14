export function buildAskAIUserPrompt(question: string, context: string): string {
  return `
    You are answering a question about a university course using ONLY the provided student comments.
    Give a concise, specific answer (2–3 sentences) that directly addresses the question.
    Ground each claim in concrete details from the comments (e.g., workload, exams, projects, pacing), and quote short phrases when helpful.
    If the comments do not contain enough relevant evidence, explicitly say so.
    Do not infer, generalize, or add information not present in the comments.

    Question: ${question}

    Student Comments:
    ${context}

    Answer the question:
  `;
}
