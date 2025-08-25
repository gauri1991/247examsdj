from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from knowledge.models import GlobalSubject, GlobalTopic

User = get_user_model()


class Command(BaseCommand):
    help = 'Build deeper topic hierarchies with subtopics and concepts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Building deeper topic hierarchies...'))
        
        admin_user = User.objects.get(username='admin')
        
        # Build hierarchies for key subjects
        self.build_upsc_gs1_hierarchy(admin_user)
        self.build_mathematics_hierarchy(admin_user)
        self.build_physics_hierarchy(admin_user)
        self.build_ssc_reasoning_hierarchy(admin_user)
        self.build_banking_hierarchy(admin_user)
        
        self.stdout.write(self.style.SUCCESS(f'Built hierarchies. Total topics: {GlobalTopic.objects.count()}'))

    def create_topic(self, subject, title, description, parent=None, topic_type='topic', 
                    difficulty='medium', priority='medium', hours=5, objectives=None, 
                    keywords=None, admin_user=None, order=0):
        """Helper method to create topic with hierarchy"""
        if objectives is None:
            objectives = []
        if keywords is None:
            keywords = []
            
        topic, created = GlobalTopic.objects.get_or_create(
            subject=subject,
            title=title,
            parent=parent,
            defaults={
                'description': description,
                'topic_type': topic_type,
                'difficulty': difficulty,
                'priority': priority,
                'estimated_hours': hours,
                'learning_objectives': objectives,
                'keywords': keywords,
                'created_by': admin_user,
                'is_approved': True,
                'approved_by': admin_user,
                'is_template': True,
                'order': order,
            }
        )
        if created:
            self.stdout.write(f'  Created {topic_type}: {title} (Level {topic.depth_level})')
        return topic

    def build_upsc_gs1_hierarchy(self, admin_user):
        """Build detailed UPSC GS1 topic hierarchy"""
        self.stdout.write('Building UPSC GS1 hierarchy...')
        
        try:
            subject = GlobalSubject.objects.get(code='UPSC_GS1')
            
            # Get existing Ancient History unit
            ancient_history = GlobalTopic.objects.get(subject=subject, title='Ancient Indian History')
            
            # Build Indus Valley detailed hierarchy
            indus_valley = GlobalTopic.objects.get(subject=subject, title='Indus Valley Civilization', parent=ancient_history)
            
            # Indus Valley subtopics
            self.create_topic(subject, 'Harappan Cities', 
                'Major Harappan cities - Harappa, Mohenjodaro, Dholavira',
                parent=indus_valley, topic_type='subtopic', difficulty='easy', hours=3,
                objectives=['Identify major Harappan sites', 'Compare city layouts'],
                keywords=['harappa', 'mohenjodaro', 'dholavira'], admin_user=admin_user, order=1)
                
            self.create_topic(subject, 'Harappan Society and Economy',
                'Social structure, occupations, and trade networks', 
                parent=indus_valley, topic_type='subtopic', difficulty='medium', hours=4,
                objectives=['Understand social hierarchy', 'Analyze trade patterns'],
                keywords=['society', 'trade', 'occupations'], admin_user=admin_user, order=2)
                
            self.create_topic(subject, 'Harappan Art and Culture',
                'Pottery, seals, sculptures and cultural practices',
                parent=indus_valley, topic_type='subtopic', difficulty='medium', hours=3,
                objectives=['Study Harappan art forms', 'Analyze cultural symbols'],
                keywords=['pottery', 'seals', 'art'], admin_user=admin_user, order=3)
                
            self.create_topic(subject, 'Decline of Harappan Civilization',
                'Theories and causes behind the decline',
                parent=indus_valley, topic_type='subtopic', difficulty='hard', hours=2,
                objectives=['Evaluate decline theories', 'Understand environmental factors'],
                keywords=['decline', 'theories', 'environmental'], admin_user=admin_user, order=4)
                
            # Build Vedic Period detailed hierarchy
            vedic_period = GlobalTopic.objects.get(subject=subject, title='Vedic Period', parent=ancient_history)
            
            # Early Vedic Period
            early_vedic = self.create_topic(subject, 'Early Vedic Period (1500-1000 BCE)',
                'Rig Vedic society, economy and religious practices',
                parent=vedic_period, topic_type='subtopic', difficulty='medium', hours=5,
                objectives=['Study Rig Vedic hymns', 'Understand tribal society'],
                keywords=['rigveda', 'tribal', 'society'], admin_user=admin_user, order=1)
                
            # Early Vedic concepts
            self.create_topic(subject, 'Rig Vedic Deities',
                'Major gods - Indra, Agni, Varuna, Soma',
                parent=early_vedic, topic_type='concept', difficulty='easy', hours=2,
                objectives=['Identify major deities', 'Understand their significance'],
                keywords=['indra', 'agni', 'varuna'], admin_user=admin_user, order=1)
                
            self.create_topic(subject, 'Rig Vedic Social Structure', 
                'Varna system emergence and tribal organization',
                parent=early_vedic, topic_type='concept', difficulty='medium', hours=2,
                objectives=['Analyze social hierarchy', 'Study tribal structure'],
                keywords=['varna', 'tribal', 'social'], admin_user=admin_user, order=2)
                
            # Later Vedic Period
            later_vedic = self.create_topic(subject, 'Later Vedic Period (1000-600 BCE)',
                'Expansion, agriculture, and complex society',
                parent=vedic_period, topic_type='subtopic', difficulty='medium', hours=6,
                objectives=['Study territorial expansion', 'Understand agricultural practices'],
                keywords=['expansion', 'agriculture', 'society'], admin_user=admin_user, order=2)
                
            # Later Vedic concepts
            self.create_topic(subject, 'Later Vedic Literature',
                'Sama, Yajur, Atharva Vedas and Brahmanas',
                parent=later_vedic, topic_type='concept', difficulty='medium', hours=2,
                objectives=['Study different Vedas', 'Understand Brahmanic literature'],
                keywords=['samaveda', 'yajurveda', 'brahmanas'], admin_user=admin_user, order=1)
                
            self.create_topic(subject, 'Later Vedic Polity',
                'Kingdom formation and administrative system',
                parent=later_vedic, topic_type='concept', difficulty='hard', hours=2,
                objectives=['Understand state formation', 'Study administrative structure'],
                keywords=['kingdom', 'administration', 'polity'], admin_user=admin_user, order=2)
                
        except GlobalSubject.DoesNotExist:
            self.stdout.write('UPSC_GS1 subject not found, skipping hierarchy build')
        except GlobalTopic.DoesNotExist:
            self.stdout.write('Required parent topics not found for UPSC_GS1')

    def build_mathematics_hierarchy(self, admin_user):
        """Build detailed Mathematics hierarchy"""
        self.stdout.write('Building Mathematics hierarchy...')
        
        try:
            # Find existing math subjects
            math_subjects = GlobalSubject.objects.filter(category='mathematics')
            
            for subject in math_subjects[:2]:  # Process first 2 math subjects
                self.stdout.write(f'Processing {subject.name}...')
                
                # Create Algebra unit if not exists
                algebra_unit, created = GlobalTopic.objects.get_or_create(
                    subject=subject,
                    title='Algebra',
                    defaults={
                        'description': 'Fundamental algebraic concepts and operations',
                        'topic_type': 'unit',
                        'difficulty': 'medium',
                        'priority': 'critical',
                        'estimated_hours': 40,
                        'created_by': admin_user,
                        'is_approved': True,
                        'approved_by': admin_user,
                    }
                )
                
                # Linear Equations Chapter
                linear_eq = self.create_topic(subject, 'Linear Equations',
                    'Solving equations with one variable',
                    parent=algebra_unit, topic_type='chapter', difficulty='easy', hours=10,
                    objectives=['Solve linear equations', 'Apply to word problems'],
                    keywords=['linear', 'equations', 'variable'], admin_user=admin_user, order=1)
                    
                # Linear Equations subtopics
                self.create_topic(subject, 'One Variable Linear Equations',
                    'ax + b = 0 type equations',
                    parent=linear_eq, topic_type='subtopic', difficulty='easy', hours=3,
                    objectives=['Solve simple linear equations'],
                    keywords=['one', 'variable', 'simple'], admin_user=admin_user, order=1)
                    
                self.create_topic(subject, 'Linear Equations with Fractions',
                    'Equations involving fractions and decimals', 
                    parent=linear_eq, topic_type='subtopic', difficulty='medium', hours=4,
                    objectives=['Handle fractions in equations'],
                    keywords=['fractions', 'decimals'], admin_user=admin_user, order=2)
                    
                self.create_topic(subject, 'Word Problems on Linear Equations',
                    'Real-world applications of linear equations',
                    parent=linear_eq, topic_type='subtopic', difficulty='medium', hours=3,
                    objectives=['Apply equations to real problems'],
                    keywords=['word', 'problems', 'applications'], admin_user=admin_user, order=3)
                    
                # Quadratic Equations Chapter
                quadratic_eq = self.create_topic(subject, 'Quadratic Equations',
                    'ax² + bx + c = 0 equations and applications',
                    parent=algebra_unit, topic_type='chapter', difficulty='medium', hours=15,
                    objectives=['Solve quadratic equations', 'Understand discriminant'],
                    keywords=['quadratic', 'parabola', 'discriminant'], admin_user=admin_user, order=2)
                    
                # Quadratic subtopics
                self.create_topic(subject, 'Factorization Method',
                    'Solving by factoring quadratic expressions',
                    parent=quadratic_eq, topic_type='subtopic', difficulty='easy', hours=4,
                    objectives=['Factor quadratic expressions'],
                    keywords=['factoring', 'factors'], admin_user=admin_user, order=1)
                    
                self.create_topic(subject, 'Quadratic Formula',
                    'Using the quadratic formula to solve equations',
                    parent=quadratic_eq, topic_type='subtopic', difficulty='medium', hours=5,
                    objectives=['Apply quadratic formula', 'Calculate discriminant'],
                    keywords=['formula', 'discriminant'], admin_user=admin_user, order=2)
                    
                self.create_topic(subject, 'Completing the Square',
                    'Method of completing the square',
                    parent=quadratic_eq, topic_type='subtopic', difficulty='hard', hours=4,
                    objectives=['Complete the square method'],
                    keywords=['completing', 'square'], admin_user=admin_user, order=3)
                    
                self.create_topic(subject, 'Applications of Quadratic Equations',
                    'Real-world problems using quadratic equations',
                    parent=quadratic_eq, topic_type='subtopic', difficulty='medium', hours=2,
                    objectives=['Apply to practical problems'],
                    keywords=['applications', 'problems'], admin_user=admin_user, order=4)
                    
        except Exception as e:
            self.stdout.write(f'Error building mathematics hierarchy: {e}')

    def build_physics_hierarchy(self, admin_user):
        """Build detailed Physics hierarchy"""
        self.stdout.write('Building Physics hierarchy...')
        
        try:
            physics_subjects = GlobalSubject.objects.filter(category='science', name__icontains='Physics')
            
            for subject in physics_subjects[:1]:  # Process first physics subject
                self.stdout.write(f'Processing {subject.name}...')
                
                # Mechanics Unit
                mechanics, created = GlobalTopic.objects.get_or_create(
                    subject=subject,
                    title='Classical Mechanics',
                    defaults={
                        'description': 'Study of motion, forces, and energy',
                        'topic_type': 'unit',
                        'difficulty': 'medium',
                        'priority': 'critical',
                        'estimated_hours': 50,
                        'created_by': admin_user,
                        'is_approved': True,
                        'approved_by': admin_user,
                    }
                )
                
                # Kinematics Chapter
                kinematics = self.create_topic(subject, 'Kinematics',
                    'Study of motion without considering forces',
                    parent=mechanics, topic_type='chapter', difficulty='medium', hours=15,
                    objectives=['Describe motion using equations', 'Analyze projectile motion'],
                    keywords=['motion', 'velocity', 'acceleration'], admin_user=admin_user, order=1)
                    
                # Motion in One Dimension
                one_d_motion = self.create_topic(subject, 'Motion in One Dimension',
                    'Linear motion along a straight line',
                    parent=kinematics, topic_type='subtopic', difficulty='easy', hours=5,
                    objectives=['Calculate displacement and velocity'],
                    keywords=['displacement', 'velocity'], admin_user=admin_user, order=1)
                    
                self.create_topic(subject, 'Uniform Motion',
                    'Motion with constant velocity',
                    parent=one_d_motion, topic_type='concept', difficulty='easy', hours=2,
                    objectives=['Understand uniform motion'],
                    keywords=['uniform', 'constant'], admin_user=admin_user, order=1)
                    
                self.create_topic(subject, 'Uniformly Accelerated Motion', 
                    'Motion with constant acceleration',
                    parent=one_d_motion, topic_type='concept', difficulty='medium', hours=3,
                    objectives=['Use kinematic equations'],
                    keywords=['acceleration', 'equations'], admin_user=admin_user, order=2)
                    
                # Motion in Two Dimensions
                two_d_motion = self.create_topic(subject, 'Motion in Two Dimensions',
                    'Projectile and circular motion',
                    parent=kinematics, topic_type='subtopic', difficulty='hard', hours=6,
                    objectives=['Analyze projectile trajectories'],
                    keywords=['projectile', 'trajectory'], admin_user=admin_user, order=2)
                    
                self.create_topic(subject, 'Projectile Motion',
                    'Motion under gravity in two dimensions',
                    parent=two_d_motion, topic_type='concept', difficulty='hard', hours=4,
                    objectives=['Calculate range and height'],
                    keywords=['projectile', 'gravity'], admin_user=admin_user, order=1)
                    
        except Exception as e:
            self.stdout.write(f'Error building physics hierarchy: {e}')

    def build_ssc_reasoning_hierarchy(self, admin_user):
        """Build detailed SSC Reasoning hierarchy"""
        self.stdout.write('Building SSC Reasoning hierarchy...')
        
        try:
            subject = GlobalSubject.objects.get(code='SSC_REASON')
            
            # Verbal Reasoning Unit
            verbal_unit = GlobalTopic.objects.get_or_create(
                subject=subject,
                title='Verbal Reasoning',
                defaults={
                    'description': 'Word-based logical reasoning',
                    'topic_type': 'unit',
                    'difficulty': 'medium',
                    'priority': 'critical',
                    'estimated_hours': 25,
                    'created_by': admin_user,
                    'is_approved': True,
                    'approved_by': admin_user,
                }
            )[0]
            
            # Analogy Chapter
            analogy = self.create_topic(subject, 'Analogy',
                'Finding relationships between words and concepts',
                parent=verbal_unit, topic_type='chapter', difficulty='easy', hours=6,
                objectives=['Identify word relationships', 'Solve analogy questions'],
                keywords=['analogy', 'relationship', 'words'], admin_user=admin_user, order=1)
                
            # Analogy subtopics
            self.create_topic(subject, 'Word Analogy',
                'Relationship between words based on meaning',
                parent=analogy, topic_type='subtopic', difficulty='easy', hours=2,
                objectives=['Find word relationships'],
                keywords=['word', 'meaning'], admin_user=admin_user, order=1)
                
            self.create_topic(subject, 'Number Analogy',
                'Mathematical relationships between numbers',
                parent=analogy, topic_type='subtopic', difficulty='medium', hours=2,
                objectives=['Find number patterns'],
                keywords=['number', 'pattern'], admin_user=admin_user, order=2)
                
            self.create_topic(subject, 'Letter Analogy',
                'Alphabetical and positional relationships',
                parent=analogy, topic_type='subtopic', difficulty='medium', hours=2,
                objectives=['Understand letter positions'],
                keywords=['letter', 'alphabet'], admin_user=admin_user, order=3)
                
            # Classification Chapter
            classification = self.create_topic(subject, 'Classification',
                'Grouping items based on common properties',
                parent=verbal_unit, topic_type='chapter', difficulty='easy', hours=5,
                objectives=['Identify odd one out', 'Group similar items'],
                keywords=['classification', 'grouping'], admin_user=admin_user, order=2)
                
            self.create_topic(subject, 'Word Classification',
                'Classify words based on meaning or category',
                parent=classification, topic_type='subtopic', difficulty='easy', hours=2,
                objectives=['Find odd word out'],
                keywords=['word', 'category'], admin_user=admin_user, order=1)
                
            self.create_topic(subject, 'Number Classification',
                'Classify numbers based on properties',
                parent=classification, topic_type='subtopic', difficulty='easy', hours=2,
                objectives=['Find odd number out'],
                keywords=['number', 'properties'], admin_user=admin_user, order=2)
                
            # Coding-Decoding Chapter
            coding = self.create_topic(subject, 'Coding-Decoding',
                'Pattern-based coding and decoding of words',
                parent=verbal_unit, topic_type='chapter', difficulty='medium', hours=7,
                objectives=['Understand coding patterns', 'Decode messages'],
                keywords=['coding', 'decoding', 'pattern'], admin_user=admin_user, order=3)
                
            self.create_topic(subject, 'Letter Shift Coding',
                'Shifting letters by fixed positions',
                parent=coding, topic_type='subtopic', difficulty='easy', hours=2,
                objectives=['Apply letter shifting rules'],
                keywords=['shift', 'position'], admin_user=admin_user, order=1)
                
            self.create_topic(subject, 'Substitution Coding',
                'Substituting letters or words with symbols',
                parent=coding, topic_type='subtopic', difficulty='medium', hours=3,
                objectives=['Decode substitution patterns'],
                keywords=['substitution', 'symbols'], admin_user=admin_user, order=2)
                
        except GlobalSubject.DoesNotExist:
            self.stdout.write('SSC_REASON subject not found')
        except Exception as e:
            self.stdout.write(f'Error building SSC reasoning hierarchy: {e}')

    def build_banking_hierarchy(self, admin_user):
        """Build detailed Banking hierarchy"""
        self.stdout.write('Building Banking hierarchy...')
        
        try:
            subject = GlobalSubject.objects.get(code='BANK_GA')
            
            # Banking Awareness Unit
            banking_unit = GlobalTopic.objects.get_or_create(
                subject=subject,
                title='Banking Awareness',
                defaults={
                    'description': 'Comprehensive banking sector knowledge',
                    'topic_type': 'unit',
                    'difficulty': 'medium',
                    'priority': 'critical',
                    'estimated_hours': 30,
                    'created_by': admin_user,
                    'is_approved': True,
                    'approved_by': admin_user,
                }
            )[0]
            
            # Indian Banking System
            banking_system = self.create_topic(subject, 'Indian Banking System',
                'Structure and functioning of Indian banking system',
                parent=banking_unit, topic_type='chapter', difficulty='medium', hours=10,
                objectives=['Understand banking structure', 'Know major banks'],
                keywords=['banking', 'system', 'structure'], admin_user=admin_user, order=1)
                
            # Banking system subtopics
            self.create_topic(subject, 'Reserve Bank of India (RBI)',
                'Central bank functions and monetary policy',
                parent=banking_system, topic_type='subtopic', difficulty='medium', hours=3,
                objectives=['Understand RBI functions', 'Know monetary policy tools'],
                keywords=['rbi', 'central', 'monetary'], admin_user=admin_user, order=1)
                
            self.create_topic(subject, 'Commercial Banks',
                'Public and private sector commercial banks',
                parent=banking_system, topic_type='subtopic', difficulty='easy', hours=3,
                objectives=['Classify commercial banks', 'Know major banks'],
                keywords=['commercial', 'public', 'private'], admin_user=admin_user, order=2)
                
            self.create_topic(subject, 'Cooperative Banks',
                'Structure and functions of cooperative banking',
                parent=banking_system, topic_type='subtopic', difficulty='medium', hours=2,
                objectives=['Understand cooperative structure'],
                keywords=['cooperative', 'rural'], admin_user=admin_user, order=3)
                
            self.create_topic(subject, 'Development Banks',
                'NABARD, SIDBI and other development financial institutions',
                parent=banking_system, topic_type='subtopic', difficulty='medium', hours=2,
                objectives=['Know development banks', 'Understand their roles'],
                keywords=['development', 'nabard', 'sidbi'], admin_user=admin_user, order=4)
                
        except GlobalSubject.DoesNotExist:
            self.stdout.write('BANK_GA subject not found')
        except Exception as e:
            self.stdout.write(f'Error building banking hierarchy: {e}')