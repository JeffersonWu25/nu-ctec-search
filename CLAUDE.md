# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Here is the context on this project. I am building a course review search and course discovery tool for Northwestern students. Northwestern has CTECs which are surveys sent to students for every course that they have ever offered. All the CTECs ask the same questions and are formatted basically the same. I extract all the information from the CTECs and store it into a relational database. I also store the comments into a vector database. The key features of the tool is 1. allowing northwestern students to easily search and filter through course reviews 2. they can discover by searching using natural language like “I want to find an easy class that teaches PyTorch” and I would have a RAG model with all the student comments and course descriptions so that I can recommend them a class based on their query. The CTECs look like this:

## Architecture

### Frontend Structure
- **Next.js 16** with TypeScript and Tailwind CSS
- **App Router** architecture with components organized by feature
- **Component Organization**:
  - `app/components` - where all components go
  - `app/hooks/` - Custom React hooks
  - `app/types/` - TypeScript interfaces

### Database Architecture

Held in schema.sql

## Data Reference
Sample CTEC artifacts are provided in docs/samples/.
These represent the canonical structure of CTEC surveys.
Use them to reason about parsing, schema design, and attribution logic. Read 1 or 2 of these.

## Development Commands

All development commands should be run from the `frontend/` directory:

```bash
# Development server
npm run dev

# Build for production  
npm run build

# Start production server
npm run start

# Lint code
npm run lint
```

## Code Quality Standard
Write code as a senior software engineer would for a production, industry-grade system.

This means:
- Correctness over cleverness
- Explicit error handling
- Clear naming and small functions
- Minimal diffs and no unnecessary refactors
- Separation of concerns
- Code that is easy for another engineer to read, test, and extend

If a change feels ambiguous or architectural, ask before implementing.
