#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
django.setup()

from exams.models import Exam

print(f'Total exams: {Exam.objects.count()}')
print('\nSample exams:')
for exam in Exam.objects.all()[:15]:
    print(f'- {exam.name} (Category: {exam.category}, Type: {exam.exam_type})')

print('\nCategories breakdown:')
categories = {}
for exam in Exam.objects.all():
    cat = exam.category or 'none'
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in sorted(categories.items()):
    print(f'  {cat}: {count}')

print('\nExam types breakdown:')
exam_types = {}
for exam in Exam.objects.all():
    et = exam.exam_type or 'none'
    exam_types[et] = exam_types.get(et, 0) + 1

for et, count in sorted(exam_types.items()):
    print(f'  {et}: {count}')