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

Here is the full SQL of my Supabase database:

```
-- ============================================================
-- CTEC Search — Full Supabase/Postgres Schema (Canonical)
-- Includes: departments + course descriptions + prerequisites_text
-- Includes: RAG tables + AI summaries (incremental refresh support)
-- ============================================================

-- ============================================================
-- 0) Extensions
-- ============================================================

create extension if not exists pgcrypto;
create extension if not exists vector;

-- ============================================================
-- 1) Enums
-- ============================================================

do $$
begin
  if not exists (select 1 from pg_type where typname = 'quarter_enum') then
    create type quarter_enum as enum ('Fall', 'Winter', 'Spring', 'Summer');
  end if;
end$$;

do $$
begin
  if not exists (select 1 from pg_type where typname = 'entity_type_enum') then
    create type entity_type_enum as enum ('course', 'instructor', 'course_offering', 'requirement');
  end if;
end$$;

-- ============================================================
-- 2) Core tables (Departments + Courses + Instructors + Requirements)
-- ============================================================

create table if not exists departments (
  id uuid primary key default gen_random_uuid(),
  code text not null,          -- e.g., "COMP_SCI", "MATH", "ECON"
  name text not null,          -- e.g., "Computer Science"
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint departments_code_unique unique (code)
);

create index if not exists idx_departments_name
  on departments(name);

create table if not exists courses (
  id uuid primary key default gen_random_uuid(),

  code varchar not null,       -- e.g., "COMP_SCI 214"
  title text not null,

  -- Catalog additions
  department_id uuid references departments(id) on delete set null,
  description text,
  prerequisites_text text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_courses_code_unique
  on courses(code);

create index if not exists idx_courses_department_id
  on courses(department_id);

create table if not exists instructors (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  profile_photo text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_instructors_name
  on instructors(name);

create table if not exists requirements (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_requirements_name_unique
  on requirements(name);

create table if not exists survey_questions (
  id uuid primary key default gen_random_uuid(),
  question text not null,
  created_at timestamptz not null default now()
);

create unique index if not exists idx_survey_questions_question_unique
  on survey_questions(question);

-- ============================================================
-- 3) Course offerings + requirements
-- ============================================================

create table if not exists course_offerings (
  id uuid primary key default gen_random_uuid(),

  course_id uuid not null references courses(id) on delete cascade,
  instructor_id uuid not null references instructors(id) on delete cascade,

  quarter quarter_enum not null,
  year int not null,
  section int,

  audience_size int,
  response_count int,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  -- Prevent duplicate uploads for the same offering
  constraint course_offering_unique
    unique (course_id, instructor_id, quarter, year, section),

  -- Basic sanity checks to catch broken parses early
  constraint course_offerings_year_check
    check (year >= 1900 and year <= 2100),

  constraint course_offerings_counts_check
    check (
      (audience_size is null or audience_size >= 0)
      and (response_count is null or response_count >= 0)
      and (audience_size is null or response_count is null or response_count <= audience_size)
    )
);

create index if not exists idx_course_offerings_course_id
  on course_offerings(course_id);

create index if not exists idx_course_offerings_instructor_id
  on course_offerings(instructor_id);

create index if not exists idx_course_offerings_term
  on course_offerings(year, quarter);

create table if not exists course_requirements (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references courses(id) on delete cascade,
  requirement_id uuid not null references requirements(id) on delete cascade,
  created_at timestamptz not null default now(),
  constraint course_requirement_unique unique (course_id, requirement_id)
);

-- ============================================================
-- 4) Comments
-- ============================================================

create table if not exists comments (
  id uuid primary key default gen_random_uuid(),
  course_offering_id uuid not null references course_offerings(id) on delete cascade,
  content text not null,
  content_hash text, -- used for idempotent inserts
  created_at timestamptz not null default now()
);

create index if not exists idx_comments_offering_id
  on comments(course_offering_id);

-- Prevent duplicate comments per offering (hash-based)
-- Note: multiple NULL hashes are allowed; your loader should always set content_hash.
create unique index if not exists comments_unique_per_offering
  on comments (course_offering_id, content_hash);

-- ============================================================
-- 5) Ratings (question-level)
-- ============================================================

create table if not exists ratings (
  id uuid primary key default gen_random_uuid(),
  course_offering_id uuid not null references course_offerings(id) on delete cascade,
  survey_question_id uuid not null references survey_questions(id) on delete cascade,
  created_at timestamptz not null default now(),
  constraint rating_unique unique (course_offering_id, survey_question_id)
);

create index if not exists idx_ratings_offering_id
  on ratings(course_offering_id);

create index if not exists idx_ratings_question_id
  on ratings(survey_question_id);

-- ============================================================
-- 6) Survey question options
-- ============================================================

create table if not exists survey_question_options (
  id uuid primary key default gen_random_uuid(),
  survey_question_id uuid not null references survey_questions(id) on delete cascade,

  label text not null,       -- "3 or fewer", "4 - 7", "1", "2", ...
  ordinal int not null,      -- display order

  numeric_value int,         -- for Likert questions (1..6)
  min_value int,             -- for bins
  max_value int,
  is_open_ended_max boolean not null default false,

  created_at timestamptz not null default now(),

  constraint sqo_unique_ordinal unique (survey_question_id, ordinal),
  constraint sqo_unique_label unique (survey_question_id, label)
);

create index if not exists idx_sqo_question_id
  on survey_question_options(survey_question_id);

create index if not exists idx_sqo_question_ordinal
  on survey_question_options(survey_question_id, ordinal);

-- ============================================================
-- 7) Rating distributions (option-based)
-- ============================================================

create table if not exists ratings_distribution (
  id bigint generated always as identity primary key,

  rating_id uuid not null references ratings(id) on delete cascade,
  option_id uuid not null references survey_question_options(id) on delete cascade,

  count bigint not null check (count >= 0),
  created_at timestamptz not null default now(),

  constraint rating_distribution_unique unique (rating_id, option_id)
);

create index if not exists idx_ratings_distribution_rating_id
  on ratings_distribution(rating_id);

create index if not exists idx_ratings_distribution_option_id
  on ratings_distribution(option_id);

-- ============================================================
-- 8) RAG: comment chunks + embeddings
-- ============================================================

create table if not exists comment_chunks (
  id uuid primary key default gen_random_uuid(),
  comment_id uuid not null references comments(id) on delete cascade,
  course_offering_id uuid not null references course_offerings(id) on delete cascade,
  chunk_index int not null default 0,
  content text not null,
  created_at timestamptz not null default now(),
  constraint comment_chunk_unique unique (comment_id, chunk_index)
);

create index if not exists idx_comment_chunks_comment_id
  on comment_chunks(comment_id);

create index if not exists idx_comment_chunks_offering_id
  on comment_chunks(course_offering_id);

create table if not exists embeddings (
  chunk_id uuid primary key references comment_chunks(id) on delete cascade,
  embedding vector(1536) not null,
  model text not null,
  embedded_at timestamptz not null default now()
);

create index if not exists idx_embeddings_vector_ivfflat
on embeddings
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

analyze embeddings;

-- ============================================================
-- 9) AI summaries (with incremental refresh support)
-- ============================================================

create table if not exists ai_summaries (
  id uuid primary key default gen_random_uuid(),
  entity_type entity_type_enum not null,
  entity_id uuid not null,

  -- NEW: allow multiple summary "kinds" per entity (e.g., default, short, detailed)
  summary_type text not null default 'default',

  summary text not null,
  model text not null,
  prompt text,

  -- Metadata for debugging + staleness detection
  source_count bigint,              -- legacy / optional (e.g., # items summarized)
  source_hash text,                 -- legacy / optional
  source_updated_at timestamptz,     -- NEW: watermark of newest underlying data used
  source_comment_count bigint,       -- NEW: how many comments were used (if applicable)

  generated_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Replace old unique(entity_type, entity_id) with unique(entity_type, entity_id, summary_type)
do $$
begin
  if exists (
    select 1
    from pg_constraint
    where conname = 'ai_summary_unique'
  ) then
    alter table ai_summaries drop constraint ai_summary_unique;
  end if;
end$$;

alter table ai_summaries
  add constraint ai_summary_unique_v2 unique (entity_type, entity_id, summary_type);

create index if not exists idx_ai_summaries_entity
  on ai_summaries(entity_type, entity_id);

create index if not exists idx_ai_summaries_lookup
  on ai_summaries(entity_type, entity_id, summary_type);

create index if not exists idx_ai_summaries_source_updated_at
  on ai_summaries(entity_type, source_updated_at);

-- Optional backfill for existing rows (safe defaults)
update ai_summaries
set
  source_updated_at = coalesce(source_updated_at, generated_at),
  updated_at = coalesce(updated_at, generated_at)
where source_updated_at is null or updated_at is null;
```

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
