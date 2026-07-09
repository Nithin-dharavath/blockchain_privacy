from django.test import TestCase
from django.contrib.auth import get_user_model
from reports.forms import ReportGenerationForm, ReportScheduleForm, ReportTemplateForm
from reports.models import Report, ReportSchedule, ReportTemplate
from experiments.models import Experiment
from privacy_tools.models import PrivacyTechnique
from datasets.models import Dataset
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class TestReportGenerationForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="repuser", password="pass"
        )
        self.technique = PrivacyTechnique.objects.create(
            name="TEE",
            technique_type="trusted_execution",
            description="Test",
            algorithm_details="Test",
        )
        csv_file = SimpleUploadedFile(
            "rdata.csv", b"a,b\n1,2\n3,4", content_type="text/csv"
        )
        self.dataset = Dataset.objects.create(
            name="Rep Dataset",
            description="Test",
            dataset_type="custom",
            file=csv_file,
            uploaded_by=self.user,
            status='approved',
        )
        self.experiment = Experiment.objects.create(
            name="Rep Exp", user=self.user,
            dataset=self.dataset, privacy_technique=self.technique,
            status='completed',
        )

    def test_valid(self):
        form = ReportGenerationForm(
            data={
                'title': 'My Report',
                'report_type': 'single',
                'experiments': [self.experiment.pk],
                'file_format': 'pdf',
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_optional(self):
        form = ReportGenerationForm(
            data={
                'title': 'Minimal Report',
                'report_type': 'summary',
                'experiments': [self.experiment.pk],
                'file_format': 'csv',
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())


class TestReportScheduleForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="scheduser", password="pass"
        )

    def test_valid_daily(self):
        form = ReportScheduleForm(
            data={
                'name': 'Daily Report',
                'report_type': 'summary',
                'file_format': 'pdf',
                'schedule_frequency': 'daily',
                'is_active': True,
                'auto_generate': True,
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_valid_weekly(self):
        form = ReportScheduleForm(
            data={
                'name': 'Weekly Report',
                'report_type': 'single',
                'file_format': 'csv',
                'schedule_frequency': 'weekly',
                'schedule_day': 0,
                'is_active': True,
                'auto_generate': False,
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_valid_monthly(self):
        form = ReportScheduleForm(
            data={
                'name': 'Monthly Report',
                'report_type': 'comparison',
                'file_format': 'xlsx',
                'schedule_frequency': 'monthly',
                'schedule_day': 15,
                'is_active': False,
                'auto_generate': True,
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())


class TestReportTemplateForm(TestCase):
    def test_valid(self):
        form = ReportTemplateForm(data={
            'name': 'My Template',
            'description': 'A custom template',
            'is_public': True,
            'layout': '{"header_text": "Report"}',
        })
        self.assertTrue(form.is_valid())
