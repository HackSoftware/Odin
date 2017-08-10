from django.db import models


class InterviewQuerySet(models.QuerySet):

    def get_free_slots(self):
        return self.filter(application__isnull=True)

    def free_slots_for(self, application_info):
        return self.get_free_slots().filter(
                interviewer__courses_to_interview__in=[application_info])

    def with_application(self):
        return self.filter(application__isnull=False)

    def without_received_email(self):
        return self.filter(has_received_email=False)

    def confirmed_for(self, info):
        return self.filter(has_confirmed=True, application__application_info=info)

    def confirmed_interviews_on(self, user):
        return self.with_application().filter(application__user=user, has_confirmed=True)
