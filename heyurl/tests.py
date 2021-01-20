from django.test import TestCase
from django.urls import reverse
from .models import Url, Click

from django.utils.timezone import now

class IndexTests(TestCase):
    def test_no_urls(self):
        """
        If no URLs exist, an appropriate message is displayed
        """
        response = self.client.get(reverse('index'))
        self.assertContains(response,"There are no URLs in the system yet!")

    def test_submitting_new_url_failure(self):
        """
        When submitting an invalid URL, an error is returned to the user
        """
        try_list = ['https://-four.com', 'https://www.g*g.com']
        for t in try_list:
            response = self.client.post(reverse('store'),{'original_url':t}, follow=True)
            self.assertContains(response, "INVALID URL")
        ct = Url.objects.all().count()
        self.assertEqual(ct,0)

    def test_submitting_new_url_success(self):
        """
        When submitting a valid URL, a success message is displayed
        """
        try_list = ["www.ebay.com"," https://go.com ", "http://www.g-g.com"]
        good_list = ['https://www.ebay.com','https://go.com', "http://www.g-g.com"]
        for t in range(len(try_list)):
            response = self.client.post(reverse('store'),{'original_url':try_list[t]}, follow=True)
            u = Url.objects.get(original_url=good_list[t])
            msg = "The URL ({0!s}) was successfully uploaded to the database. It is identified by the short URL tag ({1!s}).".format(u.original_url,u.short_url)
            self.assertContains(response, msg)
        ct = Url.objects.all().count()
        self.assertEqual(ct,len(try_list))

    def test_visiting_short_url_missing(self):
        """
        If short URL does not exist, custom 404 page is displayed
        """
        Url.objects.all().delete()
        Click.objects.all().delete()
        short_url = "ZZZZZ"
        response = self.client.get(reverse("short_url",kwargs={'short_url':short_url}))
        msg = "The short URL, identifed by the tag ({0!s}), was not found in the database.".format(short_url)
        self.assertContains(response,msg, status_code=404)
        ct = Click.objects.all().count()
        self.assertEqual(ct,0)

    def test_visiting_short_url(self):
        """
        If short URL exists, stats logged and redirected to original URL
        """
        Url.objects.all().delete()
        Click.objects.all().delete()
        original_url = "https://www.gg.com"
        short_url = "gg"
        u=Url.objects.create(original_url=original_url,short_url=short_url,created_at=now(),updated_at=now())
        response = self.client.get(reverse("short_url",kwargs={'short_url':short_url}))
        uu = Url.objects.get(id=u.pk)
        c = Click.objects.filter(url_id=u.pk)
        self.assertEqual(uu.clicks,1)
        self.assertEqual(c.count(),1)
