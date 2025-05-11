import pandas as pd
from django.core.management.base import BaseCommand
from ...models import Problem  # adjust import path as needed


class Command(BaseCommand):
    help = 'Import aptitude questions from an Excel file into the Problem model'

    def add_arguments(self, parser):
        parser.add_argument(
            'excel_path',
            type=str,
            help='Path to the Excel file containing aptitude questions'
        )

    def handle(self, *args, **options):
        excel_path = options['excel_path']
        try:
            df = pd.read_excel(excel_path)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading the Excel file: {e}"))
            return

        problems = []
        for _, row in df.iterrows():
            problem = Problem(
                question=row.get('question'),
                option1=row.get('option1'),
                option2=row.get('option2'),
                option3=row.get('option3'),
                option4=row.get('option4'),
                correct_option=int(row['correct_option']) if pd.notna(row['correct_option']) else None,
                is_active=row.get('is_active') if pd.notna(row.get('is_active')) else True,
                done=row.get('done') if pd.notna(row.get('done')) else False,
                answerurl=row.get('answerurl') if pd.notna(row.get('answerurl')) else None,
                companyname=row.get('companyname'),
                type=row.get('type'),
                test_id=int(row['test_id']) if pd.notna(row['test_id']) else None,
                questionimage=row.get('questionimage') if pd.notna(row.get('questionimage')) else None,
                )

            problems.append(problem)

        # Bulk create for performance
        Problem.objects.bulk_create(problems)
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {len(problems)} questions."))
