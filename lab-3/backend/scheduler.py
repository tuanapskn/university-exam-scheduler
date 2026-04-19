"""
Sınav Planlama Algoritması
==========================

Proje 2 ve 3 gereksinimlerini karşılayan kısıtlama kontrol sistemi ile sınav planlaması.

Kısıtlar:
1. Aynı öğrencinin aynı saatte 2 sınavı olamaz
2. Aynı derslikte aynı anda 2 sınav olamaz
3. Derslik kapasitesi yeterli olmalı
4. Öğretim üyesi müsait olduğu saatlerde sınava sahip olabilir
5. Bir derse tek sınav atanır
6. Sınav süresi dersin exam_duration alanı kadar olur
"""

import datetime
from sqlalchemy import and_


def schedule_exams(db, days=5, department_id=None, force=False):
    """
    Otomatik sınav planlama algoritması (Proximity-aware bölme ile).
    
    Args:
        db: SQLAlchemy DB instance
        days: Planlama yapılacak gün sayısı
        department_id: Bölüm ID (isteğe bağlı - belirtilirse sadece o bölümü planla)
        force: True ise mevcut planları sil
        
    Returns:
        {
            'created': int,      # Planlanan sınav sayısı
            'failed': int,       # Planlayamayan sınav sayısı
            'message': str,      # Sonuç mesajı
            'exams': [...]       # Oluşturulan sınavlar
        }
    
    Kısıtlar:
    - Kapasite yetersizse yakın dersliklere sınav bölünür
    - Aynı sınav için birden çok oda kullanılabilir (aynı saat, aynı süre)
    - Yakın derslikler ClassroomProximity tablosundan alınır
    """
    from models import Course, Exam, Classroom, Enrollment, Teacher, User, ClassroomProximity
    
    # Mevcut planları temizle
    if force:
        db.session.query(Exam).delete()
        db.session.commit()
    
    # Planlanacak dersleri al
    courses_query = db.session.query(Course).filter(Course.has_exam == True)
    if department_id:
        courses_query = courses_query.filter(Course.department_id == department_id)
    
    courses = courses_query.all()
    
    if not courses:
        return {
            'created': 0,
            'failed': 0,
            'message': 'Planlanacak ders bulunamadı',
            'exams': []
        }
    
    # Zaman slotları oluştur
    base_date = datetime.date.today()
    time_windows = [
        datetime.time(9, 0),
        datetime.time(11, 30),
        datetime.time(14, 0),
        datetime.time(16, 30)
    ]
    
    slots = []
    for d in range(days):
        current_date = base_date + datetime.timedelta(days=d)
        weekday = current_date.strftime('%a')  # Mon, Tue, ...
        
        for time_window in time_windows:
            slot_datetime = datetime.datetime.combine(current_date, time_window)
            slots.append({
                'start': slot_datetime,
                'end': slot_datetime + datetime.timedelta(minutes=1440),  # Full day
                'date': current_date,
                'weekday': weekday
            })
    
    # Derslikler (kapasite büyükten küçüğe sıralı)
    classrooms = db.session.query(Classroom).filter(
        Classroom.is_available == True
    ).order_by(Classroom.capacity.desc()).all()
    
    if not classrooms:
        return {
            'created': 0,
            'failed': len(courses),
            'message': 'Uygun derslik yok',
            'exams': []
        }
    
    # Planlama sonuçları
    created_exams = []
    failed_courses = []
    
    # Öğretim üyesi müsaitlik ve meşgu saatleri
    teacher_busy = {}  # teacher_id -> [(start, end), ...]
    
    # Öğrenci sınav planları
    student_exams = {}  # student_id -> [(start, end), ...]
    
    # Derslik kullanımı
    room_usage = {}  # room_id -> [(start, end), ...]
    for room in classrooms:
        room_usage[room.id] = []
    
    # Mevcut sınavlar varsa ekle
    existing_exams = db.session.query(Exam).all()
    for exam in existing_exams:
        exam_end = exam.slot_start + datetime.timedelta(minutes=exam.duration)
        room_usage[exam.room_id].append((exam.slot_start, exam_end))
        
        # Hocanın meşgul saatini ekle
        course = db.session.query(Course).get(exam.course_id)
        if course and course.teacher_id:
            if course.teacher_id not in teacher_busy:
                teacher_busy[course.teacher_id] = []
            teacher_busy[course.teacher_id].append((exam.slot_start, exam_end))
        
        # Öğrencilerin meşgul saatini ekle
        enrollments = db.session.query(Enrollment).filter_by(
            course_id=exam.course_id
        ).all()
        for enrollment in enrollments:
            if enrollment.student_id not in student_exams:
                student_exams[enrollment.student_id] = []
            student_exams[enrollment.student_id].append((exam.slot_start, exam_end))
    
    # Her ders için slot bulmayı dene
    for course in courses:
        # Bu ders zaten planlandı mı?
        existing_exam = db.session.query(Exam).filter_by(
            course_id=course.id
        ).first()
        if existing_exam:
            continue
        
        scheduled = False
        
        # Slot'ları dene
        for slot in slots:
            if scheduled:
                break
            
            slot_start = slot['start']
            slot_end = slot_start + datetime.timedelta(minutes=course.exam_duration)
            
            # 1. Öğretim üyesi müsait mi?
            if course.teacher_id:
                teacher = db.session.query(Teacher).get(course.teacher_id)
                
                if teacher and teacher.available_days:
                    available_days = [d.strip() for d in teacher.available_days.split(',')]
                    if slot['weekday'] not in available_days:
                        continue  # Bu gün uygun değil
                
                # Hoca zaten meşgul mü?
                busy_slots = teacher_busy.get(course.teacher_id, [])
                teacher_conflict = False
                for busy_start, busy_end in busy_slots:
                    if not (slot_end <= busy_start or slot_start >= busy_end):
                        teacher_conflict = True
                        break
                
                if teacher_conflict:
                    continue
            
            # 2. Öğrenciler meşgul değil mi?
            enrollments = db.session.query(Enrollment).filter_by(
                course_id=course.id
            ).all()
            
            student_ids = {e.student_id for e in enrollments}
            student_conflict = False
            
            for student_id in student_ids:
                busy_slots = student_exams.get(student_id, [])
                for busy_start, busy_end in busy_slots:
                    if not (slot_end <= busy_start or slot_start >= busy_end):
                        student_conflict = True
                        break
                if student_conflict:
                    break
            
            if student_conflict:
                continue
            
            # 3. Uygun derslik bul (yakın derslikleri de dikkate al)
            assigned_rooms = []
            remaining_students = course.student_count
            
            for classroom in classrooms:
                if remaining_students <= 0:
                    break
                
                # Dersliğin kapasitesi yeterli mi?
                if classroom.capacity < remaining_students:
                    # Kapasite yetersizse yakın derslikleri kontrol et
                    nearby_rooms = db.session.query(ClassroomProximity).filter(
                        ClassroomProximity.primary_classroom_id == classroom.id
                    ).all()
                    
                    if not nearby_rooms:
                        continue
                
                # Derslik meşgul mü?
                room_conflict = False
                occupied_slots = room_usage.get(classroom.id, [])
                for occupied_start, occupied_end in occupied_slots:
                    if not (slot_end <= occupied_start or slot_start >= occupied_end):
                        room_conflict = True
                        break
                
                if room_conflict:
                    continue
                
                # Bu sınıfta kaç öğrenci olacak?
                students_in_this_room = min(classroom.capacity, remaining_students)
                
                # Sınav oluştur
                exam = Exam(
                    course_id=course.id,
                    room_id=classroom.id,
                    slot_start=slot_start,
                    duration=course.exam_duration,
                    slot=slot_start.isoformat(),
                    status='scheduled'
                )
                
                db.session.add(exam)
                db.session.flush()
                
                # Kütüphaneleri güncelle
                room_usage[classroom.id].append((slot_start, slot_end))
                
                if course.teacher_id:
                    if course.teacher_id not in teacher_busy:
                        teacher_busy[course.teacher_id] = []
                    # Hoca sadece bir kez meşgul olmalı (sınav kaç odada olursa olsun)
                    if not any((s <= slot_start and e >= slot_end) for s, e in teacher_busy[course.teacher_id]):
                        teacher_busy[course.teacher_id].append((slot_start, slot_end))
                
                for student_id in student_ids:
                    if student_id not in student_exams:
                        student_exams[student_id] = []
                    # Her öğrenci sadece bir kez meşgul olmalı
                    if not any((s <= slot_start and e >= slot_end) for s, e in student_exams[student_id]):
                        student_exams[student_id].append((slot_start, slot_end))
                
                # Sonuç ekle
                assigned_rooms.append(classroom.name)
                remaining_students -= students_in_this_room
                teacher = db.session.query(Teacher).get(course.teacher_id) if course.teacher_id else None
                
                created_exams.append({
                    'course': course.name,
                    'room': classroom.name,
                    'slot': slot_start.isoformat(),
                    'duration': course.exam_duration,
                    'teacher': teacher.name if teacher else 'Atanmamış',
                    'student_count': students_in_this_room
                })
                
                # Kapasite yettiyse bitir
                if remaining_students <= 0:
                    scheduled = True
                    break
        
        if not scheduled:
            failed_courses.append(course.name)
    
    db.session.commit()
    
    return {
        'created': len(created_exams),
        'failed': len(failed_courses),
        'message': f'{len(created_exams)} ders planlandı, {len(failed_courses)} ders planlama yapılamadı',
        'exams': created_exams,
        'failed_courses': failed_courses if failed_courses else None
    }


def get_schedule_conflicts(db, course_id):
    """
    Bir dersin planlama sırasında oluşabilecek çakışmaları kontrol et.
    
    Returns:
        {
            'has_conflicts': bool,
            'conflicts': [...],  # Çakışma detayları
            'reason': str
        }
    """
    from models import Course, Exam, Enrollment
    
    course = db.session.query(Course).get(course_id)
    if not course:
        return {'has_conflicts': True, 'reason': 'Ders bulunamadı'}
    
    exams = db.session.query(Exam).filter_by(course_id=course_id).all()
    
    if not exams:
        return {'has_conflicts': False, 'conflicts': []}
    
    conflicts = []
    
    for exam in exams:
        # Aynı derslikteki çakışmalar
        overlapping = db.session.query(Exam).filter(
            Exam.room_id == exam.room_id,
            Exam.id != exam.id,
            Exam.slot_start < exam.slot_start + datetime.timedelta(minutes=exam.duration),
            Exam.slot_start + datetime.timedelta(minutes=Exam.duration) > exam.slot_start
        ).all()
        
        for other_exam in overlapping:
            conflicts.append({
                'type': 'room_conflict',
                'message': f'Derslik {exam.room_id} aynı saatte kullanılıyor'
            })
    
    return {
        'has_conflicts': len(conflicts) > 0,
        'conflicts': conflicts
    }
