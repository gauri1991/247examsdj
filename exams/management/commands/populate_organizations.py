from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from exams.models import Organization, Exam, ExamMetadata
from datetime import datetime, date
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with top 10 Indian organizations and their exams'

    def handle(self, *args, **options):
        # Get or create a system user for creating organizations
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'System',
                'last_name': 'Admin',
                'role': 'admin'
            }
        )
        
        organizations_data = [
            {
                'name': 'Union Public Service Commission',
                'short_name': 'UPSC',
                'organization_type': 'government',
                'website': 'https://upsc.gov.in',
                'description': 'Constitutional body responsible for civil services recruitment in India',
                'email': 'contact@upsc.gov.in',
                'phone': '+91-11-23381125',
                'address': 'Dholpur House, Shahjahan Road, New Delhi - 110069',
                'exams': [
                    {
                        'name': 'Civil Services Examination (CSE)',
                        'category': 'Civil Services',
                        'year': 2024,
                        'description': 'Premier examination for recruitment to various civil services of India',
                        'metadata': {
                            'notification_date': '2024-02-14',
                            'form_start_date': '2024-02-14T10:00:00',
                            'form_end_date': '2024-03-05T18:00:00',
                            'exam_start_date': '2024-06-16',
                            'exam_end_date': '2024-06-16',
                            'min_age': 21,
                            'max_age': 32,
                            'fee_structure': {'general': 100, 'obc': 100, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['civil services', 'ias', 'ips', 'ifs', 'prelims', 'mains', 'interview']
                        }
                    },
                    {
                        'name': 'Combined Defence Services Examination (CDS)',
                        'category': 'Defence',
                        'year': 2024,
                        'description': 'Examination for recruitment to Indian Military Academy, Naval Academy, and Air Force Academy',
                        'metadata': {
                            'notification_date': '2024-08-21',
                            'form_start_date': '2024-08-21T10:00:00',
                            'form_end_date': '2024-09-10T18:00:00',
                            'exam_start_date': '2024-11-10',
                            'exam_end_date': '2024-11-10',
                            'min_age': 19,
                            'max_age': 25,
                            'fee_structure': {'general': 200, 'obc': 200, 'sc_st': 0, 'female': 0},
                            'tags': ['defence', 'ima', 'ina', 'afa', 'military', 'navy', 'air force']
                        }
                    },
                    {
                        'name': 'National Defence Academy & Naval Academy Examination (NDA & NA)',
                        'category': 'Defence',
                        'year': 2024,
                        'description': 'Examination for entry into NDA and Naval Academy',
                        'metadata': {
                            'min_age': 16,
                            'max_age': 19,
                            'fee_structure': {'general': 100, 'obc': 100, 'sc_st': 0},
                            'tags': ['nda', 'naval academy', 'defence', 'cadet']
                        }
                    },
                    {
                        'name': 'Central Armed Police Forces (Assistant Commandant) Examination',
                        'category': 'Police',
                        'year': 2024,
                        'description': 'Recruitment to CAPF as Assistant Commandant',
                        'metadata': {
                            'min_age': 20,
                            'max_age': 25,
                            'fee_structure': {'general': 200, 'obc': 200, 'sc_st': 0, 'female': 0},
                            'tags': ['capf', 'crpf', 'bsf', 'cisf', 'itbp', 'ssb', 'assistant commandant']
                        }
                    },
                    {
                        'name': 'Engineering Services Examination (ESE)',
                        'category': 'Engineering',
                        'year': 2024,
                        'description': 'Recruitment to Group A and Group B engineering services',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 30,
                            'fee_structure': {'general': 200, 'obc': 200, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['engineering services', 'ese', 'ies', 'technical', 'government']
                        }
                    },
                    {
                        'name': 'Indian Forest Service Examination (IFS)',
                        'category': 'Forest Service',
                        'year': 2024,
                        'description': 'Recruitment to Indian Forest Service',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 32,
                            'fee_structure': {'general': 100, 'obc': 100, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['forest service', 'ifs', 'environment', 'forestry']
                        }
                    }
                ]
            },
            {
                'name': 'Staff Selection Commission',
                'short_name': 'SSC',
                'organization_type': 'government',
                'website': 'https://ssc.nic.in',
                'description': 'Recruits staff for various ministries and departments of Government of India',
                'email': 'sscnic@ssc.nic.in',
                'phone': '+91-11-24365825',
                'address': 'Block No.12, CGO Complex, Lodhi Road, New Delhi - 110003',
                'exams': [
                    {
                        'name': 'Combined Graduate Level Examination (CGL)',
                        'category': 'Government Jobs',
                        'year': 2024,
                        'description': 'Recruitment to Group B and Group C posts in various ministries',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 32,
                            'fee_structure': {'general': 100, 'obc': 100, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['cgl', 'graduate level', 'group b', 'group c', 'government']
                        }
                    },
                    {
                        'name': 'Combined Higher Secondary Level Examination (CHSL)',
                        'category': 'Government Jobs',
                        'year': 2024,
                        'description': 'Recruitment to posts like LDC, JSA, PA, SA, DEO',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 27,
                            'fee_structure': {'general': 100, 'obc': 100, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['chsl', '12th pass', 'ldc', 'jsa', 'pa', 'sa', 'deo']
                        }
                    },
                    {
                        'name': 'Multi Tasking Staff (MTS) Examination',
                        'category': 'Government Jobs',
                        'year': 2024,
                        'description': 'Recruitment to Multi Tasking (Non-Technical) Staff positions',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 25,
                            'fee_structure': {'general': 100, 'obc': 100, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['mts', 'multi tasking', 'non-technical', '10th pass']
                        }
                    },
                    {
                        'name': 'Junior Engineer (JE) Examination',
                        'category': 'Engineering',
                        'year': 2024,
                        'description': 'Recruitment to Junior Engineer posts in various departments',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 32,
                            'fee_structure': {'general': 100, 'obc': 100, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['junior engineer', 'je', 'technical', 'engineering', 'diploma']
                        }
                    },
                    {
                        'name': 'Stenographer Grade C & D Examination',
                        'category': 'Government Jobs',
                        'year': 2024,
                        'description': 'Recruitment to Stenographer positions',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 30,
                            'fee_structure': {'general': 100, 'obc': 100, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['stenographer', 'typing', 'shorthand', 'grade c', 'grade d']
                        }
                    }
                ]
            },
            {
                'name': 'Railway Recruitment Board',
                'short_name': 'RRB',
                'organization_type': 'government',
                'website': 'https://www.rrbcdg.gov.in',
                'description': 'Conducts recruitment for Indian Railways',
                'email': 'rrbcdg@railnet.gov.in',
                'phone': '+91-11-23384159',
                'address': 'Rail Bhawan, Raisina Road, New Delhi - 110001',
                'exams': [
                    {
                        'name': 'Railway Recruitment Board NTPC (Non-Technical Popular Categories)',
                        'category': 'Railway',
                        'year': 2024,
                        'description': 'Recruitment to non-technical popular categories in Indian Railways',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 36,
                            'fee_structure': {'general': 500, 'obc': 250, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['rrb ntpc', 'railway', 'non-technical', 'graduate', 'undergraduate']
                        }
                    },
                    {
                        'name': 'Railway Recruitment Board JE (Junior Engineer)',
                        'category': 'Railway',
                        'year': 2024,
                        'description': 'Recruitment to Junior Engineer and allied posts',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 36,
                            'fee_structure': {'general': 500, 'obc': 250, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['rrb je', 'junior engineer', 'technical', 'railway', 'engineering']
                        }
                    },
                    {
                        'name': 'Railway Recruitment Board Group D',
                        'category': 'Railway',
                        'year': 2024,
                        'description': 'Recruitment to Level 1 posts in Indian Railways',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 36,
                            'fee_structure': {'general': 500, 'obc': 250, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['rrb group d', 'railway', 'level 1', '10th pass', 'helper']
                        }
                    },
                    {
                        'name': 'Assistant Loco Pilot (ALP) Examination',
                        'category': 'Railway',
                        'year': 2024,
                        'description': 'Recruitment to Assistant Loco Pilot and Technician posts',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 36,
                            'fee_structure': {'general': 500, 'obc': 250, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['alp', 'assistant loco pilot', 'technician', 'railway', 'technical']
                        }
                    },
                    {
                        'name': 'Railway Protection Force (RPF) Constable',
                        'category': 'Railway',
                        'year': 2024,
                        'description': 'Recruitment to RPF Constable and Sub-Inspector posts',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 25,
                            'fee_structure': {'general': 500, 'obc': 250, 'sc_st': 0, 'female': 0, 'pwd': 0},
                            'tags': ['rpf', 'constable', 'sub-inspector', 'railway protection', 'security']
                        }
                    }
                ]
            },
            {
                'name': 'Institute of Banking Personnel Selection',
                'short_name': 'IBPS',
                'organization_type': 'government',
                'website': 'https://www.ibps.in',
                'description': 'Conducts recruitment examinations for public sector banks',
                'email': 'complaints@ibps.in',
                'phone': '+91-22-26528000',
                'address': 'IBPS House, 90 Hari Nagar, New Delhi - 110064',
                'exams': [
                    {
                        'name': 'Probationary Officer (PO) Examination',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to Probationary Officer posts in public sector banks',
                        'metadata': {
                            'min_age': 20,
                            'max_age': 30,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['ibps po', 'probationary officer', 'banking', 'graduate', 'public sector']
                        }
                    },
                    {
                        'name': 'Clerk Examination',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to Clerical cadre in public sector banks',
                        'metadata': {
                            'min_age': 20,
                            'max_age': 28,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['ibps clerk', 'clerical', 'banking', 'graduate', 'public sector']
                        }
                    },
                    {
                        'name': 'Specialist Officer (SO) Examination',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to specialist officer posts in various fields',
                        'metadata': {
                            'min_age': 20,
                            'max_age': 30,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['ibps so', 'specialist officer', 'it', 'hr', 'marketing', 'agriculture']
                        }
                    },
                    {
                        'name': 'Regional Rural Bank (RRB) Officer Scale I',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to Officer Scale I in Regional Rural Banks',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 30,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['rrb', 'officer scale i', 'rural banking', 'graduate']
                        }
                    },
                    {
                        'name': 'Regional Rural Bank (RRB) Office Assistant',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to Office Assistant (Multipurpose) in RRBs',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 28,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['rrb', 'office assistant', 'multipurpose', 'rural banking']
                        }
                    }
                ]
            },
            {
                'name': 'State Bank of India',
                'short_name': 'SBI',
                'organization_type': 'psu',
                'website': 'https://sbi.co.in',
                'description': 'Largest public sector bank in India conducting its own recruitment',
                'email': 'customercare@sbi.co.in',
                'phone': '1800-1234',
                'address': 'Corporate Centre, MMTC-STC Building, 1, C-1, Block G, Bandra Kurla Complex, Bandra (East), Mumbai - 400051',
                'exams': [
                    {
                        'name': 'Probationary Officer (PO) Examination',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to PO positions in SBI',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 30,
                            'fee_structure': {'general': 750, 'obc': 750, 'sc_st': 125, 'pwd': 125},
                            'tags': ['sbi po', 'probationary officer', 'banking', 'graduate']
                        }
                    },
                    {
                        'name': 'Clerk (Junior Associate) Examination',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to Junior Associate positions',
                        'metadata': {
                            'min_age': 20,
                            'max_age': 28,
                            'fee_structure': {'general': 750, 'obc': 750, 'sc_st': 125, 'pwd': 125},
                            'tags': ['sbi clerk', 'junior associate', 'banking', 'graduate']
                        }
                    },
                    {
                        'name': 'Specialist Cadre Officer (SCO) Examination',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to specialist positions in various fields',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 35,
                            'fee_structure': {'general': 750, 'obc': 750, 'sc_st': 125, 'pwd': 125},
                            'tags': ['sbi sco', 'specialist cadre', 'it', 'law', 'economics', 'ca']
                        }
                    },
                    {
                        'name': 'Apprentice Examination',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to Apprentice positions',
                        'metadata': {
                            'min_age': 20,
                            'max_age': 28,
                            'fee_structure': {'general': 750, 'obc': 750, 'sc_st': 125, 'pwd': 125},
                            'tags': ['sbi apprentice', 'trainee', 'graduate']
                        }
                    },
                    {
                        'name': 'Circle Based Officer (CBO) Examination',
                        'category': 'Banking',
                        'year': 2024,
                        'description': 'Recruitment to Circle Based Officer positions',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 30,
                            'fee_structure': {'general': 750, 'obc': 750, 'sc_st': 125, 'pwd': 125},
                            'tags': ['sbi cbo', 'circle based officer', 'regional', 'graduate']
                        }
                    }
                ]
            },
            {
                'name': 'Central Board of Secondary Education',
                'short_name': 'CBSE',
                'organization_type': 'board',
                'website': 'https://cbse.gov.in',
                'description': 'National level board of education for public and private schools',
                'email': 'cbseinfo@yahoo.com',
                'phone': '+91-11-23212603',
                'address': 'Shiksha Kendra, 2, Community Centre, Preet Vihar, Delhi - 110301',
                'exams': [
                    {
                        'name': 'National Eligibility cum Entrance Test (NEET)',
                        'category': 'Medical',
                        'year': 2024,
                        'description': 'National level entrance exam for medical and dental courses',
                        'metadata': {
                            'min_age': 17,
                            'max_age': 25,
                            'fee_structure': {'general': 1700, 'obc': 1700, 'sc_st': 1000, 'pwd': 1000},
                            'tags': ['neet', 'medical', 'dental', 'mbbs', 'bds', 'entrance']
                        }
                    },
                    {
                        'name': 'Joint Entrance Examination (JEE) Main',
                        'category': 'Engineering',
                        'year': 2024,
                        'description': 'National level entrance exam for engineering courses',
                        'metadata': {
                            'min_age': 17,
                            'max_age': 25,
                            'fee_structure': {'general': 1000, 'obc': 1000, 'sc_st': 500, 'pwd': 500},
                            'tags': ['jee main', 'engineering', 'nit', 'iiit', 'entrance', 'b.tech']
                        }
                    },
                    {
                        'name': 'Central Teacher Eligibility Test (CTET)',
                        'category': 'Teaching',
                        'year': 2024,
                        'description': 'Eligibility test for teaching in central government schools',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 35,
                            'fee_structure': {'general': 1000, 'obc': 1000, 'sc_st': 500, 'pwd': 500},
                            'tags': ['ctet', 'teacher eligibility', 'primary', 'upper primary', 'teaching']
                        }
                    },
                    {
                        'name': 'National Talent Search Examination (NTSE)',
                        'category': 'Scholarship',
                        'year': 2024,
                        'description': 'National level scholarship examination for students',
                        'metadata': {
                            'fee_structure': {'general': 0, 'obc': 0, 'sc_st': 0},
                            'tags': ['ntse', 'scholarship', 'talent search', 'class 10']
                        }
                    },
                    {
                        'name': 'Kendriya Vidyalaya Sangathan (KVS) Teacher Recruitment',
                        'category': 'Teaching',
                        'year': 2024,
                        'description': 'Recruitment of teachers in Kendriya Vidyalayas',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 40,
                            'fee_structure': {'general': 1000, 'obc': 1000, 'sc_st': 500, 'pwd': 500},
                            'tags': ['kvs', 'kendriya vidyalaya', 'teacher', 'pgt', 'tgt', 'prt']
                        }
                    }
                ]
            },
            {
                'name': 'Life Insurance Corporation of India',
                'short_name': 'LIC',
                'organization_type': 'psu',
                'website': 'https://licindia.in',
                'description': 'Largest life insurance company in India',
                'email': 'customercare@licindia.com',
                'phone': '022-67819281',
                'address': 'Yogakshema Building, Jeevan Bima Marg, Mumbai - 400021',
                'exams': [
                    {
                        'name': 'Assistant Administrative Officer (AAO) Examination',
                        'category': 'Insurance',
                        'year': 2024,
                        'description': 'Recruitment to AAO positions in LIC',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 30,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['lic aao', 'assistant administrative officer', 'insurance', 'graduate']
                        }
                    },
                    {
                        'name': 'Assistant Development Officer (ADO) Examination',
                        'category': 'Insurance',
                        'year': 2024,
                        'description': 'Recruitment to ADO positions',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 30,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['lic ado', 'assistant development officer', 'insurance', 'marketing']
                        }
                    },
                    {
                        'name': 'Housing Finance Assistant (HFA) Examination',
                        'category': 'Finance',
                        'year': 2024,
                        'description': 'Recruitment to HFA positions in LIC Housing Finance',
                        'metadata': {
                            'min_age': 20,
                            'max_age': 28,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['lic hfa', 'housing finance', 'assistant', 'finance']
                        }
                    },
                    {
                        'name': 'Apprentice Development Officer (AppDO) Examination',
                        'category': 'Insurance',
                        'year': 2024,
                        'description': 'Recruitment to apprentice development officer positions',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 30,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['lic appdo', 'apprentice', 'development officer', 'insurance']
                        }
                    },
                    {
                        'name': 'Technical Assistant (Architect) Examination',
                        'category': 'Technical',
                        'year': 2024,
                        'description': 'Recruitment to technical assistant positions for architects',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 30,
                            'fee_structure': {'general': 850, 'obc': 850, 'sc_st': 175, 'pwd': 175},
                            'tags': ['lic technical assistant', 'architect', 'technical', 'professional']
                        }
                    }
                ]
            },
            {
                'name': 'National Testing Agency',
                'short_name': 'NTA',
                'organization_type': 'government',
                'website': 'https://nta.ac.in',
                'description': 'Premier testing organization for higher education entrance examinations',
                'email': 'info@nta.ac.in',
                'phone': '+91-11-40759000',
                'address': 'Ground Floor, CIET Building, Deshbandhu Gupta Road, Karol Bagh, New Delhi - 110005',
                'exams': [
                    {
                        'name': 'Joint Entrance Examination (JEE) Advanced',
                        'category': 'Engineering',
                        'year': 2024,
                        'description': 'Advanced level entrance exam for IITs',
                        'metadata': {
                            'min_age': 17,
                            'max_age': 25,
                            'fee_structure': {'general': 2800, 'obc': 2800, 'sc_st': 1400, 'pwd': 1400},
                            'tags': ['jee advanced', 'iit', 'engineering', 'entrance', 'advanced']
                        }
                    },
                    {
                        'name': 'Common University Entrance Test (CUET)',
                        'category': 'University Admission',
                        'year': 2024,
                        'description': 'Common entrance test for admission to central universities',
                        'metadata': {
                            'min_age': 17,
                            'max_age': 25,
                            'fee_structure': {'general': 650, 'obc': 650, 'sc_st': 325, 'pwd': 325},
                            'tags': ['cuet', 'university admission', 'central universities', 'undergraduate']
                        }
                    },
                    {
                        'name': 'Graduate Aptitude Test in Engineering (GATE)',
                        'category': 'Engineering',
                        'year': 2024,
                        'description': 'National level examination for postgraduate engineering admissions',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 35,
                            'fee_structure': {'general': 1850, 'obc': 1850, 'sc_st': 925, 'pwd': 925, 'female': 925},
                            'tags': ['gate', 'postgraduate', 'engineering', 'm.tech', 'phd', 'psu']
                        }
                    },
                    {
                        'name': 'National Eligibility Test (NET)',
                        'category': 'Teaching',
                        'year': 2024,
                        'description': 'Eligibility test for Assistant Professor and JRF',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 30,
                            'fee_structure': {'general': 1250, 'obc': 1250, 'sc_st': 650, 'pwd': 650},
                            'tags': ['ugc net', 'assistant professor', 'jrf', 'research', 'teaching']
                        }
                    },
                    {
                        'name': 'Common Management Admission Test (CMAT)',
                        'category': 'Management',
                        'year': 2024,
                        'description': 'National level test for admission to MBA/PGDM programs',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 35,
                            'fee_structure': {'general': 2000, 'obc': 2000, 'sc_st': 1000, 'pwd': 1000},
                            'tags': ['cmat', 'mba', 'pgdm', 'management', 'entrance']
                        }
                    }
                ]
            },
            {
                'name': 'All India Institute of Medical Sciences',
                'short_name': 'AIIMS',
                'organization_type': 'university',
                'website': 'https://aiims.edu',
                'description': 'Premier medical institute conducting entrance examinations',
                'email': 'registrar@aiims.ac.in',
                'phone': '+91-11-26588500',
                'address': 'Ansari Nagar, New Delhi - 110029',
                'exams': [
                    {
                        'name': 'AIIMS MBBS Entrance Examination',
                        'category': 'Medical',
                        'year': 2024,
                        'description': 'Entrance examination for MBBS admission in AIIMS',
                        'metadata': {
                            'min_age': 17,
                            'max_age': 25,
                            'fee_structure': {'general': 1600, 'obc': 1600, 'sc_st': 800, 'pwd': 800},
                            'tags': ['aiims mbbs', 'medical', 'entrance', 'undergraduate']
                        }
                    },
                    {
                        'name': 'AIIMS Nursing Entrance Examination',
                        'category': 'Nursing',
                        'year': 2024,
                        'description': 'Entrance examination for B.Sc Nursing programs',
                        'metadata': {
                            'min_age': 17,
                            'max_age': 25,
                            'fee_structure': {'general': 1500, 'obc': 1500, 'sc_st': 750, 'pwd': 750},
                            'tags': ['aiims nursing', 'b.sc nursing', 'nursing', 'healthcare']
                        }
                    },
                    {
                        'name': 'AIIMS PG Entrance Examination',
                        'category': 'Medical',
                        'year': 2024,
                        'description': 'Postgraduate medical entrance examination',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 35,
                            'fee_structure': {'general': 2500, 'obc': 2500, 'sc_st': 1250, 'pwd': 1250},
                            'tags': ['aiims pg', 'postgraduate', 'medical', 'md', 'ms', 'residency']
                        }
                    },
                    {
                        'name': 'AIIMS Fellowship Entrance Examination',
                        'category': 'Medical',
                        'year': 2024,
                        'description': 'Fellowship entrance examination for super-specialization',
                        'metadata': {
                            'min_age': 25,
                            'max_age': 40,
                            'fee_structure': {'general': 3000, 'obc': 3000, 'sc_st': 1500, 'pwd': 1500},
                            'tags': ['aiims fellowship', 'super specialization', 'dm', 'mch', 'fellowship']
                        }
                    },
                    {
                        'name': 'AIIMS Ph.D Entrance Examination',
                        'category': 'Research',
                        'year': 2024,
                        'description': 'Entrance examination for Ph.D programs',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 35,
                            'fee_structure': {'general': 2000, 'obc': 2000, 'sc_st': 1000, 'pwd': 1000},
                            'tags': ['aiims phd', 'research', 'doctorate', 'phd', 'medical research']
                        }
                    }
                ]
            },
            {
                'name': 'Food Corporation of India',
                'short_name': 'FCI',
                'organization_type': 'psu',
                'website': 'https://fci.gov.in',
                'description': 'Government corporation responsible for food security and distribution',
                'email': 'info@fci.gov.in',
                'phone': '+91-11-24368535',
                'address': '16-20, Barakhamba Lane, New Delhi - 110001',
                'exams': [
                    {
                        'name': 'Assistant General Manager (AGM) Examination',
                        'category': 'Management',
                        'year': 2024,
                        'description': 'Recruitment to AGM positions in various disciplines',
                        'metadata': {
                            'min_age': 21,
                            'max_age': 30,
                            'fee_structure': {'general': 1000, 'obc': 1000, 'sc_st': 0, 'pwd': 0},
                            'tags': ['fci agm', 'assistant general manager', 'management', 'general', 'technical']
                        }
                    },
                    {
                        'name': 'Junior Engineer (JE) Examination',
                        'category': 'Engineering',
                        'year': 2024,
                        'description': 'Recruitment to Junior Engineer posts',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 30,
                            'fee_structure': {'general': 1000, 'obc': 1000, 'sc_st': 0, 'pwd': 0},
                            'tags': ['fci je', 'junior engineer', 'civil', 'electrical', 'mechanical']
                        }
                    },
                    {
                        'name': 'Typist Examination',
                        'category': 'Clerical',
                        'year': 2024,
                        'description': 'Recruitment to Typist positions',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 27,
                            'fee_structure': {'general': 1000, 'obc': 1000, 'sc_st': 0, 'pwd': 0},
                            'tags': ['fci typist', 'typing', 'clerical', 'hindi', 'english']
                        }
                    },
                    {
                        'name': 'Steno Grade II Examination',
                        'category': 'Clerical',
                        'year': 2024,
                        'description': 'Recruitment to Stenographer Grade II positions',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 27,
                            'fee_structure': {'general': 1000, 'obc': 1000, 'sc_st': 0, 'pwd': 0},
                            'tags': ['fci steno', 'stenographer', 'shorthand', 'grade ii']
                        }
                    },
                    {
                        'name': 'Watchman Examination',
                        'category': 'Security',
                        'year': 2024,
                        'description': 'Recruitment to Watchman positions',
                        'metadata': {
                            'min_age': 18,
                            'max_age': 25,
                            'fee_structure': {'general': 1000, 'obc': 1000, 'sc_st': 0, 'pwd': 0},
                            'tags': ['fci watchman', 'security', 'guard', 'protection']
                        }
                    }
                ]
            }
        ]

        self.stdout.write('Starting to populate organizations and exams...')
        
        created_orgs = 0
        created_exams = 0
        
        for org_data in organizations_data:
            # Extract exam data before creating organization
            exams_data = org_data.pop('exams', [])
            
            # Create or get organization
            organization, org_created = Organization.objects.get_or_create(
                name=org_data['name'],
                defaults={
                    **org_data,
                    'created_by': admin_user
                }
            )
            
            if org_created:
                created_orgs += 1
                self.stdout.write(f'Created organization: {organization.name}')
            else:
                self.stdout.write(f'Organization already exists: {organization.name}')
            
            # Create exams for this organization
            for exam_data in exams_data:
                metadata = exam_data.pop('metadata', {})
                
                exam, exam_created = Exam.objects.get_or_create(
                    name=exam_data['name'],
                    organization=organization,
                    year=exam_data.get('year'),
                    defaults={
                        **exam_data,
                        'organization': organization,
                        'created_by': admin_user
                    }
                )
                
                if exam_created:
                    created_exams += 1
                    self.stdout.write(f'  Created exam: {exam.name}')
                    
                    # Create exam metadata if provided
                    if metadata:
                        # Convert date strings to date objects
                        date_fields = ['notification_date', 'admit_card_date', 'exam_start_date', 'exam_end_date', 'result_date']
                        datetime_fields = ['form_start_date', 'form_end_date', 'form_extended_date', 'fee_payment_last_date', 'correction_window_start', 'correction_window_end']
                        
                        for field in date_fields:
                            if field in metadata and metadata[field]:
                                try:
                                    metadata[field] = datetime.strptime(metadata[field], '%Y-%m-%d').date()
                                except:
                                    metadata[field] = None
                        
                        for field in datetime_fields:
                            if field in metadata and metadata[field]:
                                try:
                                    metadata[field] = datetime.strptime(metadata[field], '%Y-%m-%dT%H:%M:%S')
                                except:
                                    metadata[field] = None
                        
                        ExamMetadata.objects.create(
                            exam=exam,
                            **metadata
                        )
                        self.stdout.write(f'    Created metadata for: {exam.name}')
                else:
                    self.stdout.write(f'  Exam already exists: {exam.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with {created_orgs} organizations and {created_exams} exams!'
            )
        )