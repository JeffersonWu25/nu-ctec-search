# API Documentation

Base URL: `/api`

## Endpoints

### Departments

#### GET /api/departments

Returns all departments.

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "code": "COMP_SCI",
      "name": "Computer Science (COMP_SCI)"
    }
  ]
}
```

---

### Requirements

#### GET /api/requirements

Returns all distribution requirements.

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Formal Studies Distro Area"
    }
  ]
}
```

---

### Courses

#### GET /api/courses

Returns a paginated list of courses.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `departmentId` | string | - | Filter by department UUID |
| `limit` | number | 50 | Results per page |
| `offset` | number | 0 | Number of results to skip |

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "code": "COMP_SCI_214-0",
      "title": "Data Structures & Algorithms",
      "description": "Course description...",
      "prerequisites_text": "COMP_SCI 111 and...",
      "department": {
        "id": "uuid",
        "code": "COMP_SCI",
        "name": "Computer Science (COMP_SCI)"
      }
    }
  ],
  "count": 100
}
```

#### GET /api/courses/[id]

Returns a single course with requirements.

**Response:**
```json
{
  "data": {
    "id": "uuid",
    "code": "COMP_SCI_214-0",
    "title": "Data Structures & Algorithms",
    "description": "Course description...",
    "prerequisites_text": "COMP_SCI 111 and...",
    "department": {
      "id": "uuid",
      "code": "COMP_SCI",
      "name": "Computer Science (COMP_SCI)"
    },
    "course_requirements": [
      {
        "requirement": {
          "id": "uuid",
          "name": "Formal Studies Distro Area"
        }
      }
    ]
  }
}
```

---

### Instructors

#### GET /api/instructors

Returns a paginated list of instructors.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | string | - | Filter by name (case-insensitive) |
| `limit` | number | 50 | Results per page |
| `offset` | number | 0 | Number of results to skip |

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Connor Bain",
      "profile_photo": null
    }
  ],
  "count": 18
}
```

#### GET /api/instructors/[id]

Returns an instructor with their course offerings and AI summary.

**Response:**
```json
{
  "data": {
    "id": "uuid",
    "name": "Connor Bain",
    "profile_photo": null,
    "offerings": [
      {
        "id": "uuid",
        "quarter": "Fall",
        "year": 2023,
        "section": 2,
        "audience_size": 217,
        "response_count": 183,
        "course": {
          "id": "uuid",
          "code": "COMP_SCI_111-0",
          "title": "Fund Comp Prog"
        }
      }
    ],
    "aiSummary": "Professor Bain has demonstrated..."
  }
}
```

---

### Course Offerings

#### GET /api/course-offerings

Returns a paginated list of course offerings (a specific instance of a course taught by an instructor in a given term).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `courseId` | string | - | Filter by course UUID |
| `instructorId` | string | - | Filter by instructor UUID |
| `departmentId` | string | - | Filter by department UUID |
| `quarter` | string | - | Filter by quarter (Fall, Winter, Spring, Summer) |
| `year` | number | - | Filter by year |
| `limit` | number | 20 | Results per page |
| `offset` | number | 0 | Number of results to skip |
| `sortBy` | string | year | Sort field (year, course, instructor) |
| `sortOrder` | string | desc | Sort direction (asc, desc) |

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "quarter": "Spring",
      "year": 2025,
      "section": 1,
      "audience_size": 144,
      "response_count": 115,
      "course": {
        "id": "uuid",
        "code": "COMP_SCI_214-0",
        "title": "Data Structures & Algorithms",
        "department": {
          "id": "uuid",
          "code": "COMP_SCI",
          "name": "Computer Science (COMP_SCI)"
        }
      },
      "instructor": {
        "id": "uuid",
        "name": "Vincent St-Amour",
        "profile_photo": null
      }
    }
  ],
  "count": 30,
  "limit": 20,
  "offset": 0
}
```

#### GET /api/course-offerings/[id]

Returns full details for a course offering including ratings, comments, and AI summary.

**Response:**
```json
{
  "data": {
    "id": "uuid",
    "course": {
      "id": "uuid",
      "code": "COMP_SCI_214-0",
      "title": "Data Structures & Algorithms",
      "description": "Course description...",
      "prerequisitesText": "COMP_SCI 111 and...",
      "department": {
        "id": "uuid",
        "code": "COMP_SCI",
        "name": "Computer Science (COMP_SCI)"
      }
    },
    "instructor": {
      "id": "uuid",
      "name": "Vincent St-Amour",
      "profile_photo": null
    },
    "quarter": "Spring",
    "year": 2025,
    "section": 1,
    "audienceSize": 144,
    "responseCount": 115,
    "ratings": [
      {
        "id": "uuid",
        "surveyQuestion": {
          "id": "uuid",
          "question": "Provide an overall rating of the instruction"
        },
        "distribution": [
          { "ratingValue": 1, "count": 5, "percentage": 4.5 },
          { "ratingValue": 2, "count": 9, "percentage": 8.1 },
          { "ratingValue": 3, "count": 10, "percentage": 9.0 },
          { "ratingValue": 4, "count": 18, "percentage": 16.2 },
          { "ratingValue": 5, "count": 29, "percentage": 26.1 },
          { "ratingValue": 6, "count": 40, "percentage": 36.0 }
        ],
        "mean": 4.59,
        "responseCount": 111
      }
    ],
    "comments": [
      {
        "id": "uuid",
        "content": "I really wanted to make sure..."
      }
    ],
    "requirements": [
      {
        "id": "uuid",
        "name": "Formal Studies Distro Area"
      }
    ],
    "aiSummary": "Overall, student sentiment towards..."
  }
}
```

---

### Search

#### POST /api/search

Searches courses and comments by keyword. Returns matching courses and comments with their associated course offerings.

**Request Body:**
```json
{
  "query": "programming",
  "limit": 10
}
```

**Response:**
```json
{
  "data": {
    "courses": [
      {
        "id": "uuid",
        "code": "COMP_SCI_111-0",
        "title": "Fund Comp Prog",
        "description": "Fundamental concepts of computer programming...",
        "department": {
          "id": "uuid",
          "code": "COMP_SCI",
          "name": "Computer Science (COMP_SCI)"
        }
      }
    ],
    "comments": [
      {
        "id": "uuid",
        "content": "The professor was very enthusiastic...",
        "course_offering": {
          "id": "uuid",
          "quarter": "Fall",
          "year": 2023,
          "course": {
            "id": "uuid",
            "code": "COMP_SCI_111-0",
            "title": "Fund Comp Prog"
          },
          "instructor": {
            "id": "uuid",
            "name": "Connor Bain"
          }
        }
      }
    ]
  }
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (missing/invalid parameters)
- `404` - Resource not found
- `500` - Server error
