from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from knowledge.models import GlobalSubject, GlobalTopic, TopicImportTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample subjects and topics for testing the global taxonomy system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample global taxonomy data...'))
        
        # Get or create a user for the data
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        
        # Create Mathematics Subject
        math_subject, created = GlobalSubject.objects.get_or_create(
            code='MATH',
            defaults={
                'name': 'Mathematics',
                'description': 'Comprehensive mathematics curriculum covering algebra, geometry, calculus, and statistics',
                'category': 'mathematics',
                'level': 'high_school',
                'icon': '🔢',
                'color_code': '#3B82F6',
                'created_by': admin_user,
                'approved_by': admin_user,
            }
        )
        
        # Create Mathematics Topics
        algebra_unit = GlobalTopic.objects.get_or_create(
            subject=math_subject,
            title='Algebra',
            defaults={
                'description': 'Fundamental algebraic concepts and operations',
                'topic_type': 'unit',
                'difficulty': 'medium',
                'priority': 'high',
                'estimated_hours': 40,
                'learning_objectives': [
                    'Understand algebraic expressions and equations',
                    'Solve linear and quadratic equations',
                    'Work with polynomials and factoring',
                    'Apply algebraic concepts to real-world problems'
                ],
                'keywords': ['algebra', 'equations', 'variables', 'polynomials'],
                'created_by': admin_user,
                'is_approved': True,
                'approved_by': admin_user,
            }
        )[0]
        
        # Linear Equations Chapter
        linear_equations = GlobalTopic.objects.get_or_create(
            subject=math_subject,
            parent=algebra_unit,
            title='Linear Equations',
            defaults={
                'description': 'Solving and graphing linear equations in one and two variables',
                'topic_type': 'chapter',
                'difficulty': 'easy',
                'priority': 'high',
                'estimated_hours': 12,
                'learning_objectives': [
                    'Solve linear equations in one variable',
                    'Graph linear equations',
                    'Find slope and y-intercept',
                    'Write equations in various forms'
                ],
                'keywords': ['linear', 'slope', 'intercept', 'graphing'],
                'created_by': admin_user,
                'is_approved': True,
                'approved_by': admin_user,
            }
        )[0]
        
        # Quadratic Equations Chapter
        quadratic_equations = GlobalTopic.objects.get_or_create(
            subject=math_subject,
            parent=algebra_unit,
            title='Quadratic Equations',
            defaults={
                'description': 'Solving quadratic equations using various methods',
                'topic_type': 'chapter',
                'difficulty': 'medium',
                'priority': 'high',
                'estimated_hours': 15,
                'learning_objectives': [
                    'Solve quadratic equations by factoring',
                    'Use the quadratic formula',
                    'Complete the square',
                    'Graph parabolas'
                ],
                'keywords': ['quadratic', 'parabola', 'factoring', 'formula'],
                'created_by': admin_user,
                'is_approved': True,
                'approved_by': admin_user,
            }
        )[0]
        
        # Create Physics Subject
        physics_subject, created = GlobalSubject.objects.get_or_create(
            code='PHYS',
            defaults={
                'name': 'Physics',
                'description': 'Fundamental physics concepts covering mechanics, thermodynamics, and electromagnetism',
                'category': 'science',
                'level': 'high_school',
                'icon': '⚡',
                'color_code': '#EF4444',
                'created_by': admin_user,
                'approved_by': admin_user,
            }
        )
        
        # Create Physics Topics
        mechanics_unit = GlobalTopic.objects.get_or_create(
            subject=physics_subject,
            title='Classical Mechanics',
            defaults={
                'description': 'Study of motion, forces, and energy in classical physics',
                'topic_type': 'unit',
                'difficulty': 'medium',
                'priority': 'critical',
                'estimated_hours': 50,
                'learning_objectives': [
                    'Understand Newton\'s laws of motion',
                    'Apply concepts of force and acceleration',
                    'Calculate work, energy, and power',
                    'Analyze motion in one and two dimensions'
                ],
                'keywords': ['mechanics', 'newton', 'force', 'motion', 'energy'],
                'created_by': admin_user,
                'is_approved': True,
                'approved_by': admin_user,
            }
        )[0]
        
        # Kinematics Chapter
        kinematics = GlobalTopic.objects.get_or_create(
            subject=physics_subject,
            parent=mechanics_unit,
            title='Kinematics',
            defaults={
                'description': 'Study of motion without considering the forces that cause it',
                'topic_type': 'chapter',
                'difficulty': 'easy',
                'priority': 'high',
                'estimated_hours': 18,
                'learning_objectives': [
                    'Describe motion using position, velocity, and acceleration',
                    'Use kinematic equations to solve problems',
                    'Analyze projectile motion',
                    'Understand circular motion'
                ],
                'keywords': ['kinematics', 'velocity', 'acceleration', 'projectile'],
                'created_by': admin_user,
                'is_approved': True,
                'approved_by': admin_user,
            }
        )[0]
        
        # Create English Subject for competitive exams
        english_subject, created = GlobalSubject.objects.get_or_create(
            code='ENG',
            defaults={
                'name': 'English Language',
                'description': 'English language skills for competitive examinations',
                'category': 'language',
                'level': 'competitive',
                'icon': '📚',
                'color_code': '#10B981',
                'created_by': admin_user,
                'approved_by': admin_user,
            }
        )
        
        # Grammar Unit
        grammar_unit = GlobalTopic.objects.get_or_create(
            subject=english_subject,
            title='Grammar and Usage',
            defaults={
                'description': 'Essential grammar rules and proper usage for competitive exams',
                'topic_type': 'unit',
                'difficulty': 'medium',
                'priority': 'high',
                'estimated_hours': 25,
                'learning_objectives': [
                    'Master parts of speech',
                    'Understand tense usage',
                    'Apply rules of syntax and punctuation',
                    'Identify and correct common errors'
                ],
                'keywords': ['grammar', 'tense', 'syntax', 'punctuation'],
                'created_by': admin_user,
                'is_approved': True,
                'approved_by': admin_user,
            }
        )[0]
        
        # Create a sample template
        math_template, created = TopicImportTemplate.objects.get_or_create(
            name='High School Mathematics Standard',
            defaults={
                'description': 'Complete high school mathematics curriculum template',
                'template_type': 'standard',
                'source_subject': math_subject,
                'include_prerequisites': True,
                'include_subtopics': True,
                'max_depth_level': 4,
                'filter_by_difficulty': ['easy', 'medium'],
                'is_active': True,
                'is_public': True,
                'created_by': admin_user,
            }
        )
        
        if created:
            math_template.root_topics.add(algebra_unit)
        
        # Update usage counts for demonstration
        algebra_unit.usage_count = 15
        algebra_unit.save()
        
        linear_equations.usage_count = 12
        linear_equations.save()
        
        math_subject.popularity_score = 25
        math_subject.save()
        
        physics_subject.popularity_score = 18
        physics_subject.save()
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        
        # Print summary
        self.stdout.write(f'Created subjects: {GlobalSubject.objects.count()}')
        self.stdout.write(f'Created topics: {GlobalTopic.objects.count()}')
        self.stdout.write(f'Created templates: {TopicImportTemplate.objects.count()}')