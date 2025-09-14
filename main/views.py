from datetime import timedelta

from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth import logout
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re

from django.db.models import Count
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.urls import reverse
from .forms import PlacementTestReservationForm, EnrollmentRequestForm, AssignmentForm, CommentForm, ConversationForm, \
    EducationalPostForm
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from .models import PlacementTestReservation, ENGLISH_LEVELS, EnrollmentRequest, CustomUser, Rating, Assignment, \
    AssignmentSubmission, Comment, Conversation, EducationalPost, Exam, ExamSubmission
from .models import Course, Enrollment
from .forms import CourseForm
from django.shortcuts import get_object_or_404
from .forms import StudentSearchForm, AddStudentToCourseForm


User = get_user_model()


def home(request):
    top_teachers = User.objects.filter(user_type='teacher')[:4]
    top_conversations = Conversation.objects.annotate(
        comment_count=Count("comments")
    ).order_by("-comment_count")[:4]
    latest_posts = EducationalPost.objects.all()[:4]
    context = {
        "top_conversations": top_conversations,
        "latest_posts": latest_posts,
        "top_teachers": top_teachers,
    }
    return render(request, 'home.html', context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.user_type == 'teacher':
                return redirect('home')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Wrong username or password!')

    return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        user_type = request.POST.get('user_type', '').strip()
        registration_code = request.POST.get('registration_code', '').strip()

        if not username or not email or not password or not confirm or not user_type:
            messages.error(request, 'All fields are required, including user type.')
            return redirect('signup')

        if user_type == 'teacher':
            VALID_CODE = "moon123789@"
            if registration_code != VALID_CODE:
                messages.error(request, 'Invalid registration code for teacher.')
                return redirect('signup')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email address.')
            return redirect('signup')

        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
        if not re.match(password_regex, password):
            messages.error(request,
                           'Password must be at least 8 characters and include uppercase, lowercase, number, and special character.')
            return redirect('signup')

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken!')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered!')
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.user_type = user_type
        user.save()
        return redirect('login')

    return render(request, 'signup.html')


@login_required
def student_dashboard(request):
    student = request.user
    level = student.level

    enrollments = Enrollment.objects.filter(student=student).select_related('course')

    passed = enrollments.filter(grade__gte=60)
    failed = enrollments.filter(grade__lt=60)
    in_progress = enrollments.filter(grade__isnull=True)

    assignments_notifications = {}
    for enroll in in_progress:
        course = enroll.course
        active_assignments = Assignment.objects.filter(course=course, deadline__gt=timezone.now())

        unseen_count = 0
        for assignment in active_assignments:
            submitted = AssignmentSubmission.objects.filter(student=student, assignment=assignment).exists()
            if not submitted:
                unseen_count += 1

        assignments_notifications[course.id] = unseen_count

    context = {
        'level': level,
        'passed': passed,
        'failed': failed,
        'in_progress': in_progress,
        'assignments_notifications': assignments_notifications,
    }
    return render(request, 'student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    return render(request, 'teacher_dashboard.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def placement_test(request):
    teacher = User.objects.get(username='Mahdieh Arabi')
    if request.method == 'POST':
        form = PlacementTestReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.assigned_teacher = teacher
            reservation.save()
            return redirect('reservation_success')
    else:
        form = PlacementTestReservationForm()
    return render(request, 'placement_test.html', {'form': form})


@login_required
def reservation_success(request):
    return render(request, 'reservation_success.html')


def get_reserved_times(request):
    date = request.GET.get('date')
    if date:
        reserved = PlacementTestReservation.objects.filter(date=date).values_list('time', flat=True)
        times = [t.strftime('%H:%M') for t in reserved]
        return JsonResponse({'reserved_times': times})
    return JsonResponse({'reserved_times': []})


@login_required
def teacher_dashboard(request):
    if request.user.user_type != 'teacher':
        return redirect('home')
    t = User.objects.get(username='Mahdieh Arabi')

    courses = Course.objects.filter(teacher=request.user)
    unseen_count = EnrollmentRequest.objects.filter(course__in=courses, is_seen=False).count()
    unseen_level_test = PlacementTestReservation.objects.filter(assigned_teacher=t, is_seen=False).count()
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            return redirect('teacher_dashboard')
    else:
        form = CourseForm()

    return render(request, 'teacher_dashboard.html', {
        'form': form,
        'courses': courses,
        'unseen_count': unseen_count,
        'unseen_level_test': unseen_level_test
    })


def search_students(request):
    form = StudentSearchForm(request.GET or None)
    results = []
    add_forms = {}

    if form.is_valid():
        query = form.cleaned_data['query']
        results = User.objects.filter(user_type='student', username__icontains=query)

        for student in results:
            add_forms[student.id] = AddStudentToCourseForm(
                initial={'student_id': student.id},
                teacher=request.user
            )

    return render(request, 'search_students.html', {
        'form': form,
        'results': results,
        'ENGLISH_LEVELS': ENGLISH_LEVELS,
        'add_forms': add_forms,
    })


def add_student_to_course(request):
    if request.method == 'POST':
        form = AddStudentToCourseForm(request.POST, teacher=request.user)
        if form.is_valid():
            student = get_object_or_404(User, pk=form.cleaned_data['student_id'], user_type='student')
            course = form.cleaned_data['course_id']

            enrollment, created = Enrollment.objects.get_or_create(student=student, course=course)

            if created:
                messages.success(request, f"{student.username} added to {course.title}.")
            else:
                messages.info(request, f"{student.username} is already enrolled in {course.title}.")

            return redirect('search_students')
    return redirect('teacher_dashboard')


@require_POST
def set_student_level(request, student_id):
    student = get_object_or_404(User, pk=student_id, user_type='student')
    level = request.POST.get('level')
    if level:
        student.level = level
        student.save()
    return redirect('search_students')


@login_required
def courses_list(request):
    user = request.user
    today = timezone.now().date()

    # if user.user_type == 'student' and hasattr(user, 'level'):
    #     courses = Course.objects.filter(required_level=user.level)
    # else:
    courses = Course.objects.all()

    for course in courses:
        registration_deadline = course.start_date - timedelta(days=2)
        course.registration_open = today <= registration_deadline
        course.remaining_days = (registration_deadline - today).days if course.registration_open else 0

    return render(request, 'courses_list.html', {'courses': courses})


def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    context = {
        'course': course,
        'enrollments': enrollments,
    }
    return render(request, 'course_detail.html', context)


def remove_student_from_course(request, course_id, student_id):
    course = get_object_or_404(Course, pk=course_id, teacher=request.user)
    student = get_object_or_404(User, pk=student_id, user_type='student')
    Enrollment.objects.filter(student=student, course=course).delete()
    course.students.remove(student)
    messages.success(request, f"Student {student.username} removed from {course.title}.")
    return redirect('course_detail', course_id=course_id)


@login_required
@require_POST
def set_student_grade(request, course_id, student_id):
    course = get_object_or_404(Course, pk=course_id)
    if course.teacher != request.user:
        return HttpResponseForbidden("You are not authorized to edit grades for this course.")

    enrollment = get_object_or_404(Enrollment, course=course, student__id=student_id)
    grade = request.POST.get('grade')

    try:
        grade = int(grade)
        if grade < 0 or grade > 100:
            raise ValueError
    except (ValueError, TypeError):
        return redirect(reverse('course_detail', args=[course_id]))

    enrollment.grade = grade
    enrollment.save()

    return redirect(reverse('course_detail', args=[course_id]))


@login_required
def send_enrollment_request(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user.user_type != 'student':
        return redirect('home')

    if EnrollmentRequest.objects.filter(student=request.user, course=course).exists():
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = EnrollmentRequestForm(request.POST)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = request.user
            enrollment.course = course
            enrollment.save()
            return redirect('student_dashboard')
    else:
        form = EnrollmentRequestForm(initial={
            'email': request.user.email,
        })

    return render(request, 'send_enrollment_request.html', {
        'form': form,
        'course': course,
        'student_level': request.user.level
    })


@login_required
def view_requests(request):
    if request.user.user_type != 'teacher':
        return redirect('home')

    courses = Course.objects.filter(teacher=request.user)
    requests_list = EnrollmentRequest.objects.filter(course__in=courses).order_by('-created_at')

    requests_list.filter(is_seen=False).update(is_seen=True)

    return render(request, 'teacher_requests.html', {'requests': requests_list})


@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    course.delete()
    return redirect('teacher_dashboard')


@login_required
@require_POST
def set_course_link(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if course.teacher != request.user:
        return HttpResponseForbidden("You are not allowed to edit this course.")

    link = request.POST.get('join_link')
    course.join_link = link
    course.save()

    return redirect('course_detail', course_id=course_id)


@login_required
def student_profile_detail(request, student_id):
    student = get_object_or_404(User, pk=student_id, user_type='student')
    source = request.GET.get("from")

    passed_enrollments = Enrollment.objects.filter(student=student, grade__gte=60)
    failed_enrollments = Enrollment.objects.filter(student=student, grade__lt=60)
    current_enrollments = Enrollment.objects.filter(student=student, grade__isnull=True)

    context = {
        'student': student,
        'passed_enrollments': passed_enrollments,
        'failed_enrollments': failed_enrollments,
        'current_enrollments': current_enrollments,
        'source': source
    }
    return render(request, 'see_student_profile.html', context)


@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        profile_picture = request.FILES.get('profile_picture')

        if username != user.username and CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken!')
            return redirect('edit_profile')
        else:
            user.username = username

        if email != user.email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Invalid Email Address!')
                return redirect('edit_profile')

            if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, 'This Email has been registered!')
                return redirect('edit_profile')
            else:
                user.email = email

        if profile_picture:
            user.profile_image = profile_picture

        if new_password:
            if not current_password:
                messages.error(request, 'Enter your current Password.')
                return redirect('edit_profile')

            if not user.check_password(current_password):
                messages.error(request, 'Incorrect Password')
                return redirect('edit_profile')

            password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
            if not re.match(password_regex, new_password):
                messages.error(request, 'Password requirements: 8 characters, small and capital letters, special chars')
                return redirect('edit_profile')

            if new_password != confirm_password:
                messages.error(request, 'Passwords dont match!')
                return redirect('edit_profile')

            user.set_password(new_password)
            update_session_auth_hash(request, user)

        user.save()
        if user.user_type == 'teacher':
            return redirect('teacher_dashboard')
        else:
            return redirect('student_dashboard')

    return render(request, 'edit_profile.html')


def teacher_list(request):
    teachers = User.objects.filter(user_type='teacher')
    rated_teachers = []
    related_teachers = []

    if request.user.is_authenticated and request.user.user_type == 'student':
        related_teachers = User.objects.filter(
            user_type='teacher',
            course__enrollment__student=request.user
        ).distinct()

        rated_teachers = User.objects.filter(
            user_type='teacher',
            received_ratings__student=request.user
        ).distinct()

    context = {
        'teachers': teachers,
        'rated_teachers': rated_teachers,
        'related_teachers': related_teachers,
    }
    return render(request, 'teacher_list.html', context)


@login_required
def rate_teacher(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, user_type='teacher')
    has_class = Enrollment.objects.filter(
        student=request.user,
        course__teacher=teacher
    ).exists()

    if not has_class:
        messages.error(request, "You can only rate teachers you've had classes with.")
        return redirect('teacher_list')

    if request.method == 'POST':
        try:
            score = int(request.POST.get('score'))
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating value.")
            return redirect('teacher_list')

        if score < 1 or score > 5:
            messages.error(request, "Rating must be between 1 and 5.")
            return redirect('teacher_list')

        rating, created = Rating.objects.update_or_create(
            student=request.user,
            teacher=teacher,
            defaults={'score': score}
        )

        messages.success(request, "Your rating has been submitted.")
        return redirect('teacher_list')

    return redirect('teacher_list')


@login_required
def assignment_list_create(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course = course
            assignment.save()
            return redirect('assignment_list_create', course_id=course.id)
    else:
        form = AssignmentForm()

    assignments = course.assignments.all().order_by('-created_at')
    return render(request, 'assignment_list.html', {
        'course': course,
        'form': form,
        'assignments': assignments,
    })


@login_required
def student_assignments_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course=course)

    submissions = AssignmentSubmission.objects.filter(
        student=request.user,
        assignment__in=assignments
    )
    submitted_assignment_ids = submissions.values_list('assignment_id', flat=True)

    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id')
        uploaded_file = request.FILES.get('file')

        if assignment_id and uploaded_file:
            assignment = get_object_or_404(Assignment, id=assignment_id)

            if timezone.now() > assignment.deadline:
                return render(request, 'assignment_error.html', {
                    'message': 'Deadline has passed. You can no longer submit this assignment.'
                })

            if AssignmentSubmission.objects.filter(student=request.user, assignment=assignment).exists():
                return render(request, 'assignment_error.html', {
                    'message': 'You have already submitted this assignment.'
                })

            AssignmentSubmission.objects.create(
                assignment=assignment,
                student=request.user,
                submitted_file=uploaded_file
            )
            return redirect('student_assignments_view', course_id=course.id)

    return render(request, 'student_assignments.html', {
        'course': course,
        'assignments': assignments,
        'submitted_assignment_ids': list(submitted_assignment_ids),
        'submissions': submissions,
        'now': timezone.now()
    })


@login_required
def assignment_submissions_view(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = AssignmentSubmission.objects.filter(assignment=assignment)

    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback')

        submission = get_object_or_404(AssignmentSubmission, id=submission_id)
        submission.grade = grade
        submission.feedback = feedback
        submission.graded = True
        submission.save()

        return redirect('assignment_submissions_view', assignment_id=assignment.id)

    return render(request, 'assignment_submissions.html', {
        'assignment': assignment,
        'submissions': submissions
    })


CONVERSATION_TOPICS = [
    ('Reading Skills', 'Reading Skills'),
    ('English Grammar', 'English Grammar'),
    ('Speaking', 'Speaking'),
    ('Vocabulary and Idiom', 'Vocabulary and Idiom'),
    ('Daily Life', 'Daily Life'),
    ('Fun', 'Fun'),
    ('Social Topics', 'Social Topics'),
    ('Movies', 'Movies'),
    ('Books', 'Books'),
    ('Music', 'Music'),
]


def conversation_list(request):
    selected_topic = request.GET.get('topic')

    if selected_topic:
        conversations = Conversation.objects.filter(topic=selected_topic).select_related('user')
    else:
        conversations = Conversation.objects.all().select_related('user')

    if request.user.is_authenticated and request.GET.get('my_topics') == '1':
        conversations = conversations.filter(user=request.user)

    topic_counts = {
        topic[0]: Conversation.objects.filter(topic=topic[0]).count()
        for topic in CONVERSATION_TOPICS
    }

    top_users = User.objects.annotate(conversation_count=Count('conversations')).order_by('-conversation_count')[:5]

    return render(request, 'conversation_list.html', {
        'conversations': conversations,
        'selected_topic': selected_topic,
        'topic_counts': topic_counts,
        'topics': CONVERSATION_TOPICS,
        'top_users': top_users,
    })


def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    comments = conversation.comments.all().order_by('created')
    form = CommentForm()

    return render(request, 'conversation_detail.html', {
        'conversation': conversation,
        'comments': comments,
        'form': form
    })


@login_required
def conversation_create(request):
    if request.method == 'POST':
        form = ConversationForm(request.POST)
        if form.is_valid():
            conversation = form.save(commit=False)
            conversation.user = request.user
            conversation.save()
            form.save_m2m()
            conversation.participants.add(request.user)
            return redirect('conversation_detail', pk=conversation.pk)
    else:
        form = ConversationForm()

    return render(request, 'conversation_form.html', {'form': form})


@login_required
def comment_create(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.conversation = conversation
            comment.user = request.user
            comment.save()
            conversation.participants.add(request.user)
            return redirect('conversation_detail', pk=conversation.pk)
    return redirect('conversation_detail', pk=conversation.pk)


@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    if comment.is_liked_by(user):
        comment.likes.remove(user)
    else:
        comment.likes.add(user)

    return redirect('conversation_detail', pk=comment.conversation.pk)


def educational_post_list(request):
        posts = EducationalPost.objects.all()

        if request.user.is_authenticated and request.user.user_type == "teacher" and request.GET.get('my_posts') == '1':
            posts = posts.filter(teacher=request.user)

        return render(request, 'educational_post_list.html', {'posts': posts})

@login_required
def educational_post_create(request):
    if not request.user.is_teacher:
        return redirect('home')

    if request.method == 'POST':
        form = EducationalPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.teacher = request.user
            post.save()
            return redirect('educational_post_list')
    else:
        form = EducationalPostForm()

    return render(request, 'educational_post_form.html', {'form': form})


@login_required
def educational_post_update(request, pk):
    post = get_object_or_404(EducationalPost, pk=pk, teacher=request.user)

    if request.method == 'POST':
        form = EducationalPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('educational_post_list')
    else:
        form = EducationalPostForm(instance=post)

    return render(request, 'educational_post_form.html', {'form': form, 'post': post})


@login_required
def educational_post_delete(request, pk):
    post = get_object_or_404(EducationalPost, pk=pk, teacher=request.user)

    if request.method == 'POST':
        post.delete()
        return redirect('educational_post_list')
    return redirect('educational_post_list')


def post_detail(request, pk):
    post = get_object_or_404(EducationalPost, pk=pk)
    return render(request, 'post_detail.html', {'post': post})


def level_requests(request):
    teacher = User.objects.get(username='Mahdieh Arabi')
    reservations = PlacementTestReservation.objects.filter(assigned_teacher=teacher).order_by('-date')
    reservations.filter(is_seen=False).update(is_seen=True)
    return render(request, 'level_requests.html', {'reservations': reservations})


@login_required
def conversation_edit(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)

    if request.user != conversation.user:
        return redirect('conversation_detail', pk=pk)

    if request.method == 'POST':
        form = ConversationForm(request.POST, instance=conversation)
        if form.is_valid():
            form.save()
            return redirect('conversation_detail', pk=conversation.pk)
    else:
        form = ConversationForm(instance=conversation)

    return render(request, 'conversation_form.html', {'form': form, 'conversation': conversation})


@login_required()
def conversation_delete(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)

    if request.user == conversation.user:
        conversation.delete()

    return redirect('conversation_list')


def contact(request):
    return render(request, "contact_us.html")

def about(request):
    return render(request, "about.html")


def exam_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    exams = Exam.objects.filter(course=course)
    return render(request, 'exam_list.html', {
        'course': course,
        'exams': exams
    })

@login_required
def add_exam(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user != course.teacher:
        return redirect("exam_list", course_id=course.id)

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        deadline = request.POST.get("deadline")
        file = request.FILES.get("file")

        Exam.objects.create(
            course=course,
            title=title,
            description=description,
            deadline=deadline,
            file=file
        )
        return redirect("exam_list", course_id=course.id)

    return render(request, "add_exam.html", {"course": course})


# @login_required
# def submit_exam(request, exam_id):
#     exam = get_object_or_404(Exam, id=exam_id)
#     if request.method == "POST":
#         file = request.FILES.get("file")
#         ExamSubmission.objects.create(
#             exam=exam,
#             student=request.user,
#             file=file
#         )
#         return redirect("exam_list", course_id=exam.course.id)
#     return render(request, "submit_exam.html", {"exam": exam})


@login_required
def grade_exams(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    submissions = exam.submissions.all()
    if request.method == "POST":
        for sub in submissions:
            grade = request.POST.get(f"grade_{sub.id}")
            if grade:
                sub.grade = grade
                sub.save()
        return redirect("grade_submissions", exam_id=exam.id)
    return render(request, "grade_exams.html", {"exam": exam, "submissions": submissions})



@login_required
def exam_update(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.user != exam.course.teacher:
        messages.error(request, "not allowed")
        return redirect("exam_list", course_id=exam.course.id)

    if request.method == "POST":
        exam.title = request.POST.get("title")
        exam.description = request.POST.get("description")
        exam.deadline = request.POST.get("deadline")
        exam.save()
        messages.success(request)
        return redirect("exam_list", course_id=exam.course.id)

    return render(request, "exam_update.html", {"exam": exam})


@login_required
def exam_delete(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    course = exam.course
    if request.user != course.teacher:
        messages.error(request, "not allowed.")
        return redirect("exam_list", course_id=course.id)

    exam.delete()
    messages.success(request)
    return redirect("exam_list", course_id=course.id)

@login_required
def exam_submissions_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    submissions = ExamSubmission.objects.filter(exam=exam)

    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        grade = request.POST.get('grade')

        submission = get_object_or_404(ExamSubmission, id=submission_id)
        submission.grade = grade
        submission.graded = True
        submission.save()

        return redirect('exam_submissions_view', exam_id=exam.id)

    return render(request, 'grade_exams.html', {
        'exam': exam,
        'submissions': submissions
    })


@login_required
def student_exams_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    exams = Exam.objects.filter(course=course)
    submissions = ExamSubmission.objects.filter(student=request.user, exam__in=exams)
    submitted_exam_ids = submissions.values_list('exam_id', flat=True)

    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        uploaded_file = request.FILES.get('file')

        if exam_id and uploaded_file:
            exam = get_object_or_404(Exam, id=exam_id)

            if exam.deadline and timezone.now() > exam.deadline:
                return render(request, 'assignment_error.html')

            if ExamSubmission.objects.filter(student=request.user, exam=exam).exists():
                return render(request, 'assignment_error.html')

            ExamSubmission.objects.create(
                exam=exam,
                student=request.user,
                file=uploaded_file
            )
            return redirect('student_course_exams', course_id=course.id)

    return render(request, 'student_exams.html', {
        'course': course,
        'exams': exams,
        'submitted_exam_ids': list(submitted_exam_ids),
        'submissions': submissions,
        'now': timezone.now()
    })
