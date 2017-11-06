from unittest.mock import patch
from test_plus import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.utils import timezone
from django.test.utils import override_settings

from ..services import add_student, add_teacher
from ..factories import (
    CourseFactory,
    StudentFactory,
    TeacherFactory,
    WeekFactory,
    TopicFactory,
    MaterialFactory,
    IncludedMaterialFactory,
    TaskFactory,
    IncludedTaskFactory,
    ProgrammingLanguageFactory,
    SourceCodeTestFactory,
    BinaryFileTestFactory,
    SolutionFactory,
)
from ..models import (
    Student,
    Teacher,
    Topic,
    IncludedMaterial,
    Material,
    IncludedTask,
    Task,
    Solution,
    IncludedTest,
    StudentNote,
    Lecture,
    SolutionComment
)

from odin.users.factories import ProfileFactory, BaseUserFactory, SuperUserFactory

from odin.common.faker import faker


class TestUserCoursesView(TestCase):

    def setUp(self):
        self.test_password = faker.password()
        self.course = CourseFactory()
        self.student = StudentFactory(password=self.test_password)
        self.teacher = TeacherFactory(password=self.test_password)
        self.url = reverse('dashboard:education:user-courses')
        self.student.is_active = True
        self.teacher.is_active = True
        self.student.save()
        self.teacher.save()

    def test_get_course_list_view_when_logged_in(self):
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_get_course_list_redirects_to_login_when_not_logged(self):
        response = self.get(self.url)
        self.assertEqual(302, response.status_code)

    def test_course_is_not_shown_if_student_is_not_in_it(self):
        course = CourseFactory(name="TestCourseName")
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertNotIn(course.name, response.content.decode('utf-8'))

    def test_user_courses_are_shown_for_student_in_course(self):
        with self.login(email=self.student.email, password=self.test_password):
            add_student(self.course, self.student)
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, self.course.name)

    def test_course_is_not_shown_if_teacher_is_not_in_it(self):
        course = CourseFactory(name="TestCourseName")
        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertNotContains(response, course.name)

    def test_user_courses_are_shown_for_teacher_in_course(self):
        course = CourseFactory(name="TestCourseName")
        with self.login(email=self.teacher.email, password=self.test_password):
            add_teacher(course, self.teacher)
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, course.name)

    def test_course_is_shown_if_user_is_teacher_and_student_in_different_courses(self):
        course = CourseFactory(name="TestCourseName")
        student = Student.objects.create_from_user(self.teacher.user)
        student.is_active = True
        student.save()
        with self.login(email=self.teacher.email, password=self.test_password):
            add_teacher(self.course, self.teacher)
            add_student(course, student)
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, self.course.name)
            self.assertContains(response, course.name)


class TestCourseDetailView(TestCase):

    def setUp(self):
        self.test_password = faker.password()
        self.course = CourseFactory()
        self.user = BaseUserFactory(password=self.test_password)
        self.student = StudentFactory(password=self.test_password)
        self.teacher = TeacherFactory(password=self.test_password)
        self.url = reverse('dashboard:education:user-course-detail', kwargs={'course_id': self.course.pk})
        self.user.is_active = True
        self.student.is_active = True
        self.teacher.is_active = True
        self.user.save()
        self.student.save()
        self.teacher.save()

    def test_can_not_access_course_detail_if_not_student_or_teacher(self):
        response = self.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_can_access_course_detail_if_student(self):
        add_student(self.course, self.student)
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_course_teachers_do_not_appear_if_there_is_none(self):
        ProfileFactory(user=self.teacher.user)
        add_student(self.course, self.student)
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertNotContains(response, self.teacher.get_full_name())
            self.assertNotContains(response, self.teacher.profile.description)


class TestPublicCourseListView(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.url = reverse('public:courses')

    def test_template_does_not_contain_sidebar_and_sidebar_button(self):
        response = self.get(self.url)
        self.response_200(response)
        content = response.content.decode('utf-8')
        self.assertNotIn('<div class="page-content-wrapper">', content)
        self.assertIn('<div class="menu-toggler sidebar-toggler hide">', content)


class TestPublicCourseDetailView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.url = reverse('public:course_detail', kwargs={'course_slug': self.course.slug_url})

    def test_cannot_add_topic_or_material_on_public_detail_page(self):
        response = self.get(self.url)
        self.assertEqual(200, response.status_code)
        content = response.content.decode('utf-8')
        self.assertNotIn(content,
                         "<button type='button' name='button' class='btn green uppercase' >Add new topic</button>")
        self.assertNotIn(content,
                         "<button type='button' name='button' class='btn green uppercase' >Add new material</button>")

        def test_template_does_not_contain_sidebar_and_sidebar_button(self):
            response = self.get(self.url)
            self.response_200(response)
            content = response.content.decode('utf-8')
            self.assertNotIn('<div class="page-content-wrapper">', content)
            self.assertIn('<div class="menu-toggler sidebar-toggler hide">', content)


class TestAddTopicToCourseView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.week = WeekFactory(course=self.course)
        self.url = reverse('dashboard:education:course-management:manage-course-topics',
                           kwargs={'course_id': self.course.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_create_topic_for_course_on_post(self):
        data = {
            'name': faker.name(),
            'week': self.week.id
        }
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.assertRedirects(response,
                                 expected_url=reverse('dashboard:education:user-course-detail',
                                                      kwargs={'course_id': self.course.id}))
            self.assertEqual(1, Topic.objects.count())
            self.assertEqual(1, Topic.objects.filter(course=self.course).count())


class TestExistingMaterialsView(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.topic = TopicFactory(course=self.course)
        self.url = reverse('dashboard:education:course-management:existing-materials',
                           kwargs={'course_id': self.course.id, 'topic_id': self.topic.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_materials_are_shown_correctly_when_included_or_regular(self):
        material = MaterialFactory()
        included_material = IncludedMaterialFactory(topic=self.topic)
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertContains(response, material.identifier)
            self.assertContains(response, included_material.identifier)


class TestAddNewIncludedMaterialView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.topic = TopicFactory(course=self.course)
        self.url = reverse('dashboard:education:course-management:add-new-included-material',
                           kwargs={'course_id': self.course.id,
                                   'topic_id': self.topic.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_create_new_material_for_topic_on_post(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        material_count = IncludedMaterial.objects.count()
        topic_material_count = self.topic.materials.count()
        data = {
            'identifier': faker.name(),
            'url': faker.url(),
            'content': faker.text(),
            'topic': self.topic.id,
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}
            ))
            self.assertEqual(material_count + 1, IncludedMaterial.objects.count())
            self.assertEqual(topic_material_count + 1, self.topic.materials.count())


class TestEditIncludedMaterialView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.included_material = IncludedMaterialFactory(topic__course=self.course)
        self.url = reverse('dashboard:education:course-management:edit-included-material',
                           kwargs={
                               'course_id': self.course.id,
                               'material_id': self.included_material.id
                           })
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_included_material_is_edited_successfully_on_post(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        new_identifier = faker.name()
        data = {
            'identifier': new_identifier,
            'topic': self.included_material.topic.id,
            'content': self.included_material.material.content
        }
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id})
            )
            self.included_material.refresh_from_db()
            self.assertEquals(new_identifier, self.included_material.identifier)


class TestAddIncludedMaterialFromExistingView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.topic = TopicFactory(course=self.course)
        self.url = reverse('dashboard:education:course-management:add-included-material-from-existing',
                           kwargs={'course_id': self.course.id,
                                   'topic_id': self.topic.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_add_ordinary_material_to_course(self):
        material_count = IncludedMaterial.objects.count()
        teacher = Teacher.objects.create_from_user(self.user)
        material = MaterialFactory()
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data={'material': material.id})
            self.assertRedirects(response, expected_url=reverse(
                                 'dashboard:education:user-course-detail',
                                 kwargs={'course_id': self.course.id}))
            self.assertEqual(material_count + 1, IncludedMaterial.objects.count())
            included_material = IncludedMaterial.objects.filter(material=material)
            self.assertEqual(1, Topic.objects.filter(materials__in=included_material).count())

    def test_can_add_included_material_from_existing_included_materials(self):
        course = CourseFactory()
        topic = TopicFactory(course=course)
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        included_material = IncludedMaterialFactory(topic=topic)

        included_material_count = IncludedMaterial.objects.count()
        topic_material_count = self.topic.materials.count()
        material_count = Material.objects.count()

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data={'material': included_material.material.id})
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}))
            self.assertEqual(included_material_count + 1, IncludedMaterial.objects.count())
            self.assertEqual(topic_material_count + 1, self.topic.materials.count())
            self.assertEqual(material_count, Material.objects.count())


class TestExistingTasksView(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.topic = TopicFactory(course=self.course)
        self.url = reverse('dashboard:education:course-management:existing-tasks',
                           kwargs={'course_id': self.course.id,
                                   'topic_id': self.topic.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_tasks_are_shown_correctly_when_included_or_regular(self):
        task = TaskFactory()
        included_task = IncludedTaskFactory(topic__course=self.course)
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertContains(response, task.name)
            self.assertContains(response, included_task.name)


class TestAddNewIncludedTaskView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.topic = TopicFactory(course=self.course)
        self.url = reverse('dashboard:education:course-management:add-new-included-task',
                           kwargs={'course_id': self.course.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)
        self.language = ProgrammingLanguageFactory()

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_create_new_task_for_topic_on_post(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        task_count = IncludedTask.objects.count()
        topic_task_count = self.topic.tasks.count()
        data = {
            'name': faker.name(),
            'description': faker.text(),
            'topic': self.topic.id,
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}
            ))
            self.assertEqual(task_count + 1, IncludedTask.objects.count())
            self.assertEqual(topic_task_count + 1, self.topic.tasks.count())

    def test_view_does_not_create_test_when_task_is_not_gradable(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        task_count = IncludedTask.objects.count()
        test_count = IncludedTest.objects.count()
        data = {
            'name': faker.name(),
            'description': faker.text(),
            'topic': self.topic.id,
            'gradable': False,
            'language': self.language.id,
            'code': faker.text()
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}
            ))
            self.assertEqual(task_count + 1, IncludedTask.objects.count())
            self.assertEqual(test_count, IncludedTest.objects.count())

    def test_view_creates_test_when_when_task_is_gradeable(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        task_count = IncludedTask.objects.count()
        test_count = IncludedTest.objects.count()
        data = {
            'name': faker.name(),
            'description': faker.text(),
            'topic': self.topic.id,
            'gradable': True,
            'language': self.language.id,
            'code': faker.text()
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}
            ))
            self.assertEqual(task_count + 1, IncludedTask.objects.count())
            self.assertEqual(test_count + 1, IncludedTest.objects.count())


class TestAddIncludedTaskFromExistingView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.topic = TopicFactory(course=self.course)
        self.url = reverse('dashboard:education:course-management:add-included-task-from-existing',
                           kwargs={'course_id': self.course.id,
                                   'topic_id': self.topic.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_add_ordinary_task_that_has_not_yet_been_included_to_course(self):
        task_count = IncludedTask.objects.count()
        teacher = Teacher.objects.create_from_user(self.user)
        task = TaskFactory()
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            response = self.post(self.url, data={'task': task.id})
            self.assertEqual(task_count + 1, IncludedTask.objects.count())
            included_task = IncludedTask.objects.filter(task=task)
            self.assertEqual(1, Topic.objects.filter(tasks__in=included_task).count())

    def test_can_add_included_task_from_existing_already_included_tasks(self):
        course = CourseFactory()
        topic = TopicFactory(course=course)
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        included_task = IncludedTaskFactory(topic=topic)

        included_task_count = IncludedTask.objects.count()
        task_count = Task.objects.count()

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data={'task': included_task.task.id})
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}))
            self.assertEqual(included_task_count + 1, IncludedTask.objects.count())
            self.assertEqual(task_count, Task.objects.count())


class TestEditIncludedTaskView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.included_task = IncludedTaskFactory(topic__course=self.course)
        self.url = reverse('dashboard:education:course-management:edit-included-task',
                           kwargs={
                               'course_id': self.course.id,
                               'task_id': self.included_task.id
                           })
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_included_task_is_edited_successfully_on_post(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        new_name = faker.name()
        data = {
            'name': new_name,
            'topic': self.included_task.topic.id,
            'description': self.included_task.task.description
        }
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id})
            )
            self.included_task.refresh_from_db()
            self.assertEquals(new_name, self.included_task.name)


class TestEditTaskView(TestCase):

    def setUp(self):
        self.task = TaskFactory()
        self.url = reverse('dashboard:education:edit-task',
                           kwargs={
                               'task_id': self.task.id
                           })
        self.test_password = faker.password()
        self.user = SuperUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_superuser(self):
        response = self.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_superuser(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_task_is_edited_successfully_on_post(self):
        new_name = faker.name()
        data = {
            'name': new_name,
            'description': self.task.description,
            'gradable': self.task.gradable
        }
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-courses',
            ))
            self.task.refresh_from_db()
            self.assertEquals(new_name, self.task.name)


class TestAddSourceCodeTestToTaskView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.included_task = IncludedTaskFactory(topic__course=self.course, gradable=True)
        self.test_password = faker.password()
        self.language = ProgrammingLanguageFactory()
        self.user = BaseUserFactory(password=self.test_password)
        self.url = reverse('dashboard:education:course-management:add-source-test',
                           kwargs={
                               'course_id': self.course.id,
                               'task_id': self.included_task.id,
                           })

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_source_test_is_added_to_task_on_post(self):
        filters = {
            'code__isnull': False,
            'file': ''
        }

        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        source_test_count = IncludedTest.objects.filter(**filters).count()
        task_tests = IncludedTest.objects.filter(task=self.included_task).count()

        data = {
            'language': self.language.id,
            'code': faker.text()
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id})
            )

            self.assertEqual(source_test_count + 1, IncludedTest.objects.filter(**filters).count())
            self.assertEqual(task_tests + 1, IncludedTest.objects.filter(task=self.included_task).count())


class TestAddBinaryFileTestToTaskView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.included_task = IncludedTaskFactory(topic__course=self.course, gradable=True)
        self.test_password = faker.password()
        self.language = ProgrammingLanguageFactory()
        self.user = BaseUserFactory(password=self.test_password)
        self.url = reverse('dashboard:education:course-management:add-binary-test',
                           kwargs={
                               'course_id': self.course.id,
                               'task_id': self.included_task.id,
                           })

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_binary_test_is_added_to_task_on_post(self):
        filters = {
            'code__isnull': True,
        }

        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        binary_test_count = IncludedTest.objects.filter(**filters).count()
        task_tests = IncludedTest.objects.filter(task=self.included_task).count()
        file = SimpleUploadedFile('file.jar', bytes(f'{faker.text}'.encode('utf-8')))
        data = {
            'language': self.language.id,
            'file': file
        }
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id})
            )
            self.assertEqual(binary_test_count + 1, IncludedTest.objects.filter(~Q(file=''), **filters).count())
            self.assertEqual(task_tests + 1, IncludedTest.objects.filter(task=self.included_task).count())


class TestStudentSolutionListView(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.task = IncludedTaskFactory(topic__course=self.course)
        self.url = reverse('dashboard:education:user-task-solutions',
                           kwargs={'course_id': self.course.id,
                                   'task_id': self.task.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_returns_403_when_user_is_not_student_in_course(self):
        teacher = Teacher.objects.create_from_user(user=self.user)
        add_teacher(self.course, teacher)

        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.response_403(response=response)

    def test_get_returns_200_when_user_is_student_in_course(self):
        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)

        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.response_200(response=response)


class TestSubmitGradableSolutionView(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.task = IncludedTaskFactory(gradable=True, topic__course=self.course)
        self.url = reverse('dashboard:education:add-gradable-solution',
                           kwargs={'course_id': self.course.id,
                                   'task_id': self.task.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_when_not_student_or_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_student_for_course(self):
        BinaryFileTestFactory(task=self.task)
        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_not_access_view_if_no_test_for_task(self):
        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)

        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            redirect_url = reverse('dashboard:education:user-task-solutions',
                                   kwargs={'course_id': self.course.id,
                                           'task_id': self.task.id})
            self.assertRedirects(response, expected_url=redirect_url)

    def test_can_not_submit_solution_if_no_test_for_task(self):
        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)
        solution_count = Solution.objects.count()
        data = {'code': faker.text()}

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            redirect_url = reverse('dashboard:education:user-task-solutions',
                                   kwargs={'course_id': self.course.id,
                                           'task_id': self.task.id})
            self.assertRedirects(response, expected_url=redirect_url)
            self.assertEqual(solution_count, Solution.objects.count())

    def test_submitting_solution_if_course_has_ended_is_forbidden(self):
        self.course.start_date = timezone.now().date() - timezone.timedelta(days=3)
        self.course.end_date = timezone.now().date() - timezone.timedelta(days=2)
        self.course.save()

        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)

        with self.login(email=self.user.email, password=self.test_password):
            data = {'code': faker.text()}
            response = self.post(url_name=self.url, data=data)
            self.response_403(response)

    @patch('odin.education.views.start_grader_communication')
    def test_solution_for_task_added_successfully_on_post_when_student_for_course_and_source_code_tests(
        self, mock_submit_solution
    ):
        SourceCodeTestFactory(task=self.task)
        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)
        solution_count = Solution.objects.count()
        task_solution_count = self.task.solutions.count()
        data = {'code': faker.text()}
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            redirect_url = reverse('dashboard:education:student-solution-detail',
                                   kwargs={'course_id': self.course.id,
                                           'task_id': self.task.id,
                                           'solution_id': Solution.objects.last().id})

            self.assertRedirects(response, expected_url=redirect_url)
            self.assertEqual(solution_count + 1, Solution.objects.count())
            self.assertEqual(task_solution_count + 1, self.task.solutions.count())
            self.assertEqual(mock_submit_solution.called, True)

    @patch('odin.education.views.start_grader_communication')
    def test_solution_for_task_added_successfully_on_post_when_student_for_course_and_binary_code_tests(
        self, mock_submit_solution
    ):
        BinaryFileTestFactory(task=self.task)
        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)
        solution_count = Solution.objects.count()
        task_solution_count = self.task.solutions.count()
        file = SimpleUploadedFile('file.jar', bytes(f'{faker.text}'.encode('utf-8')))
        data = {'file': file}
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            redirect_url = reverse('dashboard:education:student-solution-detail',
                                   kwargs={'course_id': self.course.id,
                                           'task_id': self.task.id,
                                           'solution_id': Solution.objects.last().id})

            self.assertRedirects(response, expected_url=redirect_url)
            self.assertEqual(solution_count + 1, Solution.objects.count())
            self.assertEqual(task_solution_count + 1, self.task.solutions.count())
            self.assertEqual(mock_submit_solution.called, True)


class TestSubmitNonGradableSolutionView(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.task = IncludedTaskFactory(gradable=False, topic__course=self.course)
        self.url = reverse('dashboard:education:add-not-gradable-solution',
                           kwargs={'course_id': self.course.id,
                                   'task_id': self.task.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_when_not_student_or_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_student_for_course(self):
        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_submitting_solution_if_course_has_ended_is_forbidden(self):
        self.course.start_date = timezone.now().date() - timezone.timedelta(days=3)
        self.course.end_date = timezone.now().date() - timezone.timedelta(days=2)
        self.course.save()

        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)

        with self.login(email=self.user.email, password=self.test_password):
            data = {'url': faker.url()}
            response = self.post(url_name=self.url, data=data)
            self.response_403(response)

    def test_solution_for_task_added_successfully_on_post_when_student_for_course(self):
        student = Student.objects.create_from_user(user=self.user)
        add_student(self.course, student)
        solution_count = Solution.objects.count()
        task_solution_count = self.task.solutions.count()
        data = {'url': faker.url()}
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            redirect_url = reverse('dashboard:education:student-solution-detail',
                                   kwargs={'course_id': self.course.id,
                                           'task_id': self.task.id,
                                           'solution_id': Solution.objects.last().id})

            self.assertRedirects(response, expected_url=redirect_url)
            self.assertEqual(solution_count + 1, Solution.objects.count())
            self.assertEqual(task_solution_count + 1, self.task.solutions.count())


class TestSolutionDetailApi(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.topic = TopicFactory(course=self.course)
        self.task = IncludedTaskFactory(topic=self.topic)
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)
        self.student = Student.objects.create_from_user(self.user)
        add_student(course=self.course, student=self.student)
        self.solution = Solution.objects.create(
            student=self.student,
            code=faker.text(),
            task=self.task
        )
        self.url = reverse('dashboard:education:student-solution-detail-api',
                           kwargs={
                               'solution_id': self.solution.id
                           })

    def test_get_is_forbidden_if_not_student_or_teacher_in_course(self):
        new_user = BaseUserFactory(password=self.test_password)

        with self.login(email=new_user.email, password=self.test_password):
            response = self.get(self.url)

            self.response_403(response)

    def test_get_is_forbidden_if_request_user_is_not_solution_author(self):
        new_user = BaseUserFactory(password=self.test_password)
        new_student = Student.objects.create_from_user(new_user)
        add_student(course=self.course, student=new_student)

        with self.login(email=new_user.email, password=self.test_password):
            response = self.get(self.url)
            self.response_403(response)

    def test_get_is_allowed_when_user_is_solution_author(self):
        with self.login(email=self.user.email, password=self.test_password):
            self.get_check_200(self.url)

    def test_get_is_allowed_when_user_is_teacher_in_course(self):
        new_user = BaseUserFactory(password=self.test_password)
        teacher = Teacher.objects.create_from_user(new_user)
        add_teacher(course=self.course, teacher=teacher)

        with self.login(email=new_user.email, password=self.test_password):
            self.get_check_200(self.url)


class TestCreateStudentNoteView(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)
        self.teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(course=self.course, teacher=self.teacher)
        self.student = Student.objects.create_from_user(BaseUserFactory())
        add_student(course=self.course, student=self.student)
        self.url = reverse('dashboard:education:create-student-note',
                           kwargs={
                               'course_id': self.course.id
                           })

    def test_get_redirects_to_course_students_list(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            expected_url = reverse('dashboard:education:course-students-list',
                                   kwargs={
                                       'course_id': self.course.id
                                   })
            self.assertRedirects(response, expected_url=expected_url)

    def test_post_with_valid_data_creates_student_note_for_correct_assignment(self):
        current_student_note_count = StudentNote.objects.count()
        data = {
            'student': self.student.id,
            'text': faker.text()
        }

        with self.login(email=self.user.email, password=self.test_password):
            self.post(self.url, data=data)
            self.assertEqual(current_student_note_count + 1, StudentNote.objects.count())
            last_note = StudentNote.objects.last()
            student_notes = self.student.course_assignments.get(course=self.course).notes.all()
            self.assertIn(last_note, student_notes)

    def test_post_with_valid_data_redirects_to_specific_notes_section(self):
        data = {
            'student': self.student.id,
            'text': faker.text()
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            expected_url = reverse('dashboard:education:course-students-list',
                                   kwargs={
                                       'course_id': self.course.id
                                   }) + f'#notes-section_{self.student.id}'

            self.assertRedirects(response, expected_url=expected_url)

    def test_post_with_invalid_student_returns_404(self):
        new_student = Student.objects.create_from_user(BaseUserFactory())
        data = {
            'student': new_student.id,
            'text': faker.text()
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)

            self.response_404(response)


class TestCourseStudentDetailView(TestCase):
    def setUp(self):
        self.test_password = faker.password()
        self.teacher = TeacherFactory(password=self.test_password)
        self.student = StudentFactory()
        self.course = CourseFactory()
        add_student(course=self.course, student=self.student)
        self.url = reverse('dashboard:education:course-student-detail',
                           kwargs={
                               'email': self.student.email,
                               'course_id': self.course.id
                           })
        self.teacher.is_active = True
        self.student.is_active = True
        self.teacher.save()
        self.student.save()

    def test_access_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.response_403(response)

    def test_access_is_allowed_when_teacher_for_course(self):
        add_teacher(course=self.course, teacher=self.teacher)

        with self.login(email=self.teacher.email, password=self.test_password):
            self.get_check_200(self.url)


class TestCreateLectureView(TestCase):
    def setUp(self):
        start_date = timezone.now().date() + timezone.timedelta(days=faker.pyint())
        self.course = CourseFactory(start_date=start_date,
                                    end_date=start_date+timezone.timedelta(days=faker.pyint()))
        self.valid_date = start_date + timezone.timedelta(days=1)
        self.invalid_date = self.course.end_date + timezone.timedelta(days=faker.pyint())
        self.test_password = faker.password()
        self.teacher = Teacher.objects.create_from_user(BaseUserFactory(password=self.test_password))
        add_teacher(course=self.course, teacher=self.teacher)
        self.url = reverse('dashboard:education:course-management:create-lecture',
                           kwargs={
                               'course_id': self.course.id
                           })

    def test_post_with_valid_date_creates_lecture_for_course(self):
        current_lecture_count = self.course.lectures.count()
        data = {
            'date': self.valid_date
        }
        with self.login(email=self.teacher.email, password=self.test_password):
            self.post(self.url, data=data)
            self.course.refresh_from_db()

            self.assertEqual(current_lecture_count + 1, self.course.lectures.count())

    def test_post_with_invalid_date_does_not_create_lecture(self):
        current_lecture_count = self.course.lectures.count()
        data = {
            'date': self.invalid_date
        }
        with self.login(email=self.teacher.email, password=self.test_password):
            self.post(self.url, data=data)
            self.course.refresh_from_db()

            self.assertEqual(current_lecture_count, self.course.lectures.count())


class TestEditLectureView(TestCase):
    def setUp(self):
        start_date = timezone.now().date() + timezone.timedelta(days=faker.pyint())
        self.course = CourseFactory(start_date=start_date,
                                    end_date=start_date+timezone.timedelta(days=faker.pyint()))
        self.lecture = Lecture.objects.create(course=self.course,
                                              week=self.course.weeks.first(),
                                              date=self.course.weeks.first().start_date)
        self.test_password = faker.password()
        self.teacher = Teacher.objects.create_from_user(BaseUserFactory(password=self.test_password))
        add_teacher(course=self.course, teacher=self.teacher)
        self.url = reverse('dashboard:education:course-management:edit-lecture',
                           kwargs={
                               'course_id': self.course.id,
                               'lecture_id': self.lecture.id
                           })

    def test_post_with_lecture_from_different_course_returns_404(self):
        new_course = CourseFactory()
        new_lecture = Lecture.objects.create(course=new_course,
                                             week=new_course.weeks.first(),
                                             date=new_course.weeks.first().start_date)
        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.post(reverse('dashboard:education:course-management:edit-lecture',
                                 kwargs={
                                     'course_id': self.course.id,
                                     'lecture_id': new_lecture.id
                                 }))

            self.response_404(response)

    def test_post_with_valid_data_redirects_to_course_detail(self):
        previous_date = self.lecture.date
        data = {
            'date': self.lecture.date + timezone.timedelta(days=1)
        }

        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.lecture.refresh_from_db()

            self.assertNotEqual(previous_date, self.lecture.date)
            self.assertRedirects(response, expected_url=reverse('dashboard:education:user-course-detail',
                                                                kwargs={
                                                                    'course_id': self.course.id
                                                                }))

    def test_post_with_date_outside_of_week_date_does_not_create_lecture(self):
        current_lecture_count = Lecture.objects.count()
        data = {
            'date': self.lecture.week.end_date + timezone.timedelta(days=1)
        }

        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.post(self.url, data=data)
            form = response.context_data.get('form')

            self.assertFalse(form.is_valid())
            self.assertEqual(current_lecture_count, Lecture.objects.count())


class TestAllStudentSolutionsView(TestCase):
    def setUp(self):
        self.test_password = faker.password()
        self.course = CourseFactory()
        self.teacher = TeacherFactory(password=self.test_password)
        add_teacher(course=self.course, teacher=self.teacher)
        self.task = IncludedTaskFactory(topic__course=self.course)
        self.student = StudentFactory(password=self.test_password)
        add_student(course=self.course, student=self.student)
        self.url = reverse('dashboard:education:all-students-solutions',
                           kwargs={
                               'course_id': self.course.id,
                               'task_id': self.task.id,
                           })
        self.student.is_active = True
        self.teacher.is_active = True
        self.student.save()
        self.teacher.save()

    def test_can_not_access_view_if_not_teacher_for_course(self):
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.response_403(response)

    def test_can_access_view_if_teacher_for_course(self):
        with self.login(email=self.teacher.email, password=self.test_password):
            self.get_check_200(self.url)

    def test_statistics_are_zero_when_there_are_no_solutions_for_task(self):
        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.response_200(response)
            self.assertEqual(0, response.context['solution_statistics'].get(
                'students_with_a_submitted_solution_count')
            )
            self.assertEqual(0, response.context['solution_statistics'].get(
                'students_with_a_passing_solution_count')
            )

    def test_students_with_passing_solution_count_is_still_zero_when_task_gradable_and_solution_is_wrong(self):
        self.task.gradable = True
        self.task.save()
        SolutionFactory(student=self.student, task=self.task, status=Solution.NOT_OK)
        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.response_200(response)
            self.assertEqual(1, response.context['solution_statistics'].get(
                'students_with_a_submitted_solution_count')
            )
            self.assertEqual(0, response.context['solution_statistics'].get(
                'students_with_a_passing_solution_count')
            )

    def test_passing_solution_count_is_one_when_passing_solution_for_gradable_task_is_submitted(self):
        self.task.gradable = True
        self.task.save()
        SolutionFactory(student=self.student, task=self.task, status=Solution.OK)
        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.response_200(response)
            self.assertEqual(1, response.context['solution_statistics'].get(
                'students_with_a_submitted_solution_count')
            )
            self.assertEqual(1, response.context['solution_statistics'].get(
                'students_with_a_passing_solution_count')
            )

    def test_no_students_are_shown_on_correct_filter_when_no_passing_solutions_for_task(self):
        self.task.gradable = True
        self.task.save()
        SolutionFactory(student=self.student, task=self.task, status=Solution.NOT_OK)
        self.url = self.url + "?status=correct"

        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.response_200(response)
            self.assertEqual(0, len(response.context['object_list']))

    def test_student_is_shown_on_correct_filter_when_passing_solution_for_task(self):
        self.task.gradable = True
        self.task.save()
        SolutionFactory(student=self.student, task=self.task, status=Solution.OK)
        self.url = self.url + "?status=correct"

        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.response_200(response)
            self.assertEqual(1, len(response.context['object_list']))


class TestSendEmailToAllStudentsView(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.students = StudentFactory.create_batch(size=5)

        for student in self.students:
            add_student(course=self.course, student=student)

        self.test_password = faker.password()
        self.teacher = Teacher.objects.create_from_user(BaseUserFactory(password=self.test_password))
        add_teacher(course=self.course, teacher=self.teacher)
        self.url = reverse('dashboard:education:course-management:send-email-to-all-students',
                           kwargs={
                               'course_id': self.course.id
                           })

    @override_settings(USE_DJANGO_EMAIL_BACKEND=False)
    @patch('odin.common.tasks.send_template_mail.delay')
    def test_post_sends_email_to_all_students(self, mock_send_mail):
        data = {
            'text': faker.text()
        }

        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.assertRedirects(response, expected_url=reverse('dashboard:education:user-course-detail',
                                                                kwargs={
                                                                    'course_id': self.course.id
                                                                }))
            self.assertTrue(mock_send_mail.called)
            (template_name, recipients, context), kwargs = mock_send_mail.call_args
            student_emails = [student.email for student in sorted(self.students, key=lambda x: x.id)]
            self.assertEqual(recipients, student_emails)


class TestCreateSolutionCommentView(TestCase):
    def setUp(self):
        self.course = CourseFactory()
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)
        self.teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(course=self.course, teacher=self.teacher)
        self.student = Student.objects.create_from_user(BaseUserFactory())
        add_student(course=self.course, student=self.student)
        self.task = IncludedTaskFactory(topic__course=self.course, gradable=False)
        self.solution = SolutionFactory(task=self.task, student=self.student)
        self.url = reverse('dashboard:education:create-solution-comment',
                           kwargs={
                               'course_id': self.course.id,
                           })

    def test_get_is_not_allowed(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.response_405(response)

    def test_post_with_valid_data_creates_solution_comment_for_correct_solution(self):
        current_solution_comment_count = SolutionComment.objects.count()
        data = {
            'solution': self.solution.id,
            'student': self.student.id,
            'text': faker.text()
        }

        with self.login(email=self.user.email, password=self.test_password):
            self.post(self.url, data=data)
            self.assertEqual(current_solution_comment_count + 1, SolutionComment.objects.count())
            last_comment = SolutionComment.objects.last()
            solution_comments = self.solution.comments.all()
            self.assertIn(last_comment, solution_comments)

    def test_post_with_valid_data_redirects_to_specific_comments_section(self):
        data = {
            'solution': self.solution.id,
            'student': self.student.id,
            'text': faker.text()
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            expected_url = reverse('dashboard:education:student-solution-detail',
                                   kwargs={
                                       'course_id': self.course.id,
                                       'task_id': self.task.id,
                                       'solution_id': self.solution.id,
                                   }) + f'#comments-section_{self.solution.id}'

            self.assertRedirects(response, expected_url=expected_url)

    def test_post_with_invalid_student_returns_404(self):
        new_student = Student.objects.create_from_user(BaseUserFactory())
        data = {
            'solution': self.solution.id,
            'student': new_student.id,
            'text': faker.text()
        }
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.response_404(response)
