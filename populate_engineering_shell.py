# Engineering data population for Django shell
from knowledge.models import GlobalSubject, GlobalTopic
from django.contrib.auth.models import User

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

print("\n🎉 Successfully populated Engineering category - High School Level!")
print("Next: Run part 2 for Undergraduate level subjects")