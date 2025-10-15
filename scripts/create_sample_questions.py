#!/usr/bin/env python3
"""
Script to create 100 sample multiple choice questions for the test platform.
Run this script from the Django project root directory.

Usage:
    python create_sample_questions.py
"""

import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
django.setup()

from questions.models import QuestionBank, Question, QuestionOption
from exams.models import Exam, Test
import random

# Sample question data organized by category
SAMPLE_QUESTIONS = {
    'mathematics': [
        {
            'question': 'What is the result of 15 + 27?',
            'options': [
                {'text': '42', 'correct': True},
                {'text': '41', 'correct': False},
                {'text': '43', 'correct': False},
                {'text': '40', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Basic Arithmetic',
            'explanation': 'Simple addition: 15 + 27 = 42'
        },
        {
            'question': 'What is the derivative of x²?',
            'options': [
                {'text': '2x', 'correct': True},
                {'text': 'x', 'correct': False},
                {'text': '2x²', 'correct': False},
                {'text': 'x²/2', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Calculus',
            'explanation': 'Using the power rule: d/dx(x²) = 2x¹ = 2x'
        },
        {
            'question': 'What is the value of π (pi) to 2 decimal places?',
            'options': [
                {'text': '3.14', 'correct': True},
                {'text': '3.15', 'correct': False},
                {'text': '3.13', 'correct': False},
                {'text': '3.16', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Constants',
            'explanation': 'π ≈ 3.14159..., rounded to 2 decimal places is 3.14'
        },
        {
            'question': 'What is the solution to the equation 2x + 5 = 13?',
            'options': [
                {'text': 'x = 4', 'correct': True},
                {'text': 'x = 3', 'correct': False},
                {'text': 'x = 5', 'correct': False},
                {'text': 'x = 6', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Algebra',
            'explanation': '2x + 5 = 13 → 2x = 8 → x = 4'
        },
        {
            'question': 'What is the area of a circle with radius 5?',
            'options': [
                {'text': '25π', 'correct': True},
                {'text': '10π', 'correct': False},
                {'text': '5π', 'correct': False},
                {'text': '50π', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Geometry',
            'explanation': 'Area = πr² = π × 5² = 25π'
        }
    ],
    'science': [
        {
            'question': 'What is the chemical symbol for water?',
            'options': [
                {'text': 'H2O', 'correct': True},
                {'text': 'CO2', 'correct': False},
                {'text': 'NaCl', 'correct': False},
                {'text': 'O2', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Chemistry',
            'explanation': 'Water consists of 2 hydrogen atoms and 1 oxygen atom: H2O'
        },
        {
            'question': 'What is the speed of light in vacuum?',
            'options': [
                {'text': '299,792,458 m/s', 'correct': True},
                {'text': '300,000,000 m/s', 'correct': False},
                {'text': '299,000,000 m/s', 'correct': False},
                {'text': '298,792,458 m/s', 'correct': False}
            ],
            'difficulty': 'hard',
            'topic': 'Physics',
            'explanation': 'The speed of light in vacuum is exactly 299,792,458 meters per second'
        },
        {
            'question': 'Which planet is closest to the Sun?',
            'options': [
                {'text': 'Mercury', 'correct': True},
                {'text': 'Venus', 'correct': False},
                {'text': 'Earth', 'correct': False},
                {'text': 'Mars', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Astronomy',
            'explanation': 'Mercury is the innermost planet in our solar system'
        },
        {
            'question': 'What is the powerhouse of the cell?',
            'options': [
                {'text': 'Mitochondria', 'correct': True},
                {'text': 'Nucleus', 'correct': False},
                {'text': 'Ribosome', 'correct': False},
                {'text': 'Endoplasmic Reticulum', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Biology',
            'explanation': 'Mitochondria produce ATP (energy) for cellular processes'
        },
        {
            'question': 'What gas do plants absorb from the atmosphere during photosynthesis?',
            'options': [
                {'text': 'Carbon Dioxide (CO2)', 'correct': True},
                {'text': 'Oxygen (O2)', 'correct': False},
                {'text': 'Nitrogen (N2)', 'correct': False},
                {'text': 'Hydrogen (H2)', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Biology',
            'explanation': 'Plants absorb CO2 and release O2 during photosynthesis'
        }
    ],
    'computer_science': [
        {
            'question': 'What does "HTML" stand for?',
            'options': [
                {'text': 'HyperText Markup Language', 'correct': True},
                {'text': 'High-Level Text Management Language', 'correct': False},
                {'text': 'Home Tool Markup Language', 'correct': False},
                {'text': 'Hyperlink and Text Markup Language', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Web Development',
            'explanation': 'HTML stands for HyperText Markup Language'
        },
        {
            'question': 'Which data structure follows the LIFO (Last In, First Out) principle?',
            'options': [
                {'text': 'Stack', 'correct': True},
                {'text': 'Queue', 'correct': False},
                {'text': 'Array', 'correct': False},
                {'text': 'Linked List', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Data Structures',
            'explanation': 'A stack follows LIFO - the last element added is the first one removed'
        },
        {
            'question': 'What is the time complexity of binary search?',
            'options': [
                {'text': 'O(log n)', 'correct': True},
                {'text': 'O(n)', 'correct': False},
                {'text': 'O(n²)', 'correct': False},
                {'text': 'O(1)', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Algorithms',
            'explanation': 'Binary search divides the search space in half each iteration: O(log n)'
        },
        {
            'question': 'Which programming language is known as the "mother of all languages"?',
            'options': [
                {'text': 'C', 'correct': True},
                {'text': 'Assembly', 'correct': False},
                {'text': 'FORTRAN', 'correct': False},
                {'text': 'COBOL', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Programming Languages',
            'explanation': 'C is often called the mother of modern programming languages'
        },
        {
            'question': 'What does "SQL" stand for?',
            'options': [
                {'text': 'Structured Query Language', 'correct': True},
                {'text': 'Simple Query Language', 'correct': False},
                {'text': 'Standard Query Language', 'correct': False},
                {'text': 'Sequential Query Language', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Database',
            'explanation': 'SQL stands for Structured Query Language'
        }
    ],
    'english': [
        {
            'question': 'Which of the following is a synonym for "happy"?',
            'options': [
                {'text': 'Joyful', 'correct': True},
                {'text': 'Sad', 'correct': False},
                {'text': 'Angry', 'correct': False},
                {'text': 'Confused', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Vocabulary',
            'explanation': 'Joyful means filled with happiness and joy'
        },
        {
            'question': 'What is the past tense of "run"?',
            'options': [
                {'text': 'Ran', 'correct': True},
                {'text': 'Runned', 'correct': False},
                {'text': 'Running', 'correct': False},
                {'text': 'Runs', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Grammar',
            'explanation': 'Run is an irregular verb: run, ran, run'
        },
        {
            'question': 'Which literary device is used in "The wind whispered through the trees"?',
            'options': [
                {'text': 'Personification', 'correct': True},
                {'text': 'Metaphor', 'correct': False},
                {'text': 'Simile', 'correct': False},
                {'text': 'Alliteration', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Literature',
            'explanation': 'Personification gives human qualities (whispering) to non-human things (wind)'
        },
        {
            'question': 'Who wrote "Romeo and Juliet"?',
            'options': [
                {'text': 'William Shakespeare', 'correct': True},
                {'text': 'Charles Dickens', 'correct': False},
                {'text': 'Jane Austen', 'correct': False},
                {'text': 'Mark Twain', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Literature',
            'explanation': 'Romeo and Juliet is one of Shakespeare\'s most famous tragedies'
        },
        {
            'question': 'What type of sentence is "Stop!"?',
            'options': [
                {'text': 'Imperative', 'correct': True},
                {'text': 'Declarative', 'correct': False},
                {'text': 'Interrogative', 'correct': False},
                {'text': 'Exclamatory', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Grammar',
            'explanation': 'Imperative sentences give commands or make requests'
        }
    ],
    'history': [
        {
            'question': 'In which year did World War II end?',
            'options': [
                {'text': '1945', 'correct': True},
                {'text': '1944', 'correct': False},
                {'text': '1946', 'correct': False},
                {'text': '1943', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'World History',
            'explanation': 'World War II ended in 1945 with the surrender of Japan'
        },
        {
            'question': 'Who was the first President of the United States?',
            'options': [
                {'text': 'George Washington', 'correct': True},
                {'text': 'Thomas Jefferson', 'correct': False},
                {'text': 'John Adams', 'correct': False},
                {'text': 'Benjamin Franklin', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'American History',
            'explanation': 'George Washington served as the first President from 1789-1797'
        },
        {
            'question': 'The ancient city of Rome was built on how many hills?',
            'options': [
                {'text': 'Seven', 'correct': True},
                {'text': 'Five', 'correct': False},
                {'text': 'Six', 'correct': False},
                {'text': 'Eight', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Ancient History',
            'explanation': 'Rome was famously built on seven hills'
        },
        {
            'question': 'Which empire was ruled by Julius Caesar?',
            'options': [
                {'text': 'Roman Empire', 'correct': True},
                {'text': 'Greek Empire', 'correct': False},
                {'text': 'Egyptian Empire', 'correct': False},
                {'text': 'Persian Empire', 'correct': False}
            ],
            'difficulty': 'easy',
            'topic': 'Ancient History',
            'explanation': 'Julius Caesar was a Roman general and statesman'
        },
        {
            'question': 'The Berlin Wall fell in which year?',
            'options': [
                {'text': '1989', 'correct': True},
                {'text': '1987', 'correct': False},
                {'text': '1991', 'correct': False},
                {'text': '1985', 'correct': False}
            ],
            'difficulty': 'medium',
            'topic': 'Modern History',
            'explanation': 'The Berlin Wall fell on November 9, 1989'
        }
    ]
}

def create_admin_user():
    """Create an admin user if none exists"""
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        print("Created admin user: admin/admin123")
        return admin_user
    else:
        return User.objects.get(username='admin')

def generate_additional_questions(category, base_questions, target_count):
    """Generate additional questions by varying the base questions"""
    questions = base_questions.copy()
    
    # Templates for generating more questions
    templates = {
        'mathematics': [
            {
                'question': 'What is {} + {}?',
                'generator': lambda: {
                    'nums': [random.randint(10, 50), random.randint(10, 50)],
                    'difficulty': 'easy',
                    'topic': 'Basic Arithmetic'
                }
            },
            {
                'question': 'What is {} × {}?',
                'generator': lambda: {
                    'nums': [random.randint(2, 12), random.randint(2, 12)],
                    'difficulty': 'medium',
                    'topic': 'Multiplication'
                }
            }
        ],
        'science': [
            {
                'question': 'What is the atomic number of {}?',
                'elements': [
                    {'name': 'Hydrogen', 'number': 1},
                    {'name': 'Helium', 'number': 2},
                    {'name': 'Carbon', 'number': 6},
                    {'name': 'Oxygen', 'number': 8},
                    {'name': 'Sodium', 'number': 11},
                    {'name': 'Iron', 'number': 26}
                ],
                'difficulty': 'medium',
                'topic': 'Chemistry'
            }
        ]
    }
    
    while len(questions) < target_count:
        if category == 'mathematics' and len(questions) < target_count:
            # Generate arithmetic questions
            a, b = random.randint(10, 100), random.randint(10, 100)
            answer = a + b
            wrong_answers = [answer + random.randint(1, 10), 
                           answer - random.randint(1, 10), 
                           answer + random.randint(11, 20)]
            
            questions.append({
                'question': f'What is {a} + {b}?',
                'options': [
                    {'text': str(answer), 'correct': True},
                    {'text': str(wrong_answers[0]), 'correct': False},
                    {'text': str(wrong_answers[1]), 'correct': False},
                    {'text': str(wrong_answers[2]), 'correct': False}
                ],
                'difficulty': 'easy',
                'topic': 'Basic Arithmetic',
                'explanation': f'{a} + {b} = {answer}'
            })
        
        elif category == 'science' and len(questions) < target_count:
            # Generate element questions
            elements = [
                {'name': 'Hydrogen', 'symbol': 'H', 'number': 1},
                {'name': 'Helium', 'symbol': 'He', 'number': 2},
                {'name': 'Carbon', 'symbol': 'C', 'number': 6},
                {'name': 'Nitrogen', 'symbol': 'N', 'number': 7},
                {'name': 'Oxygen', 'symbol': 'O', 'number': 8},
                {'name': 'Sodium', 'symbol': 'Na', 'number': 11},
                {'name': 'Magnesium', 'symbol': 'Mg', 'number': 12},
                {'name': 'Aluminum', 'symbol': 'Al', 'number': 13},
                {'name': 'Silicon', 'symbol': 'Si', 'number': 14},
                {'name': 'Chlorine', 'symbol': 'Cl', 'number': 17},
            ]
            
            element = random.choice(elements)
            wrong_symbols = [e['symbol'] for e in elements if e['symbol'] != element['symbol']]
            random.shuffle(wrong_symbols)
            
            questions.append({
                'question': f'What is the chemical symbol for {element["name"]}?',
                'options': [
                    {'text': element['symbol'], 'correct': True},
                    {'text': wrong_symbols[0], 'correct': False},
                    {'text': wrong_symbols[1], 'correct': False},
                    {'text': wrong_symbols[2], 'correct': False}
                ],
                'difficulty': 'medium',
                'topic': 'Chemistry',
                'explanation': f'The chemical symbol for {element["name"]} is {element["symbol"]}'
            })
        
        else:
            # For other categories, cycle through existing questions with variations
            base_q = random.choice(base_questions)
            variation = base_q.copy()
            variation['question'] = f"[Variation] {variation['question']}"
            questions.append(variation)
    
    return questions[:target_count]

def create_sample_data():
    """Create sample question bank and questions"""
    print("Creating sample data...")
    
    # Get or create admin user
    admin_user = create_admin_user()
    
    # Create question bank
    question_bank, created = QuestionBank.objects.get_or_create(
        name="Sample Question Bank - 100 MCQs",
        defaults={
            'description': 'A comprehensive collection of 100 multiple choice questions across various subjects',
            'category': 'other',
            'tags': ['sample', 'mcq', 'demo', 'comprehensive'],
            'created_by': admin_user,
            'is_public': True,
            'default_difficulty': 'medium',
            'default_marks': 1.0
        }
    )
    
    if created:
        print(f"Created question bank: {question_bank.name}")
    else:
        print(f"Using existing question bank: {question_bank.name}")
    
    # Clear existing questions if recreating
    if not created:
        question_bank.questions.all().delete()
        print("Cleared existing questions")
    
    # Calculate questions per category (targeting 100 total)
    categories = list(SAMPLE_QUESTIONS.keys())
    questions_per_category = 100 // len(categories)  # 20 per category
    remaining = 100 % len(categories)
    
    total_created = 0
    
    for i, (category, base_questions) in enumerate(SAMPLE_QUESTIONS.items()):
        # Add extra questions to first few categories for remainder
        target_count = questions_per_category + (1 if i < remaining else 0)
        
        # Generate enough questions for this category
        category_questions = generate_additional_questions(category, base_questions, target_count)
        
        print(f"\nCreating {len(category_questions)} questions for {category}...")
        
        for q_idx, q_data in enumerate(category_questions):
            # Create question
            question = Question.objects.create(
                question_bank=question_bank,
                question_text=q_data['question'],
                question_type='mcq',
                difficulty=q_data['difficulty'],
                marks=1.0,
                topic=q_data['topic'],
                explanation=q_data.get('explanation', ''),
                tags=[category, q_data['topic'].lower().replace(' ', '_')],
                created_by=admin_user
            )
            
            # Create options
            for opt_idx, option_data in enumerate(q_data['options']):
                QuestionOption.objects.create(
                    question=question,
                    option_text=option_data['text'],
                    is_correct=option_data['correct'],
                    order=opt_idx + 1
                )
            
            total_created += 1
            
            if q_idx < 3:  # Show first few questions
                print(f"  ✓ {question.question_text[:60]}...")
    
    print(f"\n✅ Successfully created {total_created} questions across {len(categories)} categories!")
    
    # Create a sample exam and test
    exam, created = Exam.objects.get_or_create(
        name="Sample Comprehensive Exam",
        defaults={
            'description': 'A sample exam demonstrating the platform capabilities with 100 questions',
            'created_by': admin_user,
            'category': 'general',
            'is_active': True
        }
    )
    
    test, created = Test.objects.get_or_create(
        exam=exam,
        title="100 Question MCQ Test",
        defaults={
            'description': 'Sample test with 100 multiple choice questions from various subjects',
            'duration_minutes': 120,  # 2 hours
            'total_marks': 100,
            'pass_percentage': 60.0,
            'is_published': True,
            'randomize_questions': True,
            'show_result_immediately': True,
            'allow_review': True,
            'max_attempts': 3,
            'created_by': admin_user
        }
    )
    
    if created:
        print(f"✅ Created sample test: {test.title}")
        
        # Link questions to test (optional - you can do this through admin)
        from questions.models import TestQuestion
        questions = Question.objects.filter(question_bank=question_bank)
        for idx, question in enumerate(questions, 1):
            TestQuestion.objects.get_or_create(
                test=test,
                question=question,
                defaults={
                    'order': idx,
                    'marks': 1
                }
            )
        print(f"✅ Linked {questions.count()} questions to the test")
    
    return {
        'question_bank': question_bank,
        'questions_created': total_created,
        'exam': exam,
        'test': test
    }

def main():
    """Main function"""
    print("🚀 Starting sample question creation...")
    print("=" * 50)
    
    try:
        result = create_sample_data()
        
        print("\n" + "=" * 50)
        print("📊 SUMMARY:")
        print(f"✅ Question Bank: {result['question_bank'].name}")
        print(f"✅ Questions Created: {result['questions_created']}")
        print(f"✅ Sample Exam: {result['exam'].name}")
        print(f"✅ Sample Test: {result['test'].title}")
        
        print("\n🎯 Next Steps:")
        print("1. Visit Django Admin at /admin/ (login: admin/admin123)")
        print("2. Navigate to Questions > Question Banks to view questions")
        print("3. Navigate to Exams > Tests to see the sample test")
        print("4. You can now create test attempts and use the platform!")
        
        print("\n📋 Question Distribution:")
        for category in SAMPLE_QUESTIONS.keys():
            count = Question.objects.filter(
                question_bank=result['question_bank'],
                tags__contains=[category]
            ).count()
            print(f"   {category.title()}: {count} questions")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()