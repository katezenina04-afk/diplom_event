from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import SpecialistProfile


class SpecialistProfileFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='u1', password='pass12345')

    def test_edit_specialist_profile_sets_role_to_specialist(self):
        self.client.login(username='u1', password='pass12345')
        response = self.client.post(reverse('edit_specialist_profile'), data={
            'full_name': 'Иван Иванов',
            'specialization': 'Психолог',
            'competencies': 'Консультирование',
            'experience_years': 5,
            'city': 'Москва',
            'contact_email': 'ivan@example.com',
            'moderation_status': 'pending',
        })

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'specialist')
        self.assertTrue(SpecialistProfile.objects.filter(user=self.user).exists())

    def test_specialists_list_shows_only_approved_profiles(self):
        SpecialistProfile.objects.create(
            user=self.user,
            full_name='Иван Иванов',
            specialization='Психолог',
            moderation_status='approved',
        )
        user2 = get_user_model().objects.create_user(username='u2', password='pass12345')
        SpecialistProfile.objects.create(
            user=user2,
            full_name='Петр Петров',
            specialization='Коуч',
            moderation_status='pending',
        )

        response = self.client.get(reverse('specialists_list'))

        self.assertContains(response, 'Иван Иванов')
        self.assertNotContains(response, 'Петр Петров')