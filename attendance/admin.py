from django.contrib import admin
from .models import Lesson, ClassRoom, Attendance, Subject

admin.site.register(Lesson)
admin.site.register(ClassRoom)
admin.site.register(Attendance)
admin.site.register(Subject)