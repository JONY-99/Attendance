from .models import Lesson, Attendance, UserModel
from .serializers import LessonSerializer, AttendanceSerializer, RegisterSerializer,  LessonCreateSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from django.utils import timezone

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    create_lesson_serializer_class = LessonCreateSerializer
    permission_classes = [IsAuthenticated]

    
     

    @swagger_auto_schema(
        method='get',
        operation_summary="QR kod yaratish",
        operation_description="Darsga QR kod generatsiya qiladi.",
        responses={200: openapi.Response('QR code URL')}
    )
    @action(detail=True, methods=['get'])
    def generate_qr(self, request):
        lesson = self.get_object()
        lesson.generate_qr()
        lesson.save(update_fields=['qr_code'])

        if not lesson.qr_code:
            return Response({"error": "QR kod saqlanmadi."}, status=500)

        full_url = request.build_absolute_uri(lesson.qr_code.url)
        return Response({'qr_code_url': full_url})

    @swagger_auto_schema(
        method='post',
        operation_summary="Davomat belgilash",
        operation_description="O'quvchi QR orqali davomatni belgilaydi.",
        responses={201: AttendanceSerializer, 403: 'Forbidden', 400: 'Already marked'}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_attendance(self, request, pk=None):
        user = request.user
        lesson = self.get_object()

        if str(user.role) != "1":
            return Response({'detail': 'Only students can mark attendance'}, status=403)

        if user not in lesson.subject.classroom.students.all():
            return Response({'detail': 'You are not in this class'}, status=403)

        if Attendance.objects.filter(student=user, lesson=lesson).exists():
            return Response({'detail': 'Attendance already marked'}, status=400)

        now = timezone.now()
        lesson_date = lesson.date
        if timezone.is_naive(lesson_date):
            lesson_date = timezone.make_aware(lesson_date)

        late_minutes = int((now - lesson_date).total_seconds() // 60)

        attendance = Attendance.objects.create(
            student=user,
            lesson=lesson,
            late_minutes=late_minutes if late_minutes > 0 else 0
        )

        return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method='get',
        operation_summary="Ustozning barcha darslari",
        responses={200: LessonSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='teacher')
    def teacher_lessons(self, request):
        if str(request.user.role) != "2":
            return Response({"error": "Faqat ustozlar uchun"}, status=403)

        lessons = Lesson.objects.filter(teacher=request.user)
        serializer = self.get_serializer(lessons, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='get',
        operation_summary="Darsga biriktirilgan o‘quvchilar",
        manual_parameters=[
            openapi.Parameter(
                'lesson_id',
                openapi.IN_QUERY,
                description="Dars IDsi",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={200: RegisterSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='students')
    def lesson_students(self, request):
        lesson_id = request.query_params.get("lesson_id")

        if not lesson_id or not lesson_id.isdigit():
            return Response({"error": "lesson_id raqam bo'lishi kerak"}, status=400)

        lesson = Lesson.objects.filter(id=int(lesson_id)).first()
        if lesson is None:
            return Response({"error": "Bunday dars topilmadi"}, status=404)

        students = lesson.subject.classroom.students.all()
        serializer = RegisterSerializer(students, many=True)
        return Response({"students": serializer.data})

    @swagger_auto_schema(
        method='post',
        operation_summary="O‘quvchilarga bildirishnoma (QR + fan nomi)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'lesson_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['lesson_id']
        ),
        responses={200: openapi.Response('Success')}
    )
    @action(detail=False, methods=['post'], url_path='notify')
    def notify_students(self, request):
        lesson_id = request.data.get("lesson_id")
        lesson = Lesson.objects.filter(id=lesson_id).first()
        if not lesson:
            return Response({"error": "Dars topilmadi"}, status=404)

        subject = lesson.subject.name
        qr_code = lesson.qr_code.url if lesson.qr_code else ""
        students = lesson.subject.classroom.students.all()

        result = []
        for student in students:
            if student.telegram_id:
                result.append({
                    "telegram_id": student.telegram_id,
                    "subject": subject,
                    "qr_code": qr_code,
                })

        return Response(result)

    @swagger_auto_schema(
        method='get',
        operation_summary="O‘quvchining davomatlari",
        manual_parameters=[
            openapi.Parameter(
                'telegram_id',
                openapi.IN_PATH,
                description="Telegram ID",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: AttendanceSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='attendance-stat/(?P<telegram_id>[^/.]+)')
    def attendance_stat(self, request, telegram_id):
        if str(request.user.role) != "1":
            return Response({"error": "Faqat o'quvchilar uchun"}, status=403)

        user = UserModel.objects.filter(telegram_id=telegram_id).first()
        if not user:
            return Response({"error": "Bunday o'quvchi topilmadi"}, status=404)

        attendance = Attendance.objects.filter(student=user)
        serializer = AttendanceSerializer(attendance, many=True)
        return Response(serializer.data)
    


 
@swagger_auto_schema(
    method='post',
    operation_summary="Yangi dars yaratish",
    operation_description="Bu endpoint orqali yangi dars (lesson) yaratiladi.",
    request_body=LessonCreateSerializer,
    responses={
        201: openapi.Response("Yaratilgan dars ma'lumotlari", LessonSerializer),
        400: "Xatolik"
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def lesson_created(request):
    serializer = LessonCreateSerializer(data=request.data)
    if serializer.is_valid():
        lesson = serializer.save()
        lesson.generate_qr()  # QR yaratish (agar metod bo‘lsa)
        lesson.save(update_fields=['qr_code'])
        return Response(LessonSerializer(lesson).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

