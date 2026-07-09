from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from privacy_platform.test_utils import (
    create_user, create_technique, create_dataset_csv,
    create_completed_experiment, create_experiment_share,
)
from share.models import ExperimentShare


class CreateShareLinkViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="shareuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_completed_experiment(
            self.user, self.technique, self.dataset,
        )

    def test_create_share_requires_login(self):
        response = self.client.get(
            reverse("share:create_experiment_share", args=[self.experiment.pk]),
        )
        self.assertNotEqual(response.status_code, 200)

    def test_create_share_get_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("share:create_experiment_share", args=[self.experiment.pk]),
        )
        self.assertEqual(response.status_code, 200)

    def test_create_share_post_creates_share(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("share:create_experiment_share", args=[self.experiment.pk]),
            {"permissions": "view_only"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ExperimentShare.objects.filter(
            experiment=self.experiment, shared_by=self.user,
        ).exists())

    def test_create_share_creates_with_expiry(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("share:create_experiment_share", args=[self.experiment.pk]),
            {"permissions": "download", "expires_days": "7"},
        )
        self.assertEqual(response.status_code, 200)
        share = ExperimentShare.objects.get(experiment=self.experiment)
        self.assertIsNotNone(share.expires_at)


class SharedExperimentViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="shareviewuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_completed_experiment(
            self.user, self.technique, self.dataset,
        )
        self.share = create_experiment_share(self.experiment, self.user)

    def test_shared_view_returns_200(self):
        response = self.client.get(
            reverse("share:experiment_shared_view", args=[self.share.share_token]),
        )
        self.assertEqual(response.status_code, 200)

    def test_shared_view_404_for_invalid_token(self):
        response = self.client.get(
            reverse("share:experiment_shared_view", args=["00000000-0000-0000-0000-000000000000"]),
        )
        self.assertEqual(response.status_code, 404)

    def test_shared_view_revoked_shows_error(self):
        self.share.is_revoked = True
        self.share.save(update_fields=["is_revoked"])
        response = self.client.get(
            reverse("share:experiment_shared_view", args=[self.share.share_token]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)


class ManageLinksViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="linkuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_completed_experiment(
            self.user, self.technique, self.dataset,
        )

    def test_manage_links_requires_login(self):
        response = self.client.get(
            reverse("share:manage_experiment_links", args=[self.experiment.pk]),
        )
        self.assertNotEqual(response.status_code, 200)

    def test_manage_links_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("share:manage_experiment_links", args=[self.experiment.pk]),
        )
        self.assertEqual(response.status_code, 200)

    def test_manage_links_404_for_wrong_user(self):
        other = create_user(username="otherlink", password="testpass123")
        self.client.force_login(other)
        response = self.client.get(
            reverse("share:manage_experiment_links", args=[self.experiment.pk]),
        )
        self.assertEqual(response.status_code, 404)


class RevokeLinkViewTest(TestCase):
    def setUp(self):
        self.user = create_user(username="revokeuser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_completed_experiment(
            self.user, self.technique, self.dataset,
        )
        self.share = create_experiment_share(self.experiment, self.user)

    def test_revoke_requires_login(self):
        response = self.client.post(
            reverse("share:revoke_experiment_link", args=[self.share.pk]),
        )
        self.assertNotEqual(response.status_code, 200)

    def test_revoke_marks_as_revoked(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("share:revoke_experiment_link", args=[self.share.pk]),
        )
        self.share.refresh_from_db()
        self.assertTrue(self.share.is_revoked)


class SharedViewExpiredTokenTest(TestCase):
    def setUp(self):
        self.user = create_user(username="expireduser", password="testpass123")
        self.technique = create_technique("ring_signature")
        self.dataset = create_dataset_csv(self.user)
        self.experiment = create_completed_experiment(
            self.user, self.technique, self.dataset,
        )
        self.share = create_experiment_share(self.experiment, self.user)
        self.share.expires_at = timezone.now() - timedelta(days=1)
        self.share.save(update_fields=["expires_at"])

    def test_shared_view_expired_returns_error(self):
        response = self.client.get(
            reverse("share:experiment_shared_view", args=[self.share.share_token]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)

    def test_shared_view_revoked_after_revocation_view_error(self):
        self.share.is_revoked = True
        self.share.save(update_fields=["is_revoked"])
        second_response = self.client.get(
            reverse("share:experiment_shared_view", args=[self.share.share_token]),
        )
        self.assertEqual(second_response.status_code, 200)
        self.assertIn("error", second_response.context)
