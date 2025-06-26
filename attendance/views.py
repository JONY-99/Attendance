from .models import Lesson, Attendance, UserModel
from .serializers import LessonSerializer, AttendanceSerializer, RegisterSerializer
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def perform_create(self, serializer):
        lesson = serializer.save()
        lesson.generate_qr()
        lesson.save(update_fields=['qr_code'])

    @action(detail=True, methods=['get'])
    def generate_qr(self, request, pk=None):
        lesson = self.get_object()

    # QR kodni generate qilish
        lesson.generate_qr()

    # Saqlash
        lesson.save(update_fields=['qr_code'])

    # Fayl mavjudligini tekshirish
        if not lesson.qr_code:
            return Response(
                {"error": "QR kod saqlanmadi."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    # To‘liq URL hosil qilish
        full_url = request.build_absolute_uri(lesson.qr_code.url)

        return Response({'qr_code_url': full_url})
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
    operation_summary="Ustozning darslari",
    operation_description="Tizimga kirgan ustoz uchun biriktirilgan barcha darslar ro'yxatini qaytaradi.",
    responses={200: LessonSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_lessons(request):
    user = request.user
    if str(user.role) != "2":
        return Response({"error": "Faqat ustozlar uchun"}, status=403)

    lessons = Lesson.objects.filter(teacher=user)
    serializer = LessonSerializer(lessons, many=True)
    return Response(serializer.data)



# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Lesson
from accounts.serializers import RegisterSerializer


class LessonStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
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
    def get(self, request):
        lesson_id = request.query_params.get("lesson_id")

        if not lesson_id or not lesson_id.isdigit():
            return Response({"error": "lesson_id raqam bo'lishi kerak"}, status=400)

        lesson = Lesson.objects.filter(id=int(lesson_id)).first()
        if lesson is None:
            return Response({"error": "Bunday dars topilmadi"}, status=404)

        students = lesson.subject.classroom.students.all()
        serializer = RegisterSerializer(students, many=True)
        return Response({"students": serializer.data})
    

class NotifyStudentsAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        lesson_id = request.data.get("lesson_id")
        subject = Lesson.objects.get(id=lesson_id).subject.name
        qr_code = Lesson.objects.get(id=lesson_id).qr_code.url
        students = Lesson.objects.get(id=lesson_id).subject.classroom.students.all()
        
        result = []
        for student in students:
            if student.telegram_id:
                result.append({
                    "telegram_id": student.telegram_id,
                    "subject": subject,
                    "qr_code": qr_code,
                })

        return Response(result)


