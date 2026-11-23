from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from pharmacy.models import Medicine, Pharmacy

PW = 'Str0ngPass!9'


class AvailabilityTests(TestCase):
    def setUp(self):
        self.ph = User.objects.create_user('pharma', 'p@x.com', PW, role='pharmacist')
        self.ph2 = User.objects.create_user('pharma2', 'p2@x.com', PW, role='pharmacist')
        self.se = User.objects.create_user('seeker', 's@x.com', PW, role='seeker')
        self.ad = User.objects.create_user('boss', 'a@x.com', PW, role='admin')

    def login(self, u):
        self.client.logout()
        self.client.login(username=u, password=PW)

    # ---- accounts
    def test_register_and_role_redirects(self):
        r = self.client.post(reverse('register'), {'username': 'new', 'email': 'n@x.com', 'role': 'pharmacist',
                             'password': PW, 'confirm_password': PW})
        self.assertRedirects(r, reverse('pharmacist_dashboard'))
        self.client.logout()
        r = self.client.post(reverse('login'), {'username': 'seeker', 'password': PW})
        self.assertRedirects(r, reverse('patient_dashboard'))

    def test_register_validation(self):
        r = self.client.post(reverse('register'), {'username': 'n2', 'email': 's@x.com', 'role': 'seeker',
                             'password': PW, 'confirm_password': 'nope'})
        self.assertContains(r, 'already registered')
        self.assertContains(r, 'Passwords do not match')

    def test_bad_login(self):
        r = self.client.post(reverse('login'), {'username': 'seeker', 'password': 'bad'})
        self.assertContains(r, 'alert-danger')

    def test_role_isolation(self):
        self.login('seeker')
        for name in ('pharmacist_dashboard', 'admin_dashboard', 'pharmacist_medicines', 'my_pharmacy',
                     'admin_pharmacies', 'admin_medicines'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)
        self.login('pharma')
        for name in ('patient_dashboard', 'medicine_search', 'admin_pharmacies', 'admin_dashboard'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('medicine_search')).status_code, 302)

    # ---- pharmacist flow
    def test_pharmacist_must_setup_pharmacy_first(self):
        self.login('pharma')
        r = self.client.get(reverse('pharmacist_medicines'), follow=True)
        self.assertRedirects(r, reverse('my_pharmacy'))
        self.assertContains(r, 'Set up your pharmacy')

    def test_pharmacy_validation_and_save(self):
        self.login('pharma')
        r = self.client.post(reverse('my_pharmacy'), {'name': 'ab', 'location': 'x', 'contact_number': 'abc'})
        self.assertContains(r, 'at least 3 characters')
        self.assertContains(r, 'valid contact number')
        r = self.client.post(reverse('my_pharmacy'), {'name': 'Mercury Drug', 'location': 'Colon, Cebu City',
                             'contact_number': '032 255 1234'}, follow=True)
        self.assertContains(r, 'Pharmacy profile saved')
        self.assertEqual(Pharmacy.objects.get().owner, self.ph)
        # duplicate name from another pharmacist
        self.login('pharma2')
        r = self.client.post(reverse('my_pharmacy'), {'name': 'mercury drug', 'location': 'Mandaue City'})
        self.assertContains(r, 'already exists')

    def test_medicine_crud_and_timestamp(self):
        pharmacy = Pharmacy.objects.create(owner=self.ph, name='Mercury', location='Cebu City')
        self.login('pharma')
        r = self.client.post(reverse('medicine_create'), {'name': 'Paracetamol', 'strength': '500mg', 'status': 'available'},
                             follow=True)
        self.assertContains(r, 'added to your listing')
        m = Medicine.objects.get()
        self.assertEqual(m.pharmacy, pharmacy)
        # duplicate
        r = self.client.post(reverse('medicine_create'), {'name': 'paracetamol', 'strength': '500MG', 'status': 'available'})
        self.assertContains(r, 'already lists this medicine')
        # quick status update refreshes timestamp
        old = timezone.now() - timedelta(days=3)
        Medicine.objects.filter(pk=m.pk).update(availability_updated_at=old)
        r = self.client.post(reverse('medicine_status', args=[m.id]), {'status': 'out_of_stock'}, follow=True)
        self.assertContains(r, 'Out of Stock')
        m.refresh_from_db()
        self.assertEqual(m.status, 'out_of_stock')
        self.assertGreater(m.availability_updated_at, old + timedelta(days=2))
        # invalid status rejected
        r = self.client.post(reverse('medicine_status', args=[m.id]), {'status': 'nonsense'}, follow=True)
        self.assertContains(r, 'Invalid availability status')
        # edit via form changes status -> timestamp refreshed
        Medicine.objects.filter(pk=m.pk).update(availability_updated_at=old)
        self.client.post(reverse('medicine_edit', args=[m.id]), {'name': 'Paracetamol', 'strength': '500mg', 'status': 'low_stock'})
        m.refresh_from_db()
        self.assertEqual(m.status, 'low_stock')
        self.assertGreater(m.availability_updated_at, old + timedelta(days=2))
        # delete
        r = self.client.post(reverse('medicine_delete', args=[m.id]), follow=True)
        self.assertContains(r, 'removed from your listing')
        self.assertFalse(Medicine.objects.exists())

    def test_pharmacist_cannot_touch_other_pharmacy(self):
        p2 = Pharmacy.objects.create(owner=self.ph2, name='Other', location='Mandaue')
        m = Medicine.objects.create(pharmacy=p2, name='Biogesic')
        Pharmacy.objects.create(owner=self.ph, name='Mine', location='Cebu')
        self.login('pharma')
        self.assertEqual(self.client.get(reverse('medicine_edit', args=[m.id])).status_code, 404)
        self.assertEqual(self.client.post(reverse('medicine_status', args=[m.id]), {'status': 'available'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('medicine_delete', args=[m.id])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('pharmacist_medicines')), 'Biogesic')

    # ---- seeker flow
    def test_seeker_search_and_filters(self):
        a = Pharmacy.objects.create(owner=self.ph, name='Mercury', location='Colon, Cebu City')
        b = Pharmacy.objects.create(owner=self.ph2, name='Watsons', location='Mandaue City')
        Medicine.objects.create(pharmacy=a, name='Paracetamol', generic_name='Acetaminophen', status='available')
        Medicine.objects.create(pharmacy=a, name='Amoxicillin', status='out_of_stock')
        Medicine.objects.create(pharmacy=b, name='Paracetamol', status='low_stock')
        self.login('seeker')
        r = self.client.get(reverse('medicine_search'))
        self.assertContains(r, 'Mercury'); self.assertContains(r, 'Watsons'); self.assertContains(r, 'Last updated')
        self.assertContains(self.client.get(reverse('medicine_search') + '?q=aceta'), 'Paracetamol')
        r = self.client.get(reverse('medicine_search') + '?q=amox')
        self.assertContains(r, 'Amoxicillin'); self.assertNotContains(r, 'Biogesic')
        r = self.client.get(reverse('medicine_search') + '?status=low_stock')
        self.assertContains(r, 'Watsons'); self.assertNotContains(r, 'Amoxicillin')
        r = self.client.get(reverse('medicine_search') + f'?pharmacy={b.id}')
        self.assertContains(r, 'Watsons'); self.assertNotContains(r, 'Amoxicillin')
        r = self.client.get(reverse('medicine_search') + '?location=mandaue')
        self.assertNotContains(r, 'Amoxicillin')
        # bogus filter values don't crash
        self.assertEqual(self.client.get(reverse('medicine_search') + '?status=zzz&pharmacy=abc').status_code, 200)

    def test_deactivated_pharmacy_hidden_from_seekers(self):
        a = Pharmacy.objects.create(owner=self.ph, name='Mercury', location='Cebu', is_active=False)
        Medicine.objects.create(pharmacy=a, name='Paracetamol')
        self.login('seeker')
        self.assertNotContains(self.client.get(reverse('medicine_search')), 'Paracetamol')

    # ---- admin flow
    def test_admin_management(self):
        a = Pharmacy.objects.create(owner=self.ph, name='Mercury', location='Cebu')
        m = Medicine.objects.create(pharmacy=a, name='Paracetamol')
        self.login('boss')
        self.assertContains(self.client.get(reverse('admin_pharmacies')), 'Mercury')
        self.assertContains(self.client.get(reverse('admin_medicines')), 'Paracetamol')
        r = self.client.post(reverse('pharmacy_toggle', args=[a.id]), follow=True)
        self.assertContains(r, 'deactivated'); a.refresh_from_db(); self.assertFalse(a.is_active)
        r = self.client.post(reverse('admin_medicine_edit', args=[m.id]), {'name': 'Paracetamol', 'strength': '650mg', 'status': 'available'}, follow=True)
        self.assertContains(r, 'updated'); m.refresh_from_db(); self.assertEqual(m.strength, '650mg')
        self.client.post(reverse('admin_medicine_delete', args=[m.id]))
        self.assertFalse(Medicine.objects.exists())
        self.assertEqual(self.client.get(reverse('admin_dashboard')).status_code, 200)

    def test_dashboards_and_profile(self):
        for u, name in [('seeker', 'patient_dashboard'), ('pharma', 'pharmacist_dashboard'), ('boss', 'admin_dashboard')]:
            self.login(u)
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
            self.assertEqual(self.client.get(reverse('profile')).status_code, 200)
            r = self.client.post(reverse('profile'), {'username': u, 'email': f'{u}@new.com', 'phone_number': '0917'}, follow=True)
            self.assertContains(r, 'Profile updated')
        Pharmacy.objects.create(owner=self.ph, name='Mercury', location='Cebu')
        self.login('pharma')
        self.assertContains(self.client.get(reverse('pharmacist_dashboard')), 'Mercury')
