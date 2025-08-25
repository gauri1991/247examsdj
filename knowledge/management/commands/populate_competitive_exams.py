from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from knowledge.models import GlobalSubject, GlobalTopic
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate comprehensive Indian competitive exam subjects and topics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating comprehensive Indian competitive exam taxonomy...'))
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        
        # UPSC Civil Services Subjects
        self.create_upsc_subjects(admin_user)
        
        # SSC Subjects
        self.create_ssc_subjects(admin_user)
        
        # Banking Exam Subjects
        self.create_banking_subjects(admin_user)
        
        # Railway Exam Subjects
        self.create_railway_subjects(admin_user)
        
        # Defense Exam Subjects
        self.create_defense_subjects(admin_user)
        
        # State PSC Subjects
        self.create_state_psc_subjects(admin_user)
        
        # Professional Exams
        self.create_professional_subjects(admin_user)
        
        self.stdout.write(self.style.SUCCESS(f'Created {GlobalSubject.objects.count()} subjects and {GlobalTopic.objects.count()} topics'))

    def create_upsc_subjects(self, admin_user):
        """Create UPSC Civil Services subjects"""
        
        # UPSC General Studies Papers
        upsc_gs1 = self.create_subject('UPSC_GS1', 'General Studies Paper 1', 
            'Indian Heritage, Culture, History, Geography', 'general_knowledge', 'competitive',
            '🏛️', '#8B5A2B', admin_user)
        
        upsc_gs2 = self.create_subject('UPSC_GS2', 'General Studies Paper 2',
            'Governance, Constitution, Polity, Social Justice, International Relations', 'social_science', 'competitive',
            '⚖️', '#1E40AF', admin_user)
            
        upsc_gs3 = self.create_subject('UPSC_GS3', 'General Studies Paper 3',
            'Technology, Economic Development, Biodiversity, Environment, Security', 'science', 'competitive', 
            '🔬', '#059669', admin_user)
            
        upsc_gs4 = self.create_subject('UPSC_GS4', 'General Studies Paper 4',
            'Ethics, Integrity and Aptitude', 'general_knowledge', 'competitive',
            '🧭', '#7C2D12', admin_user)
            
        # UPSC Optional Subjects
        upsc_history = self.create_subject('UPSC_HIST', 'History (Optional)',
            'Ancient, Medieval and Modern History of India and World', 'social_science', 'competitive',
            '📜', '#92400E', admin_user)
            
        upsc_geography = self.create_subject('UPSC_GEO', 'Geography (Optional)', 
            'Physical, Human and Economic Geography', 'social_science', 'competitive',
            '🌍', '#065F46', admin_user)
            
        upsc_pub_admin = self.create_subject('UPSC_PUBAD', 'Public Administration (Optional)',
            'Public Administration Theories and Practices', 'social_science', 'competitive',
            '🏢', '#374151', admin_user)
            
        # Create GS1 Topics
        self.create_topics_for_upsc_gs1(upsc_gs1, admin_user)
        self.create_topics_for_upsc_gs2(upsc_gs2, admin_user)
        self.create_topics_for_upsc_gs3(upsc_gs3, admin_user)
        
    def create_ssc_subjects(self, admin_user):
        """Create SSC exam subjects"""
        
        ssc_reasoning = self.create_subject('SSC_REASON', 'Reasoning Ability',
            'Logical and Analytical Reasoning for SSC Exams', 'general_knowledge', 'competitive',
            '🧠', '#7C3AED', admin_user)
            
        ssc_quant = self.create_subject('SSC_QUANT', 'Quantitative Aptitude', 
            'Mathematics and Numerical Ability for SSC', 'mathematics', 'competitive',
            '🔢', '#DC2626', admin_user)
            
        ssc_english = self.create_subject('SSC_ENG', 'English Comprehension',
            'English Language and Comprehension for SSC', 'language', 'competitive',
            '📖', '#059669', admin_user)
            
        ssc_gk = self.create_subject('SSC_GK', 'General Awareness',
            'General Knowledge and Current Affairs', 'general_knowledge', 'competitive',
            '🌐', '#EA580C', admin_user)
            
        # Create SSC Topics
        self.create_topics_for_ssc_reasoning(ssc_reasoning, admin_user)
        self.create_topics_for_ssc_quant(ssc_quant, admin_user)
        
    def create_banking_subjects(self, admin_user):
        """Create Banking exam subjects"""
        
        bank_reasoning = self.create_subject('BANK_REASON', 'Reasoning Ability (Banking)',
            'Logical Reasoning for Banking Exams', 'general_knowledge', 'competitive',
            '💭', '#6366F1', admin_user)
            
        bank_quant = self.create_subject('BANK_QUANT', 'Quantitative Aptitude (Banking)',
            'Mathematical Ability for Banking Sector', 'mathematics', 'competitive', 
            '💰', '#10B981', admin_user)
            
        bank_english = self.create_subject('BANK_ENG', 'English Language (Banking)',
            'English Communication for Banking', 'language', 'competitive',
            '💬', '#3B82F6', admin_user)
            
        bank_ga = self.create_subject('BANK_GA', 'General Awareness (Banking)',
            'Banking and Financial Awareness', 'commerce', 'competitive',
            '🏦', '#F59E0B', admin_user)
            
        bank_computer = self.create_subject('BANK_COMP', 'Computer Knowledge (Banking)',
            'Computer Awareness for Banking Sector', 'computer_science', 'competitive',
            '💻', '#8B5CF6', admin_user)
            
    def create_railway_subjects(self, admin_user):
        """Create Railway exam subjects"""
        
        railway_math = self.create_subject('RLY_MATH', 'Mathematics (Railway)',
            'Mathematical Ability for Railway Recruitment', 'mathematics', 'competitive',
            '🚂', '#EF4444', admin_user)
            
        railway_reasoning = self.create_subject('RLY_REASON', 'Reasoning (Railway)', 
            'Logical Reasoning for Railway Exams', 'general_knowledge', 'competitive',
            '🛤️', '#8B5A2B', admin_user)
            
        railway_gk = self.create_subject('RLY_GK', 'General Knowledge (Railway)',
            'Current Affairs and Railway Knowledge', 'general_knowledge', 'competitive',
            '📰', '#059669', admin_user)
            
        railway_tech = self.create_subject('RLY_TECH', 'Technical Knowledge (Railway)',
            'Engineering and Technical Subjects for Railways', 'engineering', 'competitive',
            '⚙️', '#374151', admin_user)
            
    def create_defense_subjects(self, admin_user):
        """Create Defense exam subjects"""
        
        nda_math = self.create_subject('NDA_MATH', 'Mathematics (NDA)', 
            'Mathematics for National Defence Academy', 'mathematics', 'competitive',
            '🎯', '#DC2626', admin_user)
            
        nda_gat = self.create_subject('NDA_GAT', 'General Ability Test (NDA)',
            'English and General Knowledge for NDA', 'general_knowledge', 'competitive', 
            '🛡️', '#1E40AF', admin_user)
            
        cds_english = self.create_subject('CDS_ENG', 'English (CDS)',
            'English Language for Combined Defence Services', 'language', 'competitive',
            '📚', '#059669', admin_user)
            
        cds_gk = self.create_subject('CDS_GK', 'General Knowledge (CDS)', 
            'General Awareness for CDS Examination', 'general_knowledge', 'competitive',
            '🌟', '#7C2D12', admin_user)
            
        afcat_reasoning = self.create_subject('AFCAT_REASON', 'Reasoning (AFCAT)',
            'Logical and Verbal Reasoning for Air Force', 'general_knowledge', 'competitive',
            '✈️', '#3B82F6', admin_user)
            
    def create_state_psc_subjects(self, admin_user):
        """Create State PSC subjects"""
        
        state_prelims = self.create_subject('STATE_PRELIMS', 'State PSC Prelims',
            'General Studies for State Public Service Commissions', 'general_knowledge', 'competitive',
            '🏛️', '#92400E', admin_user)
            
        state_mains = self.create_subject('STATE_MAINS', 'State PSC Mains', 
            'Descriptive Papers for State Civil Services', 'social_science', 'competitive',
            '✍️', '#065F46', admin_user)
            
        state_regional = self.create_subject('STATE_REGIONAL', 'Regional Language',
            'State Regional Language Papers', 'language', 'competitive',
            '🗣️', '#7C3AED', admin_user)
            
    def create_professional_subjects(self, admin_user):
        """Create Professional exam subjects"""
        
        ca_accounts = self.create_subject('CA_ACC', 'Chartered Accountancy',
            'Accounting, Auditing, Taxation for CA', 'commerce', 'professional',
            '📊', '#F59E0B', admin_user)
            
        cs_law = self.create_subject('CS_LAW', 'Company Secretary',
            'Corporate Laws and Governance', 'commerce', 'professional', 
            '⚖️', '#374151', admin_user)
            
        cma_cost = self.create_subject('CMA_COST', 'Cost & Management Accountancy',
            'Cost Accounting and Financial Management', 'commerce', 'professional',
            '💹', '#10B981', admin_user)
            
    def create_subject(self, code, name, description, category, level, icon, color, admin_user):
        """Helper method to create subject"""
        subject, created = GlobalSubject.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'category': category,
                'level': level,
                'icon': icon,
                'color_code': color,
                'created_by': admin_user,
                'approved_by': admin_user,
                'is_featured': True,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'Created subject: {code} - {name}')
        return subject
        
    def create_topic(self, subject, title, description, parent=None, topic_type='chapter', 
                    difficulty='medium', priority='high', hours=10, objectives=None, 
                    keywords=None, admin_user=None):
        """Helper method to create topic"""
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
            }
        )
        return topic
        
    def create_topics_for_upsc_gs1(self, subject, admin_user):
        """Create comprehensive topics for UPSC GS1"""
        
        # Ancient History Unit
        ancient_history = self.create_topic(subject, 'Ancient Indian History', 
            'Comprehensive study of ancient Indian civilization, culture and history',
            topic_type='unit', difficulty='medium', priority='critical', hours=40,
            objectives=[
                'Understand Indus Valley Civilization',
                'Study Vedic period and literature', 
                'Analyze rise of Buddhism and Jainism',
                'Examine Mauryan and Gupta periods'
            ],
            keywords=['ancient', 'indus', 'vedic', 'mauryan', 'gupta'], admin_user=admin_user)
            
        # Indus Valley subtopics
        self.create_topic(subject, 'Indus Valley Civilization',
            'Harappan civilization - urban planning, trade, decline',
            parent=ancient_history, topic_type='chapter', difficulty='medium', hours=8,
            objectives=['Understand Harappan city planning', 'Analyze trade networks', 'Examine reasons for decline'],
            keywords=['harappa', 'mohenjodaro', 'urban', 'trade'], admin_user=admin_user)
            
        self.create_topic(subject, 'Vedic Period', 
            'Early and Later Vedic periods - society, religion, literature',
            parent=ancient_history, topic_type='chapter', difficulty='medium', hours=10,
            objectives=['Study Vedic literature', 'Understand social structure', 'Analyze religious practices'],
            keywords=['vedas', 'rig', 'society', 'religion'], admin_user=admin_user)
            
        # Medieval History Unit  
        medieval_history = self.create_topic(subject, 'Medieval Indian History',
            'Delhi Sultanate, Mughal Empire and regional kingdoms',
            topic_type='unit', difficulty='hard', priority='critical', hours=50,
            objectives=[
                'Study Delhi Sultanate administration',
                'Analyze Mughal empire expansion',
                'Understand cultural synthesis',
                'Examine art and architecture'
            ],
            keywords=['delhi', 'sultanate', 'mughal', 'akbar', 'architecture'], admin_user=admin_user)
            
        # Modern History Unit
        modern_history = self.create_topic(subject, 'Modern Indian History',
            'British colonial rule, freedom struggle and independence',
            topic_type='unit', difficulty='hard', priority='critical', hours=60,
            objectives=[
                'Analyze colonial economic policies',
                'Study freedom movement phases', 
                'Understand role of leaders',
                'Examine partition and independence'
            ],
            keywords=['british', 'colonial', 'freedom', 'gandhi', 'independence'], admin_user=admin_user)
            
        # Geography Unit
        geography = self.create_topic(subject, 'Indian Geography',
            'Physical features, climate, natural resources of India',
            topic_type='unit', difficulty='medium', priority='high', hours=35,
            objectives=[
                'Understand physical divisions',
                'Study climate patterns',
                'Analyze natural resources',
                'Examine environmental issues'
            ],
            keywords=['mountains', 'rivers', 'climate', 'resources'], admin_user=admin_user)
            
    def create_topics_for_upsc_gs2(self, subject, admin_user):
        """Create topics for UPSC GS2"""
        
        # Constitution and Polity
        polity = self.create_topic(subject, 'Indian Constitution and Polity',
            'Constitutional framework, institutions and governance',
            topic_type='unit', difficulty='hard', priority='critical', hours=50,
            objectives=[
                'Understand constitutional provisions',
                'Study institutional framework',
                'Analyze federal structure',
                'Examine fundamental rights and duties'
            ],
            keywords=['constitution', 'parliament', 'judiciary', 'federalism'], admin_user=admin_user)
            
        # International Relations
        ir = self.create_topic(subject, 'International Relations',
            'India\'s foreign policy and global relations', 
            topic_type='unit', difficulty='hard', priority='high', hours=30,
            objectives=[
                'Understand foreign policy principles',
                'Study bilateral relations',
                'Analyze multilateral engagements',
                'Examine global issues'
            ],
            keywords=['foreign', 'policy', 'bilateral', 'multilateral'], admin_user=admin_user)
            
    def create_topics_for_upsc_gs3(self, subject, admin_user):
        """Create topics for UPSC GS3"""
        
        # Economics
        economics = self.create_topic(subject, 'Economic Development',
            'Indian economy, planning, reforms and growth',
            topic_type='unit', difficulty='hard', priority='critical', hours=45,
            objectives=[
                'Understand economic planning',
                'Study liberalization reforms', 
                'Analyze growth patterns',
                'Examine current challenges'
            ],
            keywords=['economy', 'planning', 'reforms', 'growth'], admin_user=admin_user)
            
        # Science and Technology
        science_tech = self.create_topic(subject, 'Science and Technology',
            'Scientific developments and technological applications',
            topic_type='unit', difficulty='medium', priority='high', hours=25,
            objectives=[
                'Study recent scientific advances',
                'Understand technology applications',
                'Analyze innovation policy',
                'Examine space and nuclear programs'
            ],
            keywords=['science', 'technology', 'innovation', 'space'], admin_user=admin_user)
            
    def create_topics_for_ssc_reasoning(self, subject, admin_user):
        """Create topics for SSC Reasoning"""
        
        # Verbal Reasoning
        verbal = self.create_topic(subject, 'Verbal Reasoning',
            'Word-based logical reasoning questions',
            topic_type='unit', difficulty='easy', priority='high', hours=20,
            objectives=[
                'Master analogy questions',
                'Understand classification',
                'Study coding-decoding',
                'Practice direction sense'
            ],
            keywords=['analogy', 'classification', 'coding', 'direction'], admin_user=admin_user)
            
        # Non-Verbal Reasoning  
        non_verbal = self.create_topic(subject, 'Non-Verbal Reasoning',
            'Pattern and figure-based reasoning',
            topic_type='unit', difficulty='medium', priority='high', hours=25,
            objectives=[
                'Understand pattern recognition',
                'Study figure series',
                'Practice mirror images',
                'Master paper folding'
            ],
            keywords=['pattern', 'figures', 'mirror', 'folding'], admin_user=admin_user)
            
    def create_topics_for_ssc_quant(self, subject, admin_user):
        """Create topics for SSC Quantitative Aptitude"""
        
        # Number System
        numbers = self.create_topic(subject, 'Number System',
            'Fundamental concepts of numbers and their properties',
            topic_type='unit', difficulty='easy', priority='critical', hours=15,
            objectives=[
                'Understand number properties',
                'Study divisibility rules',
                'Practice HCF and LCM', 
                'Master percentage calculations'
            ],
            keywords=['numbers', 'divisibility', 'hcf', 'lcm'], admin_user=admin_user)
            
        # Algebra
        algebra = self.create_topic(subject, 'Algebra',
            'Linear equations, quadratic equations and functions',
            topic_type='unit', difficulty='medium', priority='high', hours=20,
            objectives=[
                'Solve linear equations',
                'Understand quadratic equations',
                'Study functions and graphs',
                'Practice word problems'
            ],
            keywords=['equations', 'quadratic', 'functions', 'graphs'], admin_user=admin_user)