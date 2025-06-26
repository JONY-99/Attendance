from rest_framework import serializers
from .models import ClassRoom, Subject, Lesson, Attendance
from accounts.serializers import RegisterSerializer


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoom
        fields = ['id', 'name', 'teacher', 'students']

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'classroom', 'subject', 'teacher']  # replace with actual Subject model fields

class LessonSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name')
    time = serializers.SerializerMethodField()
    classroom_id = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'subject', 'subject_name', 'date', 'time', 'qr_code', 'is_active', 'classroom_id']
        read_only_fields = ['qr_code', 'date']

    def get_time(self, obj):
        return obj.date.strftime('%H:%M')  # soat:daqiqa formatda
    
    def get_subject_name(self, obj):
        return obj.subject.name

    def get_classroom_id(self, obj):
        return obj.subject.classroom.id


class AttendanceSerializer(serializers.ModelSerializer):
    student = RegisterSerializer(read_only=True)
    is_present = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'lesson', 'created_at', 'late_minutes', 'is_present']

    def get_is_present(self, obj):
        return getattr(obj, 'created_at', None) is not None
    


class LessonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['subject', 'date', 'is_active']  # kerakli fieldlar
