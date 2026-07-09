import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from privacy_platform.test_utils import (
    create_user, create_technique, create_dataset_csv,
    create_completed_experiment, create_report,
    create_report_template, create_report_schedule, create_report_share,
)
from reports.models import Report, ReportSchedule, ReportTemplate, ReportShare


class ReportListViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="reportlistuser", password="testpass123")

    def test_list_requires_login(self):
        response = self.client.get(reverse("reports:list"))
        self.assertNotEqual(response.status_code, 200)

    def test_list_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_list.html")

    def test_list_shows_user_reports_only(self):
        other = create_user(username="otherrep", password="testpass123")
        create_report(self.user)
        create_report(other)
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:list"))
        self.assertEqual(len(response.context["reports"]), 1)


class ReportGenerateViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="regenuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_completed_experiment(
            self.user, self.technique, self.dataset,
        )

    def test_generate_requires_login(self):
        response = self.client.get(reverse("reports:generate"))
        self.assertNotEqual(response.status_code, 200)

    def test_get_generate_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:generate"))
        self.assertEqual(response.status_code, 200)

    @patch("reports.views.generate_report_file")
    def test_post_generate_creates_report(self, mock_gen_file):
        mock_gen_file.return_value = None
        self.client.force_login(self.user)
        response = self.client.post(reverse("reports:generate"), {
            "title": "Test Report",
            "report_type": "single",
            "file_format": "csv",
            "experiments": [self.experiment.pk],
        })
        report = Report.objects.get(user=self.user)
        self.assertRedirects(response, reverse("reports:detail", args=[report.pk]))
        mock_gen_file.assert_called_once()


class ReportDetailViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="repdetuser", password="testpass123")
        self.report = create_report(self.user)

    def test_detail_requires_login(self):
        response = self.client.get(reverse("reports:detail", args=[self.report.pk]))
        self.assertNotEqual(response.status_code, 200)

    def test_detail_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:detail", args=[self.report.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_detail.html")

    def test_detail_404_for_wrong_user(self):
        other = create_user(username="otherdet", password="testpass123")
        self.client.force_login(other)
        response = self.client.get(reverse("reports:detail", args=[self.report.pk]))
        self.assertEqual(response.status_code, 404)


class ReportDownloadViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="repdluser", password="testpass123")
        self.report = create_report(self.user)

    def test_download_without_file_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:download", args=[self.report.pk]))
        self.assertRedirects(response, reverse("reports:detail", args=[self.report.pk]))


class ReportDeleteViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="repdeluser", password="testpass123")
        self.report = create_report(self.user)

    def test_delete_get_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:delete", args=[self.report.pk]))
        self.assertEqual(response.status_code, 200)

    def test_delete_post_deletes(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("reports:delete", args=[self.report.pk]))
        self.assertRedirects(response, reverse("reports:list"))
        self.assertEqual(Report.objects.count(), 0)


# ── Schedule Views ──────────────────────────────────────────────

class ScheduleListViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="schluser", password="testpass123")

    def test_schedule_list_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:schedule_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_schedule_list.html")


class ScheduleCreateViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="schlcreate", password="testpass123")

    def test_schedule_create_get_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:schedule_create"))
        self.assertEqual(response.status_code, 200)

    def test_schedule_create_post_creates(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("reports:schedule_create"), {
            "name": "Daily Report",
            "report_type": "summary",
            "file_format": "pdf",
            "schedule_frequency": "daily",
        })
        schedule = ReportSchedule.objects.get(user=self.user)
        self.assertRedirects(response, reverse("reports:schedule_detail",
                                                args=[schedule.pk]))


class ScheduleDetailViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="schldet", password="testpass123")
        self.schedule = create_report_schedule(self.user)

    def test_schedule_detail_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("reports:schedule_detail", args=[self.schedule.pk]),
        )
        self.assertEqual(response.status_code, 200)


class ScheduleEditViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="schledit", password="testpass123")
        self.schedule = create_report_schedule(self.user)

    def test_schedule_edit_get_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("reports:schedule_edit", args=[self.schedule.pk]),
        )
        self.assertEqual(response.status_code, 200)

    def test_schedule_edit_post_updates(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("reports:schedule_edit", args=[self.schedule.pk]),
            {
                "name": "Updated Schedule",
                "report_type": "summary",
                "file_format": "pdf",
                "schedule_frequency": "weekly",
                "schedule_day": 1,
            },
        )
        self.assertRedirects(response, reverse("reports:schedule_detail",
                                                args=[self.schedule.pk]))
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.name, "Updated Schedule")


class ScheduleToggleViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="schltoggle", password="testpass123")
        self.schedule = create_report_schedule(self.user)

    def test_schedule_toggle(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("reports:schedule_toggle", args=[self.schedule.pk]),
        )
        self.assertRedirects(response, reverse("reports:schedule_detail",
                                                args=[self.schedule.pk]))
        self.schedule.refresh_from_db()
        self.assertFalse(self.schedule.is_active)


class ScheduleDeleteViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="schldel", password="testpass123")
        self.schedule = create_report_schedule(self.user)

    def test_schedule_delete(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("reports:schedule_delete", args=[self.schedule.pk]),
        )
        self.assertRedirects(response, reverse("reports:schedule_list"))
        self.assertEqual(ReportSchedule.objects.count(), 0)


# ── Template Views ──────────────────────────────────────────────

class TemplateListViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="tpluser", password="testpass123")

    def test_template_list_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:template_list"))
        self.assertEqual(response.status_code, 200)


class TemplateCreateViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="tplcreate", password="testpass123")

    def test_template_create_get_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:template_create"))
        self.assertEqual(response.status_code, 200)

    def test_template_create_post_creates(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("reports:template_create"), {
            "name": "New Template",
            "description": "Test",
            "is_public": True,
        })
        self.assertRedirects(response, reverse("reports:template_list"))
        self.assertTrue(ReportTemplate.objects.filter(name="New Template").exists())


class TemplateEditViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="tpledit", password="testpass123")
        self.template = create_report_template(user=self.user, is_public=False)

    def test_template_edit_get_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("reports:template_edit", args=[self.template.pk]),
        )
        self.assertEqual(response.status_code, 200)

    def test_template_edit_post_updates(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("reports:template_edit", args=[self.template.pk]),
            {
                "name": "Updated Template",
                "description": "Updated",
                "is_public": True,
            },
        )
        self.assertRedirects(response, reverse("reports:template_list"))
        self.template.refresh_from_db()
        self.assertEqual(self.template.name, "Updated Template")


class TemplateDeleteViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="tpldel", password="testpass123")
        self.template = create_report_template(user=self.user, is_public=False)

    def test_template_delete(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("reports:template_delete", args=[self.template.pk]),
        )
        self.assertRedirects(response, reverse("reports:template_list"))
        self.assertEqual(ReportTemplate.objects.count(), 0)


# ── Share Report Views ──────────────────────────────────────────

class ShareReportViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="shrrepuser", password="testpass123")
        self.report = create_report(self.user)

    def test_share_report_post(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("reports:share_report", args=[self.report.pk]),
            {"permissions": "view_only"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("share_token", data)

    def test_share_report_with_user(self):
        target = create_user(username="targetuser", password="testpass123")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("reports:share_report", args=[self.report.pk]),
            {"permissions": "view_only", "shared_with_user": "targetuser"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

    def test_share_report_user_not_found(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("reports:share_report", args=[self.report.pk]),
            {"permissions": "view_only", "shared_with_user": "nonexistent"},
        )
        self.assertEqual(response.status_code, 404)


class ManageSharesViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="mgshuser", password="testpass123")
        self.report = create_report(self.user)
        create_report_share(self.report, self.user)

    def test_manage_shares_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("reports:manage_shares", args=[self.report.pk]),
        )
        self.assertEqual(response.status_code, 200)

    def test_manage_shares_ajax(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("reports:manage_shares", args=[self.report.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("shares", data)


class RevokeShareViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="revshruser", password="testpass123")
        self.report = create_report(self.user)
        self.share = create_report_share(self.report, self.user)

    def test_revoke_share(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("reports:revoke_share", args=[self.report.pk, self.share.pk]),
        )
        self.assertRedirects(response, reverse("reports:manage_shares",
                                                args=[self.report.pk]))
        self.share.refresh_from_db()
        self.assertTrue(self.share.is_revoked)


class SharedReportViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="shrviewuser", password="testpass123")
        self.report = create_report(self.user)
        self.share = create_report_share(self.report, self.user)

    def test_shared_view_returns_200(self):
        response = self.client.get(
            reverse("reports:shared_view", args=[self.share.share_token]),
        )
        self.assertEqual(response.status_code, 200)

    def test_shared_view_revoked_shows_error(self):
        self.share.is_revoked = True
        self.share.save(update_fields=["is_revoked"])
        response = self.client.get(
            reverse("reports:shared_view", args=[self.share.share_token]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)

    def test_shared_view_404_invalid_token(self):
        response = self.client.get(
            reverse("reports:shared_view",
                    args=["00000000-0000-0000-0000-000000000000"]),
        )
        self.assertEqual(response.status_code, 404)


class ReportDownloadChartsViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="chrtuser", password="testpass123")
        self.report = create_report(self.user)

    def test_download_charts_no_dir_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("reports:download_charts", args=[self.report.pk]),
        )
        self.assertRedirects(response, reverse("reports:detail",
                                                args=[self.report.pk]))
