from django.utils import timezone
from django.db import models

from tinymce.models import HTMLField

from odin.education.models import Course

from odin.users.models import BaseUser

from .managers import ApplicationInfoManager
from .query import ApplicationQuerySet


class ApplicationInfo(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()

    course = models.OneToOneField(Course, related_name='application_info')

    start_interview_date = models.DateField(blank=True, null=True)
    end_interview_date = models.DateField(blank=True, null=True)

    description = HTMLField(blank=True, null=True)

    external_application_form = models.URLField(
        blank=True, null=True,
        help_text='Only add if course requires external application form'
    )

    objects = ApplicationInfoManager()

    def __str__(self):
        return "{0}".format(self.course)

    @property
    def accepted_applicants(self):
        return self.applications.select_related('user__profile').filter(is_accepted=True)

    def apply_is_active(self):
        return self.start_date <= timezone.now().date() <= self.end_date

    def interview_is_active(self):
        return self.start_interview_date <= timezone.now().date() and \
               self.end_interview_date >= timezone.now().date()


class Application(models.Model):
    application_info = models.ForeignKey(ApplicationInfo, related_name='applications')
    user = models.ForeignKey(BaseUser, related_name='applications')

    phone = models.CharField(null=True, blank=True, max_length=255)
    skype = models.CharField(max_length=255)
    works_at = models.CharField(null=True, blank=True, max_length=255)
    studies_at = models.CharField(blank=True, null=True, max_length=255)
    is_accepted = models.BooleanField(default=False)

    interview_slot = models.DateTimeField(null=True, blank=True)
    interview_person = models.ForeignKey(BaseUser, blank=True, null=True, related_name='interviews')

    has_interview_date = models.BooleanField(default=False)

    objects = ApplicationQuerySet.as_manager()

    def get_interview(self):
        interview = self.interview_set.select_related('interviewer__profile')
        if interview:
            return self.interview_set.select_related('interviewer__profile').first()

    def __str__(self):
        return "{0} applying to {1}".format(self.user, self.application_info)

    class Meta:
        unique_together = (("application_info", "user"),)
