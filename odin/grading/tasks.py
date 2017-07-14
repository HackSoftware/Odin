from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.conf import settings
from django.apps import apps

from .client import DjangoGraderClient
from .helper import get_grader_ready_data


@shared_task(bind=True)
def poll_solution(self, solution_id):
    solution_model = apps.get_model(settings.GRADER_SOLUTION_MODEL)
    grader_ready_data = get_grader_ready_data(solution_id, solution_model)
    grader_client = DjangoGraderClient(solution_model=solution_model,
                                       settings_module=settings,
                                       grader_ready_data=grader_ready_data)
    grader_client.poll_grader(solution_id)


@shared_task(bind=True)
def submit_solution(self, solution_id):
    solution_model = apps.get_model(settings.GRADER_SOLUTION_MODEL)
    grader_ready_data = get_grader_ready_data(solution_id, solution_model)
    grader_client = DjangoGraderClient(solution_model=solution_model,
                                       settings_module=settings,
                                       grader_ready_data=grader_ready_data)
    grader_client.submit_request_to_grader(solution_id, poll_solution)
