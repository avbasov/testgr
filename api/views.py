from django.http import JsonResponse
from loader.models import TestJobs
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseForbidden
from tools.tools import normalize_unix_time

import json


def jobs_latest(request):

    latest_jobs = TestJobs.objects.all().order_by('-stop_time').exclude(status='1')[:10]
    result = []
    for job in latest_jobs:
        job_item = dict()
        job_item['uuid'] = job.uuid
        job_item['time_taken'] = job.time_taken
        job_item['stop_time'] = normalize_unix_time(job.stop_time)
        job_item['status'] = job.status
        job_item['env'] = job.env
        result.append(job_item)
    return JsonResponse(result, safe=False)


def jobs_running(request):

    running_jobs = TestJobs.objects.filter(status='1').order_by('-start_time')
    result = []
    for job in running_jobs:
        job_item = dict()
        job_item['uuid'] = job.uuid
        job_item['start_time'] = normalize_unix_time(job.start_time)
        job_item['status'] = job.status
        job_item['env'] = job.env
        result.append(job_item)
    return JsonResponse(result, safe=False)


@csrf_exempt
def job_details(request):

    if request.method == "POST":
        data = json.loads(request.body)
        uuid = data['uuid']
    else:
        return HttpResponseForbidden()

    job_object = TestJobs.objects.get(uuid=uuid)
    result = {}

    # Statistics
    if job_object.stop_time is not None:
        result['stop_time'] = normalize_unix_time(job_object.stop_time)
    else:
        result['stop_time'] = None
    if job_object.time_taken is not None:
        result['time_taken'] = normalize_unix_time(job_object.time_taken, remove_date=True)
    else:
        result['time_taken'] = None

    # Tests
    tests = []
    for test in job_object.tests.all():
        test_item = dict()
        test_item['identity'] = test.get_test_method()
        test_item['uuid'] = test.uuid
        test_item['time_taken'] = test.time_taken
        test_item['status'] = test.status
        tests.append(test_item)

    # Result JSON
    result['status'] = str(job_object.status)
    result['test_count'] = str(job_object.tests.count())
    result['not_started'] = str(job_object.tests.filter(status=1).count())
    result['passed'] = str(job_object.tests.filter(status=3).count())
    result['failed'] = str(job_object.tests.filter(status=4).count())
    result['skipped'] = str(job_object.tests.filter(status=5).count())
    result['aborted'] = str(job_object.tests.filter(status=6).count())
    result['tests'] = tests
    return JsonResponse(result, safe=False)