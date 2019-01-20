from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count

from loader.models import TestJobs, Tests, Environments, TestsStorage

from tools.tools import unix_time_to_datetime
from statistics import median
import uuid

from loader.email.email import SendJobReport


class Nose2Loader:

    def __init__(self, data):
        self.data = data

    @staticmethod
    def generate_uuid() -> str:
        value = uuid.uuid4()
        return str(value)

    def get_start_test_run(self):
        # print("DBG: startTestRun")
        # print(self.data)
        if TestJobs.objects.filter(uuid=self.data['job_id']):
            return HttpResponse(status=409)

        try:
            env = Environments.objects.get(name=self.data['env'])
        except ObjectDoesNotExist:
            if self.data['env'] is not None:
                env = Environments(name=self.data['env'])
                env.save()
            else:
                try:
                    env = Environments.objects.get(name="None")
                except ObjectDoesNotExist:
                    env = Environments(name="None")
                    env.save()

        # We should not create a job without tests
        if len(self.data['tests']) == 0:
            return HttpResponse(status=403)

        job_object = TestJobs(uuid=self.data['job_id'],
                              status=1,
                              fw_type=1,
                              start_time=unix_time_to_datetime(self.data['startTime']),
                              env=env)
        job_object.save()
        # Tests
        for k, identity in self.data['tests'].items():
            test_uuid = self.generate_uuid()

            # Tests Storage
            try:
                test_storage_item = TestsStorage.objects.get(identity=identity)
                if not test_storage_item.test:
                    test_storage_item.test = identity.split('.')[-1]
                    test_storage_item.save()
            except ObjectDoesNotExist:
                test_storage_item = TestsStorage(identity=identity,
                                   test=identity.split('.')[-1])
                test_storage_item.save()

            # Tests for Job
            test_object = Tests(uuid=test_uuid,
                                status=1,
                                job=job_object,
                                test=test_storage_item)
            test_object.save()

        job_object.tests_not_started = job_object.tests.count()
        job_object.save()

        return HttpResponse(status=200)

    def get_stop_test_run(self):
        # print("DBG: stopTestRun")
        # print(self.data)
        try:
            job_object = TestJobs.objects.get(uuid=self.data['job_id'])
            if job_object.status == 1:
                # in case if 'stopTestRun' was caught, but some running test exists
                if job_object.tests.filter(status=2).first():
                    tests = job_object.tests.filter(status=2)  # 'In progress' tests become 'Aborted'
                    aborted_tests = 0
                    for test in tests:
                        test.status = 6
                        test.save()
                        aborted_tests += 1
                    job_object.status = 3
                    job_object.tests_aborted = aborted_tests
                # in case if 'stopTestRun' was caught and at least one test was failed
                elif job_object.tests.filter(status=4).first():
                    job_object.status = 3
                # in case if 'stopTestRun' was caught and at least one test was aborted
                elif job_object.tests.filter(status=6).first():
                    job_object.status = 3
                # in case if 'stopTestRun' was caught and some tests remain not started
                else:
                    if job_object.tests.filter(status=1).first():
                        tests = job_object.tests.filter(status=1)
                        tests_not_started = 0
                        for test in tests:
                            tests_not_started += 1
                        job_object.tests_not_started = tests_not_started
                        job_object.status = 3
                    if job_object.tests.filter(status=5).all():
                        job_object.status = 5
                    else:
                        # if no tests with 'failed', 'aborted' or 'running' states after 'stopTestRun' signal -
                        # mark job as 'Passed'
                        job_object.status = 2
                job_object.stop_time = unix_time_to_datetime(self.data['stopTime'])
                job_object.time_taken = job_object.stop_time - job_object.start_time
                job_object.save()
                if self.data['send_report'] == "1":
                    SendJobReport(job_object).send()
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=403)
        except ObjectDoesNotExist:
            return HttpResponse(status=403)

    def get_start_test(self):
        # print("DBG: startTest")
        # print(self.data)
        try:
            job_object = TestJobs.objects.get(uuid=self.data['job_id'])
            job_object.tests_not_started -= 1
            job_object.save()
            if job_object.status == 1:
                try:
                    test = Tests.objects.get(test__identity=self.data['test'], job=job_object)
                    test.status = 2
                    test.start_time = unix_time_to_datetime(self.data['startTime'])
                    test.save()
                    return HttpResponse(status=200)
                except ObjectDoesNotExist:
                    return HttpResponse(status=403)
            else:
                return HttpResponse(status=403)
        except ObjectDoesNotExist:
            return HttpResponse(status=403)

    def get_stop_test(self):
        # print("DBG: stopTest")
        # print(self.data)
        try:
            job_object = TestJobs.objects.get(uuid=self.data['job_id'])
            if job_object.status == 1:
                try:
                    test = Tests.objects.get(test__identity=self.data['test'], job=job_object)
                    if self.data['status'] == "passed":
                        test.status = 3
                        if not job_object.tests_passed:
                            job_object.tests_passed = 1
                        else:
                            job_object.tests_passed += 1
                    elif self.data['status'] == "error":
                        test.status = 4
                        if not job_object.tests_failed:
                            job_object.tests_failed = 1
                        else:
                            job_object.tests_failed += 1
                    elif self.data['status'] == "failed":
                        test.status = 4
                        if not job_object.tests_failed:
                            job_object.tests_failed = 1
                        else:
                            job_object.tests_failed += 1
                    elif self.data['status'] == "skipped":
                        test.status = 5
                        if not job_object.tests_skipped:
                            job_object.tests_skipped = 1
                        else:
                            job_object.tests_skipped += 1
                    job_object.save()
                    test.stop_time = unix_time_to_datetime(self.data['stopTime'])
                    test.time_taken = test.stop_time - test.start_time
                    test.msg = str(self.data['msg']).replace("\\n", "\n")
                    test.save()
                    # Tests Storage
                    obj = TestsStorage.objects.get(identity=test.test.identity)
                    if obj.time_taken and not obj.time_taken2:
                        obj.time_taken2 = test.time_taken
                        obj.calculated_eta = median([obj.time_taken, test.time_taken])
                        obj.save()
                    if obj.time_taken2 and not obj.time_taken3:
                        obj.time_taken3 = test.time_taken
                        obj.calculated_eta = median([obj.time_taken, obj.time_taken2, test.time_taken])
                        obj.save()
                    if obj.time_taken3:
                        obj.time_taken3 = obj.time_taken2
                        obj.time_taken2 = obj.time_taken
                        obj.time_taken = test.time_taken
                        obj.calculated_eta = median([obj.time_taken, obj.time_taken2, obj.time_taken3])
                        obj.save()
                    return HttpResponse(status=200)
                except ObjectDoesNotExist:
                    return HttpResponse(status=403)
            else:
                return HttpResponse(status=403)
        except ObjectDoesNotExist:
            return HttpResponse(status=403)
