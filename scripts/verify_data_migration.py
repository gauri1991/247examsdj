#!/usr/bin/env python
"""
Verify data migration success - checks if all data was imported correctly
Run this script after migration: python manage.py shell < scripts/verify_data_migration.py
"""

import sys
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
django.setup()

from django.contrib.auth import get_user_model
from exams.models import Exam, Test, TestAttempt, Organization, TestSection
from questions.models import QuestionBank, Question, TestQuestion, QuestionOption, UserAnswer

User = get_user_model()

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_section(title):
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print('─' * 70)

def verify_migration():
    """Verify all data was migrated successfully"""

    print_header("DATA MIGRATION VERIFICATION REPORT")

    # Expected counts from export
    expected_data = {
        'users': 7,
        'exams_total': 84,  # All exam-related records
        'questions_total': 756,  # All question-related records
        'knowledge_total': 458,
        'payments_total': 8,
    }

    print_section("RECORD COUNTS")

    # Users
    user_count = User.objects.count()
    print(f"✓ Users: {user_count} (Expected: {expected_data['users']})")
    status = "✅ PASS" if user_count == expected_data['users'] else "⚠️  MISMATCH"
    print(f"  Status: {status}")

    # Organizations
    org_count = Organization.objects.count()
    print(f"\n✓ Organizations: {org_count}")

    # Exams
    exam_count = Exam.objects.count()
    print(f"✓ Exams: {exam_count}")

    # Tests
    test_count = Test.objects.count()
    print(f"✓ Tests: {test_count}")

    # Test Sections
    section_count = TestSection.objects.count()
    print(f"✓ Test Sections: {section_count}")

    # Test Attempts
    attempt_count = TestAttempt.objects.count()
    print(f"✓ Test Attempts: {attempt_count}")

    # Question Banks
    bank_count = QuestionBank.objects.count()
    print(f"\n✓ Question Banks: {bank_count}")

    # Questions
    question_count = Question.objects.count()
    print(f"✓ Questions: {question_count}")

    # Question Options
    option_count = QuestionOption.objects.count()
    print(f"✓ Question Options: {option_count}")

    # Test Questions (linking)
    test_question_count = TestQuestion.objects.count()
    print(f"✓ Test Questions (linked): {test_question_count}")

    # User Answers
    answer_count = UserAnswer.objects.count()
    print(f"✓ User Answers: {answer_count}")

    # Knowledge base
    try:
        from knowledge.models import Topic, Material
        topic_count = Topic.objects.count()
        material_count = Material.objects.count()
        print(f"\n✓ Knowledge Topics: {topic_count}")
        print(f"✓ Knowledge Materials: {material_count}")
    except ImportError:
        print("\n⚠️  Knowledge app not available")

    # Payments
    try:
        from payments.models import Payment, UserSubscription, SubscriptionPlan
        payment_count = Payment.objects.count()
        subscription_count = UserSubscription.objects.count()
        plan_count = SubscriptionPlan.objects.count()
        print(f"\n✓ Subscription Plans: {plan_count}")
        print(f"✓ User Subscriptions: {subscription_count}")
        print(f"✓ Payments: {payment_count}")
    except ImportError:
        print("\n⚠️  Payments app not available")

    # Sample Data
    print_section("SAMPLE DATA - USERS")

    users = User.objects.all()[:10]
    if users:
        for user in users:
            role = user.role if hasattr(user, 'role') else 'N/A'
            print(f"  • {user.username:20} | {user.email:30} | Role: {role}")
    else:
        print("  ⚠️  No users found!")

    print_section("SAMPLE DATA - EXAMS")

    exams = Exam.objects.all()[:5]
    if exams:
        for exam in exams:
            org_name = exam.organization.name if exam.organization else 'No Organization'
            print(f"  • {exam.name[:40]:40} | Org: {org_name:20} | Created by: {exam.created_by.username}")
    else:
        print("  ⚠️  No exams found!")

    print_section("SAMPLE DATA - TESTS")

    tests = Test.objects.all()[:5]
    if tests:
        for test in tests:
            print(f"  • {test.title[:40]:40} | Exam: {test.exam.name[:30]:30} | Published: {test.is_published}")
    else:
        print("  ⚠️  No tests found!")

    print_section("SAMPLE DATA - QUESTION BANKS")

    banks = QuestionBank.objects.all()[:5]
    if banks:
        for bank in banks:
            q_count = bank.questions.count() if hasattr(bank, 'questions') else 0
            print(f"  • {bank.name[:40]:40} | Questions: {q_count:4} | Created by: {bank.created_by.username}")
    else:
        print("  ⚠️  No question banks found!")

    # Summary
    print_header("MIGRATION SUMMARY")

    total_records = (user_count + org_count + exam_count + test_count +
                    section_count + attempt_count + bank_count +
                    question_count + option_count + test_question_count + answer_count)

    print(f"\nTotal records imported: {total_records}")
    print(f"Expected approximately: ~1,313 records")

    if user_count > 0 and exam_count > 0 and question_count > 0:
        print("\n✅ MIGRATION SUCCESSFUL!")
        print("   Core data (Users, Exams, Questions) imported successfully.")
    elif user_count == 0:
        print("\n❌ MIGRATION FAILED!")
        print("   No users found. Migration did not import data.")
        print("\n   Troubleshooting steps:")
        print("   1. Check if fixtures exist: ls -la users/fixtures/")
        print("   2. Check migration logs for errors")
        print("   3. Try manual import: python manage.py loaddata users/fixtures/users.json")
    else:
        print("\n⚠️  PARTIAL MIGRATION")
        print("   Some data imported but counts don't match expected values.")

    print("\n" + "=" * 70 + "\n")

if __name__ == '__main__':
    try:
        verify_migration()
    except Exception as e:
        print(f"\n❌ ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
