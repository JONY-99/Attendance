from django.urls import path
from .views import LessonViewSet, lesson_created

# ViewSet metodlarini `as_view` bilan bog‘laymiz
lesson_list = LessonViewSet.as_view({'get': 'list', 'post': 'create'})
lesson_detail = LessonViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
generate_qr = LessonViewSet.as_view({'get': 'generate_qr'})
mark_attendance = LessonViewSet.as_view({'post': 'mark_attendance'})
teacher_lessons = LessonViewSet.as_view({'get': 'teacher_lessons'})
attendance_stat = LessonViewSet.as_view({'get': 'attendance_stat'})
create_lesson = LessonViewSet.as_view({'post': 'create_lesson'})

urlpatterns = [
    # ✅ Darslar bilan ishlash
    path("lessons/", lesson_list, name="lesson-list"),
    path("lessons/<int:pk>/", lesson_detail, name="lesson-detail"),
    path("lessons/<int:pk>/generate_qr/", generate_qr, name="lesson-generate-qr"),
    path("lessons/<int:pk>/mark_attendance/", mark_attendance, name="lesson-mark-attendance"),

    # ✅ Ustozga tegishli barcha darslar
    path("lessons/teacher/", teacher_lessons, name="teacher-lessons"),
    path("lessons/create/", create_lesson, name="create-lesson"),

]