#!/usr/bin/env python
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
django.setup()

from exams.models import Exam
from django.core import serializers

# Export all exams
exams = Exam.objects.all()
exam_data = []

for exam in exams:
    exam_info = {
        'name': exam.name,
        'description': exam.description,
        'category': exam.category,
        'exam_type': exam.exam_type,
        'difficulty_level': exam.difficulty_level,
        'target_audience': exam.target_audience,
        'language': exam.language,
        'state_specific': exam.state_specific,
        'tags': exam.tags,
        'year': exam.year,
        'is_active': exam.is_active,
        'is_featured': exam.is_featured,
        'created_at': exam.created_at.isoformat() if exam.created_at else None,
    }
    exam_data.append(exam_info)

# Save to JSON file
with open('exams_export.json', 'w') as f:
    json.dump(exam_data, f, indent=2, ensure_ascii=False)

print(f'Exported {len(exam_data)} exams to exams_export.json')