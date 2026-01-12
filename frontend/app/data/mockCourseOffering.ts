import { CourseOffering } from '@/app/types/course';

export const mockCourseOffering: CourseOffering = {
  id: 'offering-123',
  course: {
    id: 'course-456',
    code: 'COMP_SCI 111',
    title: 'Fund Comp Prog'
  },
  instructor: {
    id: 'instructor-789',
    name: 'Connor Bain',
    profile_photo: undefined
  },
  quarter: 'Fall',
  year: 2023,
  section: 2,
  audienceSize: 217,
  responseCount: 183,
  requirements: [
    { id: 'req-1', name: 'Formal Studies' },
    { id: 'req-2', name: 'Quantitative Reasoning' }
  ],
  aiSummary: 'This course provides a strong foundation in computer programming fundamentals using the Racket programming language. Students consistently praise Professor Bain\'s engaging teaching style and clear explanations, though many note the challenges of learning Racket as a first programming language. The course is well-structured with good support through office hours and tutorials.',
  ratings: [
    {
      id: 'rating-1',
      surveyQuestion: {
        id: 'q1',
        question: 'Provide an overall rating of the instruction.'
      },
      distribution: [
        { ratingValue: 1, count: 0, percentage: 0.0 },
        { ratingValue: 2, count: 2, percentage: 1.1 },
        { ratingValue: 3, count: 3, percentage: 1.7 },
        { ratingValue: 4, count: 19, percentage: 10.6 },
        { ratingValue: 5, count: 45, percentage: 25.0 },
        { ratingValue: 6, count: 111, percentage: 61.7 }
      ],
      mean: 5.44,
      responseCount: 180
    },
    {
      id: 'rating-2',
      surveyQuestion: {
        id: 'q2',
        question: 'Provide an overall rating of the course.'
      },
      distribution: [
        { ratingValue: 1, count: 0, percentage: 0.0 },
        { ratingValue: 2, count: 5, percentage: 2.7 },
        { ratingValue: 3, count: 18, percentage: 9.9 },
        { ratingValue: 4, count: 47, percentage: 25.8 },
        { ratingValue: 5, count: 59, percentage: 32.4 },
        { ratingValue: 6, count: 53, percentage: 29.1 }
      ],
      mean: 4.75,
      responseCount: 182
    },
    {
      id: 'rating-3',
      surveyQuestion: {
        id: 'q3',
        question: 'Estimate how much you learned in the course.'
      },
      distribution: [
        { ratingValue: 1, count: 1, percentage: 0.5 },
        { ratingValue: 2, count: 17, percentage: 9.3 },
        { ratingValue: 3, count: 30, percentage: 16.4 },
        { ratingValue: 4, count: 50, percentage: 27.3 },
        { ratingValue: 5, count: 50, percentage: 27.3 },
        { ratingValue: 6, count: 35, percentage: 19.1 }
      ],
      mean: 4.29,
      responseCount: 183
    },
    {
      id: 'rating-4',
      surveyQuestion: {
        id: 'q4',
        question: 'Rate the effectiveness of the course in challenging you intellectually.'
      },
      distribution: [
        { ratingValue: 1, count: 6, percentage: 3.3 },
        { ratingValue: 2, count: 16, percentage: 8.7 },
        { ratingValue: 3, count: 32, percentage: 17.5 },
        { ratingValue: 4, count: 52, percentage: 28.4 },
        { ratingValue: 5, count: 44, percentage: 24.0 },
        { ratingValue: 6, count: 33, percentage: 18.0 }
      ],
      mean: 4.15,
      responseCount: 183
    },
    {
      id: 'rating-5',
      surveyQuestion: {
        id: 'q5',
        question: 'Rate the effectiveness of the instructor in stimulating your interest in the subject.'
      },
      distribution: [
        { ratingValue: 1, count: 0, percentage: 0.0 },
        { ratingValue: 2, count: 4, percentage: 2.2 },
        { ratingValue: 3, count: 8, percentage: 4.4 },
        { ratingValue: 4, count: 35, percentage: 19.4 },
        { ratingValue: 5, count: 52, percentage: 28.9 },
        { ratingValue: 6, count: 81, percentage: 45.0 }
      ],
      mean: 5.10,
      responseCount: 180
    },
    {
      id: 'rating-6',
      surveyQuestion: {
        id: 'q6',
        question: 'Rate the amount you learned relative to your effort.'
      },
      distribution: [
        { ratingValue: 1, count: 3, percentage: 1.6 },
        { ratingValue: 2, count: 12, percentage: 6.6 },
        { ratingValue: 3, count: 28, percentage: 15.4 },
        { ratingValue: 4, count: 55, percentage: 30.2 },
        { ratingValue: 5, count: 48, percentage: 26.4 },
        { ratingValue: 6, count: 36, percentage: 19.8 }
      ],
      mean: 4.35,
      responseCount: 182
    },
    {
      id: 'rating-7',
      surveyQuestion: {
        id: 'q7',
        question: 'Rate the clarity of the instructor\'s explanations.'
      },
      distribution: [
        { ratingValue: 1, count: 1, percentage: 0.6 },
        { ratingValue: 2, count: 3, percentage: 1.7 },
        { ratingValue: 3, count: 7, percentage: 3.9 },
        { ratingValue: 4, count: 25, percentage: 13.9 },
        { ratingValue: 5, count: 52, percentage: 28.9 },
        { ratingValue: 6, count: 92, percentage: 51.1 }
      ],
      mean: 5.23,
      responseCount: 180
    },
    {
      id: 'rating-8',
      surveyQuestion: {
        id: 'q8',
        question: 'Rate the availability of the instructor for consultation.'
      },
      distribution: [
        { ratingValue: 1, count: 2, percentage: 1.1 },
        { ratingValue: 2, count: 3, percentage: 1.7 },
        { ratingValue: 3, count: 8, percentage: 4.4 },
        { ratingValue: 4, count: 28, percentage: 15.6 },
        { ratingValue: 5, count: 45, percentage: 25.0 },
        { ratingValue: 6, count: 94, percentage: 52.2 }
      ],
      mean: 5.21,
      responseCount: 180
    },
    {
      id: 'rating-9',
      surveyQuestion: {
        id: 'q9',
        question: 'Rate the usefulness of the assignments in learning the subject matter.'
      },
      distribution: [
        { ratingValue: 1, count: 1, percentage: 0.5 },
        { ratingValue: 2, count: 8, percentage: 4.4 },
        { ratingValue: 3, count: 22, percentage: 12.0 },
        { ratingValue: 4, count: 48, percentage: 26.2 },
        { ratingValue: 5, count: 58, percentage: 31.7 },
        { ratingValue: 6, count: 46, percentage: 25.1 }
      ],
      mean: 4.65,
      responseCount: 183
    },
    {
      id: 'rating-10',
      surveyQuestion: {
        id: 'q10',
        question: 'Rate the fairness of the grading procedures.'
      },
      distribution: [
        { ratingValue: 1, count: 0, percentage: 0.0 },
        { ratingValue: 2, count: 2, percentage: 1.1 },
        { ratingValue: 3, count: 5, percentage: 2.8 },
        { ratingValue: 4, count: 15, percentage: 8.3 },
        { ratingValue: 5, count: 48, percentage: 26.7 },
        { ratingValue: 6, count: 110, percentage: 61.1 }
      ],
      mean: 5.44,
      responseCount: 180
    }
  ],
  comments: [
    {
      id: 'comment-1',
      content: 'This is a great intro class to CS with a fantastic professor. Dr. Bain is a really engaging lecturer and gives many good examples for us to better understand abstract concepts about computer science. The Racket language is fairly easy to use and is really beginner friendly so there should be no fear about that. I would say that the weekly homeworks seem daunting but they are very easy and the class has many office hours opportunities both online and in–person to help with them.'
    },
    {
      id: 'comment-2',
      content: 'to say the least, i hated this class. the professor wasnt the issue, it was just racket which is a really outdated language so i dont know why we\'re learning it. as someone with past comp sci experience, racket was difficult to understand. the assignments are manageable and dont take a lot of time. racket is just rly different from other languages so it might take a while to understand how it works.'
    },
    {
      id: 'comment-3',
      content: 'Quickly became one of my favorite courses in the quarter, the structure of the course was easy to follow and kept a good pace. Professor Connor Bain is probably the best professor this course could have, even on the more boring days he always brought energy and passion to his lectures. He made the course fun, and you could tell he cares a lot about the class as he would often stay after class ended for office hours to help on whatever the students needed, whether it be the tutorials or exercises.'
    },
    {
      id: 'comment-4',
      content: 'This course isn\'t too difficult, Racket is annoying to program in (and honestly a pretty useless language to learn), but I wouldn\'t call it difficult by any means. Bain is extremely nice, to the point that if you already have CS knowledge it\'s honestly a little annoying (I felt like I was being talked to like a toddler sometimes), but if you have no CS knowledge at all it\'s nice to have an instructor like him.'
    },
    {
      id: 'comment-5',
      content: 'This course was interesting and I enjoyed the different class methods. Professor Bain helps to make the lectures entertaining, and I enjoyed the format of the class in that on Wednesdays we had tutorials where we got to collaborate with other people in the class if we needed help. There definitely wasn\'t a lack of support with the OH, PMs, etc.'
    },
    {
      id: 'comment-6',
      content: 'I think the course was pretty enjoyable. I really do think Professor Bain was right about the class getting pretty hard up until recursion and then getting easier. Overall, i think this is a really good class to take if you are interested in getting into coding.'
    },
    {
      id: 'comment-7',
      content: 'Connor Bain is an interesting man. Things to note: – 4 quizzes per quarter, lowest is dropped. TAKE THESE SERIOUSLY, EVEN IF YOU KNOW HOW TO CODE BEFOREHAND. – Weekly exercises are easy, but make sure for the Snake game and for the final exercise you don\'t wait until the last day to do them – Other than that pretty chill class. Bain the goat.'
    },
    {
      id: 'comment-8',
      content: 'Racket sucks but everyone already knows that. I think Racket makes many things a lot more complicated compared to other languages, especially recursion, so I don\'t really understand why Racket is used to teach an introductory class. Exams are also purposely just trying to trick you and you have to catch every little trick in the code or you get many points off since some questions are worth 10 points and the exams are only 100 total.'
    },
    {
      id: 'comment-9',
      content: 'I enjoyed and learned quite a lot from this class. Coming in as someone who already had 2 years of coding experience, this class was not overwhelming and still managed to challenge me, making me a better coder in the process. Professor Bain\'s lectures were quite helpful in being able to learn the specifics of the Racket coding language, as it is different from almost any other language.'
    },
    {
      id: 'comment-10',
      content: 'This class was pretty manageable. The lectures were easy to follow along with and the instructor brought a great energy to the whole class. The only hard part would be the later weekly exercise assignments became a pain to do. They would take hours and many times I had to go into office hours to finish them. But reaching out for help was not a problem.'
    },
    {
      id: 'comment-11',
      content: 'This course is so active and depends on the practice more to become familiar with the materials and the contacts of the course. This course laid the foundation for how to program in any language, not just the study of a singular language, which is very important in today\'s computer science landscape.'
    },
    {
      id: 'comment-12',
      content: 'Overall CS 111 was a good introductory class to programming as a beginner. Course content and slides were clear to follow. The class was good in helping us learn, especially with Prof. Bain\'s teaching. It was quite a lot of work, especially if you want to get an A.'
    },
    {
      id: 'comment-13',
      content: 'Pretty easy intro to programming – if you\'ve done it before this class will be a breeze although you may want to rip your hair out due to Racket (the random programming language used for the class). Instruction is clear and makes sense – homework and exams are manageable – you shouldn\'t have any trouble if you put more than 5% of your brain into this class.'
    },
    {
      id: 'comment-14',
      content: 'Professor Bain is a really great instructor! He made an extremely organized course with engaging lectures, practice quizzes, and helpful but fun assignments. Lots of opportunity for help and very beginner friendly.'
    },
    {
      id: 'comment-15',
      content: 'Very good class to take as a beginner CS student. Also good for those with some programming experience. The professor is very accommodating and the work is not daunting at all.'
    },
    {
      id: 'comment-16',
      content: 'The course started off as pretty basic. The first few classes are significantly easy especially if you have a prior knowledge of programming. However, as it continued, it got much harder and as a person with prior experience with java and c++, adjusting to dr.racket was really challenging. But when you get past that, everything is pretty straightforward.'
    },
    {
      id: 'comment-17',
      content: 'One big assignment weekly that can take anywhere from 30 minutes to 3 hours. 4 exams but can drop one. Should receive an A if all assignments are completed with full marks (can drop one), attend classes, and 82.5+ average on 3/4 tests. Basically put in the work and you will be rewarded fairly and accordingly.'
    },
    {
      id: 'comment-18',
      content: 'While I think this class is a good introduction to computer programming (and the programming language called Dr. Racket), I found it challenging to keep up with the course, as there are a lot of moving parts each week and the class accelerates pretty quickly. However, Professor Bain is an excellent lecturer and there are a lot of resources available to students to help them succeed.'
    },
    {
      id: 'comment-19',
      content: 'This course was amazing. The professor is one of the best I have ever had at NU and he made himself available for his students way more than I would have expected. In such a large class, it can often be easy to feel lost in the mass and not noticed by the professor, but he took care to help and acknowledge every student who needed/wanted it.'
    },
    {
      id: 'comment-20',
      content: 'This is an interesting class because you do not use any programming language. While this sounds like it would be easy, if you have prior coding experience, you might be confused. Some things are very racket specific and thus make some assignments tedious.'
    }
  ]
};