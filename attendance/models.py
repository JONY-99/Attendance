from django.db import models
from accounts.models import UserModel
import qrcode
from django.utils import timezone
from django.core.files.base import ContentFile
from io import BytesIO


class ClassRoom(models.Model):
    name = models.CharField(max_length=100)
    students = models.ManyToManyField(UserModel, limit_choices_to={'role': '1'}, related_name='classrooms')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='subjects')
    teacher = models.ForeignKey(UserModel, on_delete=models.CASCADE, limit_choices_to={'role': '2'})

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.classroom.name}"


class Lesson(models.Model):
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey(UserModel, on_delete=models.CASCADE, limit_choices_to={'role': '2'})
    date = models.DateTimeField(default=timezone.now)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_qr(self):
        qr_data = f"lesson:{self.id}"
        qr = qrcode.make(qr_data)

        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        filename = f"lesson_{self.id}_qr.png"

        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        buffer.close()

    def save(self, *args, **kwargs):
        if not self.teacher:
            self.teacher = self.subject.teacher
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject.name} - {self.date.strftime('%Y-%m-%d %H:%M')}"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', '✅ Keldi'),
        ('late', '⏰ Kechikdi'),
        ('absent', '❌ Kelmadi'),
    )

    student = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        limit_choices_to={'role': '1'},
        related_name='attendances'
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    late_minutes = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('lesson', 'student')

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.lesson} - {self.status}"
    

 