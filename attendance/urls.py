from django.urls import path
from attendance.views import LessonStudentsAPIView, NotifyStudentsAPIView
from .views import (
    LessonViewSet,
    teacher_lessons,
)

# ViewSet metodlarini `as_view` bilan path'ga biriktiramiz
lesson_list = LessonViewSet.as_view({'get': 'list', 'post': 'create'})
lesson_detail = LessonViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
generate_qr = LessonViewSet.as_view({'get': 'generate_qr'})
mark_attendance_view = LessonViewSet.as_view({'post': 'mark_attendance'})

urlpatterns = [
    # ✅ Faqat ustozlar uchun darslar
    path("teacher_lessons/", teacher_lessons, name="teacher-lessons"),

    # ✅ LessonViewSet uchun yo‘llar
    path("lessons/", lesson_list, name="lesson-list"),
    path("lessons/<int:pk>/", lesson_detail, name="lesson-detail"),
    path("lessons/<int:pk>/generate_qr/", generate_qr, name="lesson-generate-qr"),
    path("lessons/<int:pk>/mark_attendance/", mark_attendance_view, name="lesson-mark-attendance"),
    path('lesson_students/', LessonStudentsAPIView.as_view(), name='lesson-students'),
    path('notify_lesson_students/', NotifyStudentsAPIView.as_view(), name='notify-lesson-students'),

    
]
