#!/usr/bin/env python
"""
Script to create comprehensive DCIO syllabus with hierarchical structure
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
sys.path.insert(0, '/home/gss/Documents/projects/dts/test_platform')
django.setup()

from exams.models import Exam, Syllabus, SyllabusNode
from django.contrib.auth import get_user_model

User = get_user_model()

def create_dcio_syllabus():
    """Create detailed DCIO syllabus structure"""
    
    # Get DCIO exam
    try:
        exam = Exam.objects.get(id='e37267b7-f69d-4272-b186-9e81600f6456')  # DCIO - Tech
        print(f"Found exam: {exam.name}")
    except Exam.DoesNotExist:
        print("DCIO exam not found!")
        return
    
    # Create or get syllabus
    syllabus, created = Syllabus.objects.get_or_create(
        exam=exam,
        defaults={
            'description': 'Comprehensive syllabus for Deputy Central Intelligence Officer (Technical) examination covering core engineering and technology subjects.',
            'version': '1.0',
            'estimated_hours': 200,
            'total_topics': 0,
            'is_active': True
        }
    )
    
    if created:
        print("Created new syllabus for DCIO exam")
    else:
        print("Using existing syllabus for DCIO exam")
        # Clear existing nodes if any
        SyllabusNode.objects.filter(syllabus=syllabus).delete()
        print("Cleared existing syllabus nodes")
    
    # Detailed syllabus structure
    syllabus_structure = {
        "Engineering Aptitude": {
            "order": 1,
            "estimated_hours": 15,
            "difficulty": "medium",
            "weightage": 10.0,
            "subtopics": {
                "Logical Reasoning": {
                    "order": 1,
                    "estimated_hours": 8,
                    "difficulty": "medium",
                    "weightage": 5.0,
                    "concepts": [
                        "Verbal Reasoning - Analogies, Classification, Series",
                        "Non-Verbal Reasoning - Pattern Recognition, Visual Series",
                        "Logical Deduction - Syllogisms, Statements and Conclusions",
                        "Blood Relations and Family Trees",
                        "Direction and Distance Problems",
                        "Ranking and Arrangement Problems"
                    ]
                },
                "Analytical Ability": {
                    "order": 2,
                    "estimated_hours": 7,
                    "difficulty": "medium",
                    "weightage": 5.0,
                    "concepts": [
                        "Data Interpretation - Tables, Graphs, Charts",
                        "Quantitative Aptitude - Number Systems, Percentages",
                        "Problem Solving Techniques",
                        "Critical Thinking and Decision Making",
                        "Coding-Decoding Problems",
                        "Mathematical Operations and BODMAS"
                    ]
                }
            }
        },
        "Electronic Devices and Circuits": {
            "order": 2,
            "estimated_hours": 18,
            "difficulty": "hard",
            "weightage": 12.0,
            "subtopics": {
                "Semiconductor Physics": {
                    "order": 1,
                    "estimated_hours": 6,
                    "difficulty": "hard",
                    "weightage": 4.0,
                    "concepts": [
                        "Crystal Structure and Energy Bands",
                        "Intrinsic and Extrinsic Semiconductors",
                        "P-N Junction Diodes - Formation and Characteristics",
                        "Zener Diodes and Special Purpose Diodes",
                        "Varactor and Tunnel Diodes",
                        "LED and Photodiodes"
                    ]
                },
                "Transistors": {
                    "order": 2,
                    "estimated_hours": 8,
                    "difficulty": "hard",
                    "weightage": 5.0,
                    "concepts": [
                        "BJT - Construction, Working and Characteristics",
                        "BJT Configurations - CB, CE, CC",
                        "BJT Biasing Techniques",
                        "Small Signal Analysis of BJT",
                        "JFET and MOSFET - Construction and Characteristics",
                        "CMOS Technology and Applications"
                    ]
                },
                "Amplifiers": {
                    "order": 3,
                    "estimated_hours": 4,
                    "difficulty": "medium",
                    "weightage": 3.0,
                    "concepts": [
                        "Single Stage Amplifiers",
                        "Multi-stage Amplifiers",
                        "Feedback in Amplifiers",
                        "Operational Amplifiers - Ideal and Practical",
                        "Op-Amp Applications",
                        "Frequency Response of Amplifiers"
                    ]
                }
            }
        },
        "Digital Electronics": {
            "order": 3,
            "estimated_hours": 16,
            "difficulty": "medium",
            "weightage": 10.0,
            "subtopics": {
                "Number Systems": {
                    "order": 1,
                    "estimated_hours": 3,
                    "difficulty": "easy",
                    "weightage": 2.0,
                    "concepts": [
                        "Binary, Octal, Decimal, Hexadecimal Systems",
                        "Base Conversions",
                        "1's and 2's Complement",
                        "Binary Arithmetic",
                        "BCD and Gray Codes",
                        "Error Detection and Correction Codes"
                    ]
                },
                "Boolean Algebra": {
                    "order": 2,
                    "estimated_hours": 4,
                    "difficulty": "medium",
                    "weightage": 3.0,
                    "concepts": [
                        "Boolean Laws and Theorems",
                        "Canonical Forms - SOP and POS",
                        "Karnaugh Maps",
                        "Quine-McCluskey Method",
                        "Logic Gates - AND, OR, NOT, NAND, NOR, XOR",
                        "Universal Gates"
                    ]
                },
                "Combinational Circuits": {
                    "order": 3,
                    "estimated_hours": 5,
                    "difficulty": "medium",
                    "weightage": 3.0,
                    "concepts": [
                        "Adders - Half and Full Adders",
                        "Subtractors and Comparators",
                        "Multiplexers and Demultiplexers",
                        "Encoders and Decoders",
                        "Priority Encoders",
                        "Code Converters"
                    ]
                },
                "Sequential Circuits": {
                    "order": 4,
                    "estimated_hours": 4,
                    "difficulty": "hard",
                    "weightage": 2.0,
                    "concepts": [
                        "Flip-Flops - SR, JK, D, T",
                        "Registers and Shift Registers",
                        "Counters - Synchronous and Asynchronous",
                        "State Machines and State Diagrams",
                        "Timing Analysis",
                        "Memory Elements"
                    ]
                }
            }
        },
        "Computer Programming and Data Structures": {
            "order": 4,
            "estimated_hours": 20,
            "difficulty": "medium",
            "weightage": 15.0,
            "subtopics": {
                "Programming Fundamentals": {
                    "order": 1,
                    "estimated_hours": 6,
                    "difficulty": "easy",
                    "weightage": 4.0,
                    "concepts": [
                        "Programming Paradigms",
                        "Variables, Data Types, and Operators",
                        "Control Structures - Loops and Conditionals",
                        "Functions and Recursion",
                        "Arrays and Pointers",
                        "Memory Management"
                    ]
                },
                "Data Structures": {
                    "order": 2,
                    "estimated_hours": 10,
                    "difficulty": "medium",
                    "weightage": 8.0,
                    "concepts": [
                        "Linear Data Structures - Arrays, Linked Lists",
                        "Stacks and Queues",
                        "Trees - Binary Trees, BST, AVL Trees",
                        "Graphs - Representation and Traversal",
                        "Hash Tables and Hashing",
                        "Priority Queues and Heaps"
                    ]
                },
                "Algorithms": {
                    "order": 3,
                    "estimated_hours": 4,
                    "difficulty": "hard",
                    "weightage": 3.0,
                    "concepts": [
                        "Sorting Algorithms",
                        "Searching Algorithms",
                        "Graph Algorithms - DFS, BFS, Dijkstra",
                        "Dynamic Programming",
                        "Greedy Algorithms",
                        "Algorithm Complexity Analysis"
                    ]
                }
            }
        },
        "Analog and Digital Communications": {
            "order": 5,
            "estimated_hours": 18,
            "difficulty": "hard",
            "weightage": 12.0,
            "subtopics": {
                "Analog Communication": {
                    "order": 1,
                    "estimated_hours": 9,
                    "difficulty": "hard",
                    "weightage": 6.0,
                    "concepts": [
                        "Amplitude Modulation - DSB, SSB, VSB",
                        "Frequency and Phase Modulation",
                        "Superheterodyne Receivers",
                        "Noise in Communication Systems",
                        "Signal-to-Noise Ratio",
                        "Analog-to-Digital Conversion"
                    ]
                },
                "Digital Communication": {
                    "order": 2,
                    "estimated_hours": 9,
                    "difficulty": "hard",
                    "weightage": 6.0,
                    "concepts": [
                        "Digital Modulation - ASK, FSK, PSK, QAM",
                        "Source and Channel Coding",
                        "Error Control Coding",
                        "Multiple Access Techniques - TDMA, FDMA, CDMA",
                        "Spread Spectrum Techniques",
                        "OFDM and Modern Modulation Schemes"
                    ]
                }
            }
        },
        "Microwave Engineering, RADAR Systems": {
            "order": 6,
            "estimated_hours": 16,
            "difficulty": "expert",
            "weightage": 10.0,
            "subtopics": {
                "Microwave Engineering": {
                    "order": 1,
                    "estimated_hours": 8,
                    "difficulty": "expert",
                    "weightage": 5.0,
                    "concepts": [
                        "Transmission Lines and Smith Chart",
                        "Waveguides and Cavity Resonators",
                        "Microwave Components - Couplers, Circulators",
                        "Microwave Antennas",
                        "S-Parameters and Network Analysis",
                        "Microwave Measurements"
                    ]
                },
                "RADAR Systems": {
                    "order": 2,
                    "estimated_hours": 8,
                    "difficulty": "expert",
                    "weightage": 5.0,
                    "concepts": [
                        "RADAR Principles and Range Equation",
                        "Pulse and CW RADAR",
                        "Doppler RADAR and MTI",
                        "RADAR Antennas and Beam Forming",
                        "Target Detection and Tracking",
                        "RADAR Signal Processing"
                    ]
                }
            }
        },
        "Satellite Communications": {
            "order": 7,
            "estimated_hours": 14,
            "difficulty": "hard",
            "weightage": 8.0,
            "subtopics": {
                "Satellite Systems": {
                    "order": 1,
                    "estimated_hours": 7,
                    "difficulty": "hard",
                    "weightage": 4.0,
                    "concepts": [
                        "Satellite Orbits - GEO, LEO, MEO",
                        "Satellite Subsystems",
                        "Launch and Tracking",
                        "Satellite Link Budget",
                        "Multiple Access in Satellites",
                        "Satellite Network Protocols"
                    ]
                },
                "Earth Station Technology": {
                    "order": 2,
                    "estimated_hours": 7,
                    "difficulty": "hard",
                    "weightage": 4.0,
                    "concepts": [
                        "Earth Station Components",
                        "Antenna Tracking Systems",
                        "Low Noise Amplifiers",
                        "Up and Down Converters",
                        "VSAT Technology",
                        "Satellite Internet and Broadcasting"
                    ]
                }
            }
        },
        "Signals and Systems, Digital Signal Processing": {
            "order": 8,
            "estimated_hours": 18,
            "difficulty": "hard",
            "weightage": 12.0,
            "subtopics": {
                "Signals and Systems": {
                    "order": 1,
                    "estimated_hours": 9,
                    "difficulty": "hard",
                    "weightage": 6.0,
                    "concepts": [
                        "Continuous and Discrete Time Signals",
                        "System Properties - Linearity, Time Invariance",
                        "Impulse Response and Convolution",
                        "Fourier Transform and Properties",
                        "Laplace Transform and Z-Transform",
                        "Transfer Functions and Frequency Response"
                    ]
                },
                "Digital Signal Processing": {
                    "order": 2,
                    "estimated_hours": 9,
                    "difficulty": "hard",
                    "weightage": 6.0,
                    "concepts": [
                        "Sampling and Quantization",
                        "DFT and FFT Algorithms",
                        "Digital Filter Design - FIR and IIR",
                        "Window Functions",
                        "Multirate Signal Processing",
                        "DSP Hardware and Implementation"
                    ]
                }
            }
        },
        "Computer Organization and Operating Systems": {
            "order": 9,
            "estimated_hours": 18,
            "difficulty": "medium",
            "weightage": 12.0,
            "subtopics": {
                "Computer Organization": {
                    "order": 1,
                    "estimated_hours": 9,
                    "difficulty": "medium",
                    "weightage": 6.0,
                    "concepts": [
                        "CPU Architecture and Instruction Sets",
                        "Memory Hierarchy - Cache, RAM, Storage",
                        "Input/Output Systems and Interrupts",
                        "Pipelining and Parallel Processing",
                        "RISC vs CISC Architectures",
                        "Performance Metrics and Benchmarking"
                    ]
                },
                "Operating Systems": {
                    "order": 2,
                    "estimated_hours": 9,
                    "difficulty": "medium",
                    "weightage": 6.0,
                    "concepts": [
                        "Process Management and Scheduling",
                        "Memory Management and Virtual Memory",
                        "File Systems and Storage Management",
                        "Deadlocks and Synchronization",
                        "Security and Protection Mechanisms",
                        "Distributed and Real-time Systems"
                    ]
                }
            }
        },
        "Computer Networks and Cyber Security": {
            "order": 10,
            "estimated_hours": 20,
            "difficulty": "hard",
            "weightage": 15.0,
            "subtopics": {
                "Network Fundamentals": {
                    "order": 1,
                    "estimated_hours": 8,
                    "difficulty": "medium",
                    "weightage": 6.0,
                    "concepts": [
                        "OSI and TCP/IP Model",
                        "Network Topologies and Protocols",
                        "Routing Algorithms and Protocols",
                        "Switching Techniques",
                        "Network Performance and QoS",
                        "Network Troubleshooting"
                    ]
                },
                "Cyber Security": {
                    "order": 2,
                    "estimated_hours": 12,
                    "difficulty": "hard",
                    "weightage": 9.0,
                    "concepts": [
                        "Cryptography - Symmetric and Asymmetric",
                        "Digital Signatures and PKI",
                        "Network Security Protocols - SSL/TLS, IPSec",
                        "Firewalls and Intrusion Detection",
                        "Malware Analysis and Prevention",
                        "Ethical Hacking and Penetration Testing",
                        "Security Standards and Compliance",
                        "Incident Response and Forensics"
                    ]
                }
            }
        },
        "Wireless Communications and Networking": {
            "order": 11,
            "estimated_hours": 16,
            "difficulty": "hard",
            "weightage": 10.0,
            "subtopics": {
                "Wireless Communication Systems": {
                    "order": 1,
                    "estimated_hours": 8,
                    "difficulty": "hard",
                    "weightage": 5.0,
                    "concepts": [
                        "Mobile Communication Principles",
                        "Cellular Systems - GSM, CDMA, LTE",
                        "5G Technology and mmWave",
                        "Antenna Systems for Mobile",
                        "Propagation Models and Path Loss",
                        "Multiple Input Multiple Output (MIMO)"
                    ]
                },
                "Wireless Networking": {
                    "order": 2,
                    "estimated_hours": 8,
                    "difficulty": "medium",
                    "weightage": 5.0,
                    "concepts": [
                        "WiFi Standards and Protocols",
                        "Bluetooth and Personal Area Networks",
                        "Zigbee and Sensor Networks",
                        "Mobile Ad-hoc Networks (MANET)",
                        "Wireless Security Protocols",
                        "Quality of Service in Wireless Networks"
                    ]
                }
            }
        },
        "Artificial Intelligence": {
            "order": 12,
            "estimated_hours": 16,
            "difficulty": "medium",
            "weightage": 10.0,
            "subtopics": {
                "AI Fundamentals": {
                    "order": 1,
                    "estimated_hours": 8,
                    "difficulty": "medium",
                    "weightage": 5.0,
                    "concepts": [
                        "Search Algorithms - BFS, DFS, A*",
                        "Knowledge Representation",
                        "Expert Systems and Rule-based Systems",
                        "Uncertainty and Probabilistic Reasoning",
                        "Planning and Decision Making",
                        "Natural Language Processing Basics"
                    ]
                },
                "Machine Learning": {
                    "order": 2,
                    "estimated_hours": 8,
                    "difficulty": "medium",
                    "weightage": 5.0,
                    "concepts": [
                        "Supervised Learning Algorithms",
                        "Unsupervised Learning - Clustering",
                        "Neural Networks and Deep Learning",
                        "Feature Selection and Engineering",
                        "Model Evaluation and Validation",
                        "AI Applications in Security and Intelligence"
                    ]
                }
            }
        },
        "Internet of Things": {
            "order": 13,
            "estimated_hours": 12,
            "difficulty": "easy",
            "weightage": 8.0,
            "subtopics": {
                "IoT Architecture": {
                    "order": 1,
                    "estimated_hours": 6,
                    "difficulty": "easy",
                    "weightage": 4.0,
                    "concepts": [
                        "IoT System Architecture and Components",
                        "Sensors and Actuators",
                        "Microcontrollers and Single Board Computers",
                        "Communication Protocols - MQTT, CoAP",
                        "Cloud Integration and Edge Computing",
                        "IoT Data Analytics"
                    ]
                },
                "IoT Applications and Security": {
                    "order": 2,
                    "estimated_hours": 6,
                    "difficulty": "medium",
                    "weightage": 4.0,
                    "concepts": [
                        "Smart Cities and Industrial IoT",
                        "Healthcare and Agricultural IoT",
                        "IoT Security Challenges",
                        "Device Authentication and Encryption",
                        "Privacy and Data Protection",
                        "IoT Standards and Protocols"
                    ]
                }
            }
        }
    }
    
    total_topics = 0
    
    # Create main units
    for unit_name, unit_data in syllabus_structure.items():
        print(f"Creating unit: {unit_name}")
        
        unit_node = SyllabusNode.objects.create(
            syllabus=syllabus,
            parent=None,
            title=unit_name,
            description=f"Comprehensive coverage of {unit_name} for DCIO technical examination",
            node_type='unit',
            order=unit_data['order'],
            estimated_hours=unit_data['estimated_hours'],
            difficulty=unit_data['difficulty'],
            weightage=unit_data['weightage'],
            is_optional=False,
            is_active=True,
            tags=[unit_name.lower().replace(' ', '_')]
        )
        total_topics += 1
        
        # Create subtopics
        if 'subtopics' in unit_data:
            for subtopic_name, subtopic_data in unit_data['subtopics'].items():
                print(f"  Creating subtopic: {subtopic_name}")
                
                subtopic_node = SyllabusNode.objects.create(
                    syllabus=syllabus,
                    parent=unit_node,
                    title=subtopic_name,
                    description=f"Detailed study of {subtopic_name} within {unit_name}",
                    node_type='chapter',
                    order=subtopic_data['order'],
                    estimated_hours=subtopic_data['estimated_hours'],
                    difficulty=subtopic_data['difficulty'],
                    weightage=subtopic_data['weightage'],
                    is_optional=False,
                    is_active=True,
                    tags=[subtopic_name.lower().replace(' ', '_')]
                )
                total_topics += 1
                
                # Create concepts
                if 'concepts' in subtopic_data:
                    for idx, concept in enumerate(subtopic_data['concepts'], 1):
                        print(f"    Creating concept: {concept[:50]}...")
                        
                        concept_node = SyllabusNode.objects.create(
                            syllabus=syllabus,
                            parent=subtopic_node,
                            title=concept,
                            description=f"Study and understand {concept}",
                            node_type='concept',
                            order=idx,
                            estimated_hours=round(subtopic_data['estimated_hours'] / len(subtopic_data['concepts']), 1),
                            difficulty=subtopic_data['difficulty'],
                            weightage=round(subtopic_data['weightage'] / len(subtopic_data['concepts']), 2),
                            is_optional=False,
                            is_active=True,
                            tags=[concept.lower().replace(' ', '_').replace('-', '_')[:10]]
                        )
                        total_topics += 1
    
    # Update syllabus total topics
    syllabus.total_topics = total_topics
    syllabus.save()
    
    print(f"\n✅ Successfully created DCIO syllabus with {total_topics} topics!")
    print(f"📚 Syllabus structure: 13 Units → 26 Chapters → {total_topics-39} Concepts")
    print(f"⏱️  Total estimated study hours: 200")
    print(f"🎯 Exam: {exam.name}")
    return syllabus

if __name__ == "__main__":
    create_dcio_syllabus()