#!/usr/bin/env python3
"""
Script to populate Engineering category subjects and topics in Indian context
"""

import os
import sys
import django

# Setup Django environment - fix path to current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')
django.setup()

from knowledge.models import GlobalSubject, GlobalTopic
from django.contrib.auth.models import User

def populate_engineering_data():
    # Get admin user for created_by field
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.filter(is_staff=True).first()
    
    print("Starting Engineering data population...")
    
    # 1. HIGH SCHOOL LEVEL - JEE PREPARATION
    
    # Physics for JEE
    physics_hs, created = GlobalSubject.objects.get_or_create(
        code="PHYS_JEE",
        defaults={
            'name': "Physics (JEE Preparation)",
            'description': "High school physics covering mechanics, thermodynamics, electricity, magnetism, optics and modern physics for engineering entrance preparation",
            'category': "engineering",
            'level': "high_school",
            'icon': "⚡",
            'color_code': "#f59e0b",
            'is_active': True,
            'is_featured': True,
            'created_by': admin_user,
            'reference_standards': ["CBSE Class 11-12", "JEE Main", "JEE Advanced", "NCERT"],
            'popularity_score': 95
        }
    )
    
    if created:
        physics_topics = [
            ("Mechanics", "Laws of motion, work energy power, rotational motion, gravitation, oscillations", "chapter", "medium", 1, 40),
            ("Thermodynamics", "Kinetic theory, laws of thermodynamics, heat engines, entropy", "chapter", "hard", 2, 25),
            ("Electricity and Magnetism", "Electrostatics, current electricity, magnetic effects, electromagnetic induction", "chapter", "hard", 3, 45),
            ("Optics", "Geometrical optics, wave optics, interference, diffraction, polarization", "chapter", "medium", 4, 20),
            ("Modern Physics", "Atomic structure, nuclear physics, photoelectric effect, dual nature of matter", "chapter", "hard", 5, 30),
            ("Oscillations and Waves", "Simple harmonic motion, wave motion, sound waves, Doppler effect", "chapter", "medium", 6, 25),
        ]
        
        for title, desc, topic_type, difficulty, order, hours in physics_topics:
            GlobalTopic.objects.get_or_create(
                subject=physics_hs,
                title=title,
                defaults={
                    'description': desc,
                    'topic_type': topic_type,
                    'difficulty': difficulty,
                    'order': order,
                    'estimated_hours': hours,
                    'is_active': True,
                    'is_template': True,
                    'is_approved': True,
                    'created_by': admin_user,
                    'learning_objectives': [f"Master {title.lower()} concepts", f"Solve {title.lower()} problems", f"Apply {title.lower()} in engineering"],
                    'keywords': [title.lower(), "physics", "engineering", "jee"],
                    'usage_count': 50
                }
            )
        print(f"✓ Created Physics (JEE) with {len(physics_topics)} topics")
    
    # Chemistry for JEE
    chemistry_hs, created = GlobalSubject.objects.get_or_create(
        code="CHEM_JEE",
        defaults={
            'name': "Chemistry (JEE Preparation)",
            'description': "High school chemistry covering physical, inorganic and organic chemistry for engineering entrance preparation",
            'category': "engineering",
            'level': "high_school",
            'icon': "🧪",
            'color_code': "#ef4444",
            'is_active': True,
            'is_featured': True,
            'created_by': admin_user,
            'reference_standards': ["CBSE Class 11-12", "JEE Main", "JEE Advanced", "NCERT"],
            'popularity_score': 90
        }
    )
    
    if created:
        chemistry_topics = [
            ("Physical Chemistry", "Atomic structure, chemical bonding, thermodynamics, equilibrium, electrochemistry", "chapter", "hard", 1, 50),
            ("Inorganic Chemistry", "Periodic table, s-block, p-block, d-block elements, coordination compounds", "chapter", "medium", 2, 40),
            ("Organic Chemistry", "Hydrocarbons, functional groups, reactions, biomolecules, polymers", "chapter", "hard", 3, 45),
            ("Chemical Kinetics", "Rate of reaction, factors affecting rate, mechanisms, catalysis", "chapter", "medium", 4, 20),
            ("Surface Chemistry", "Adsorption, colloids, emulsions, catalysis applications", "chapter", "easy", 5, 15),
        ]
        
        for title, desc, topic_type, difficulty, order, hours in chemistry_topics:
            GlobalTopic.objects.get_or_create(
                subject=chemistry_hs,
                title=title,
                defaults={
                    'description': desc,
                    'topic_type': topic_type,
                    'difficulty': difficulty,
                    'order': order,
                    'estimated_hours': hours,
                    'is_active': True,
                    'is_template': True,
                    'is_approved': True,
                    'created_by': admin_user,
                    'learning_objectives': [f"Master {title.lower()} concepts", f"Solve {title.lower()} problems"],
                    'keywords': [title.lower(), "chemistry", "engineering", "jee"],
                    'usage_count': 45
                }
            )
        print(f"✓ Created Chemistry (JEE) with {len(chemistry_topics)} topics")
    
    # Mathematics for JEE
    maths_hs, created = GlobalSubject.objects.get_or_create(
        code="MATH_JEE",
        defaults={
            'name': "Mathematics (JEE Preparation)",
            'description': "High school mathematics covering algebra, calculus, coordinate geometry, trigonometry for engineering entrance preparation",
            'category': "engineering",
            'level': "high_school",
            'icon': "📐",
            'color_code': "#8b5cf6",
            'is_active': True,
            'is_featured': True,
            'created_by': admin_user,
            'reference_standards': ["CBSE Class 11-12", "JEE Main", "JEE Advanced", "NCERT"],
            'popularity_score': 98
        }
    )
    
    if created:
        maths_topics = [
            ("Algebra", "Complex numbers, quadratic equations, sequences, series, binomial theorem", "chapter", "medium", 1, 35),
            ("Calculus", "Limits, derivatives, integration, differential equations, applications", "chapter", "hard", 2, 50),
            ("Coordinate Geometry", "Straight lines, circles, parabola, ellipse, hyperbola", "chapter", "medium", 3, 40),
            ("Trigonometry", "Trigonometric functions, identities, equations, inverse functions", "chapter", "medium", 4, 25),
            ("Vectors and 3D Geometry", "Vector algebra, 3D coordinates, planes, lines in space", "chapter", "hard", 5, 30),
            ("Probability and Statistics", "Probability, conditional probability, distributions, statistics", "chapter", "easy", 6, 20),
        ]
        
        for title, desc, topic_type, difficulty, order, hours in maths_topics:
            GlobalTopic.objects.get_or_create(
                subject=maths_hs,
                title=title,
                defaults={
                    'description': desc,
                    'topic_type': topic_type,
                    'difficulty': difficulty,
                    'order': order,
                    'estimated_hours': hours,
                    'is_active': True,
                    'is_template': True,
                    'is_approved': True,
                    'created_by': admin_user,
                    'learning_objectives': [f"Master {title.lower()} concepts", f"Solve {title.lower()} problems", f"Apply {title.lower()} in engineering"],
                    'keywords': [title.lower(), "mathematics", "engineering", "jee"],
                    'usage_count': 60
                }
            )
        print(f"✓ Created Mathematics (JEE) with {len(maths_topics)} topics")
    
    # 2. UNDERGRADUATE LEVEL - BTech Core Branches
    
    # Computer Science Engineering
    cse_ug, created = GlobalSubject.objects.get_or_create(
        code="CSE_BTECH",
        defaults={
            'name': "Computer Science & Engineering",
            'description': "Undergraduate computer science covering programming, algorithms, data structures, databases, networks, software engineering",
            'category': "engineering",
            'level': "undergraduate",
            'icon': "💻",
            'color_code': "#3b82f6",
            'is_active': True,
            'is_featured': True,
            'created_by': admin_user,
            'reference_standards': ["AICTE Model Curriculum", "IEEE/ACM Guidelines", "NEP 2020"],
            'popularity_score': 100
        }
    )
    
    if created:
        cse_topics = [
            ("Programming Fundamentals", "C, C++, Java, Python programming, OOPs concepts", "subject", "medium", 1, 80),
            ("Data Structures & Algorithms", "Arrays, linked lists, trees, graphs, searching, sorting algorithms", "subject", "hard", 2, 100),
            ("Computer Networks", "OSI model, TCP/IP, routing, switching, network security", "subject", "medium", 3, 60),
            ("Database Management Systems", "Relational databases, SQL, normalization, transactions, concurrency", "subject", "hard", 4, 70),
            ("Operating Systems", "Process management, memory management, file systems, concurrency", "subject", "hard", 5, 60),
            ("Software Engineering", "SDLC, design patterns, testing, project management, agile methodologies", "subject", "medium", 6, 50),
            ("Computer Architecture", "Processor design, memory hierarchy, instruction sets, parallel processing", "subject", "hard", 7, 50),
            ("Theory of Computation", "Automata theory, formal languages, computability, complexity theory", "subject", "expert", 8, 40),
            ("Machine Learning", "Supervised learning, unsupervised learning, neural networks, deep learning", "subject", "hard", 9, 60),
            ("Web Technologies", "HTML, CSS, JavaScript, frameworks, web services, cloud computing", "subject", "medium", 10, 45),
        ]
        
        for title, desc, topic_type, difficulty, order, hours in cse_topics:
            GlobalTopic.objects.get_or_create(
                subject=cse_ug,
                title=title,
                defaults={
                    'description': desc,
                    'topic_type': topic_type,
                    'difficulty': difficulty,
                    'order': order,
                    'estimated_hours': hours,
                    'is_active': True,
                    'is_template': True,
                    'is_approved': True,
                    'created_by': admin_user,
                    'learning_objectives': [f"Master {title.lower()}", f"Implement {title.lower()} solutions", f"Apply {title.lower()} in real projects"],
                    'keywords': [title.lower().replace(' & ', ' '), "computer science", "programming", "engineering"],
                    'usage_count': 75
                }
            )
        print(f"✓ Created Computer Science & Engineering with {len(cse_topics)} topics")
    
    # Electronics & Communication Engineering
    ece_ug, created = GlobalSubject.objects.get_or_create(
        code="ECE_BTECH",
        defaults={
            'name': "Electronics & Communication Engineering",
            'description': "Undergraduate electronics covering circuit analysis, digital electronics, communication systems, VLSI, embedded systems",
            'category': "engineering",
            'level': "undergraduate", 
            'icon': "📡",
            'color_code': "#06b6d4",
            'is_active': True,
            'is_featured': True,
            'created_by': admin_user,
            'reference_standards': ["AICTE Model Curriculum", "IEEE Standards", "Industry Requirements"],
            'popularity_score': 85
        }
    )
    
    if created:
        ece_topics = [
            ("Circuit Analysis", "Network theorems, AC/DC circuits, transient analysis, frequency response", "subject", "medium", 1, 70),
            ("Electronic Devices & Circuits", "Diodes, transistors, amplifiers, oscillators, power electronics", "subject", "hard", 2, 80),
            ("Digital Electronics", "Boolean algebra, combinational circuits, sequential circuits, microprocessors", "subject", "medium", 3, 60),
            ("Signals & Systems", "Signal analysis, Fourier transforms, Z-transforms, system analysis", "subject", "hard", 4, 65),
            ("Communication Engineering", "AM, FM, digital communication, modulation techniques, antenna theory", "subject", "hard", 5, 75),
            ("Control Systems", "Transfer functions, stability analysis, PID controllers, state space", "subject", "hard", 6, 55),
            ("VLSI Design", "CMOS technology, digital IC design, layout design, verification", "subject", "expert", 7, 60),
            ("Embedded Systems", "Microcontrollers, real-time systems, IoT, sensor interfacing", "subject", "hard", 8, 50),
            ("Electromagnetics", "Maxwell's equations, wave propagation, transmission lines, antennas", "subject", "expert", 9, 45),
            ("DSP", "Digital filters, DFT, FFT, speech processing, image processing", "subject", "hard", 10, 50),
        ]
        
        for title, desc, topic_type, difficulty, order, hours in ece_topics:
            GlobalTopic.objects.get_or_create(
                subject=ece_ug,
                title=title,
                defaults={
                    'description': desc,
                    'topic_type': topic_type,
                    'difficulty': difficulty,
                    'order': order,
                    'estimated_hours': hours,
                    'is_active': True,
                    'is_template': True,
                    'is_approved': True,
                    'created_by': admin_user,
                    'learning_objectives': [f"Master {title.lower()}", f"Design {title.lower()} systems", f"Analyze {title.lower()} problems"],
                    'keywords': [title.lower(), "electronics", "communication", "engineering"],
                    'usage_count': 65
                }
            )
        print(f"✓ Created Electronics & Communication Engineering with {len(ece_topics)} topics")
        
    # 3. COMPETITIVE LEVEL - Engineering Services Exam
    
    # Engineering Services Exam
    ese_comp, created = GlobalSubject.objects.get_or_create(
        code="ESE_COMP",
        defaults={
            'name': "Engineering Services Examination (ESE)",
            'description': "Civil services exam for engineers covering technical subjects, general studies, and engineering aptitude",
            'category': "engineering",
            'level': "competitive",
            'icon': "🏛️",
            'color_code': "#dc2626",
            'is_active': True,
            'is_featured': True,
            'created_by': admin_user,
            'reference_standards': ["UPSC ESE Syllabus", "Technical Services", "Government Standards"],
            'popularity_score': 70
        }
    )
    
    if created:
        ese_topics = [
            ("General Studies & Engineering Aptitude", "Current affairs, Indian history, geography, engineering mathematics", "subject", "medium", 1, 100),
            ("Civil Engineering", "Structural engineering, geotechnical, transportation, environmental", "subject", "hard", 2, 120),
            ("Mechanical Engineering", "Thermodynamics, fluid mechanics, machine design, manufacturing", "subject", "hard", 3, 120),
            ("Electrical Engineering", "Power systems, machines, control systems, electronics", "subject", "hard", 4, 120),
            ("Electronics & Telecom", "Analog/digital electronics, communication systems, networks", "subject", "hard", 5, 100),
        ]
        
        for title, desc, topic_type, difficulty, order, hours in ese_topics:
            GlobalTopic.objects.get_or_create(
                subject=ese_comp,
                title=title,
                defaults={
                    'description': desc,
                    'topic_type': topic_type,
                    'difficulty': difficulty,
                    'order': order,
                    'estimated_hours': hours,
                    'is_active': True,
                    'is_template': True,
                    'is_approved': True,
                    'created_by': admin_user,
                    'learning_objectives': [f"Master {title.lower()}", f"Apply concepts in government services", f"Solve {title.lower()} problems"],
                    'keywords': [title.lower(), "ese", "upsc", "engineering services"],
                    'usage_count': 40
                }
            )
        print(f"✓ Created Engineering Services Examination with {len(ese_topics)} topics")
    
    print("\n🎉 Successfully populated Engineering category with:")
    print("- High School Level: Physics, Chemistry, Mathematics (JEE Prep)")
    print("- Undergraduate Level: CSE, ECE")  
    print("- Competitive Level: ESE")
    print("- Total subjects created with comprehensive topic hierarchies")

if __name__ == "__main__":
    populate_engineering_data()