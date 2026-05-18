from app import app
from app.database.models import get_db, get_next_id
from werkzeug.security import generate_password_hash
from app.services.crypto_service import generate_exam_key, encrypt_exam_key, load_master_key
from datetime import datetime, timezone

with app.app_context():

    db = get_db()
    master_key = load_master_key()

    # Drop all existing collections for a clean slate
    for col in ("users", "candidates", "exams", "questions",
                "exam_sessions", "answers", "evaluations",
                "examiner_assignments", "exam_assignments",
                "departments", "subjects", "academic_years", "semesters", "exam_types",
                "counters"):
        db[col].drop()

    # Re-create unique indexes
    db.users.create_index("username", unique=True)
    db.users.create_index("email", unique=True)
    db.candidates.create_index("registration_no", unique=True)
    db.departments.create_index("name", unique=True)
    db.subjects.create_index("name", unique=True)
    db.academic_years.create_index("name", unique=True)
    db.semesters.create_index("name", unique=True)
    db.exam_types.create_index("name", unique=True)
    # ----
    # -----------------------------

    # -----------------------------
    # INVIGILATOR USER
    # -----------------------------
    inv_id = get_next_id("users")
    db.users.insert_one({
        "_id": inv_id,
        "full_name": "Demo Invigilator",
        "username": "invigilator",
        "email": "invigilator@test.com",
        "password_hash": generate_password_hash("invigilator123"),
        "role": "INVIGILATOR",
        "is_active": True,        "email_verified": True,        "phone_no": None,
        "created_at": datetime.now(timezone.utc),
        "session_token": None,
    })

    # -----------------------------
    # CANDIDATE USER
    # -----------------------------
    cand_user_id = get_next_id("users")
    db.users.insert_one({
        "_id": cand_user_id,
        "full_name": "Demo Candidate",
        "username": "student",
        "email": "student@test.com",
        "password_hash": generate_password_hash("student123"),
        "role": "CANDIDATE",
        "is_active": True,        "email_verified": True,        "phone_no": "9999999999",
        "created_at": datetime.now(timezone.utc),
        "session_token": None,
    })

    # -----------------------------
    # EXAMINER USER
    # -----------------------------
    examiner_id = get_next_id("users")
    db.users.insert_one({
        "_id": examiner_id,
        "full_name": "Demo Examiner",
        "username": "examiner",
        "email": "examiner@test.com",
        "password_hash": generate_password_hash("examiner123"),
        "role": "EXAMINER",
        "is_active": True,        "email_verified": True,        "phone_no": None,
        "created_at": datetime.now(timezone.utc),
        "session_token": None,
    })

    # -----------------------------
    # ADMIN USER
    # -----------------------------
    admin_id = get_next_id("users")
    db.users.insert_one({
        "_id": admin_id,
        "full_name": "Demo Admin",
        "username": "admin",
        "email": "admin@test.com",
        "password_hash": generate_password_hash("admin123"),
        "role": "ADMIN",
        "is_active": True,        "email_verified": True,        "phone_no": None,
        "created_at": datetime.now(timezone.utc),
        "session_token": None,
    })

    # -----------------------------
    # CANDIDATE PROFILE ENTRY
    # -----------------------------
    cand_id = get_next_id("candidates")
    db.candidates.insert_one({
        "_id": cand_id,
        "reg_id": cand_user_id,
        "registration_no": "CAND-001",
        "department_id": dept_id,
        "semester_id": sem_id,
        "academic_year_id": year_id,
    })

    # -----------------------------
    # SAMPLE PHYSICS EXAM (with encrypted key)
    # -----------------------------
    exam_key = generate_exam_key()
    enc_ct, enc_iv, enc_tag = encrypt_exam_key(exam_key, master_key)

    exam_id = get_next_id("exams")
    db.exams.insert_one({
        "_id": exam_id,
        "exam_name": "Physics \u2013 Demo Subjective Exam",
        "duration": 60,
        "total_marks": 100,
        "department_id": dept_id,
        "subject_id": subject_id,
        "semester_id": sem_id,
        "academic_year_id": year_id,
        "exam_type_id": exam_type_id,
        "is_active": True,
        "created_by": inv_id,
        "enc_key_ciphertext": enc_ct,
        "enc_key_iv": enc_iv,
        "enc_key_tag": enc_tag,
    })

    # -----------------------------
    # EXAMINER ASSIGNMENT (link examiner -> student + exam)
    # -----------------------------
    assign_id = get_next_id("examiner_assignments")
    db.examiner_assignments.insert_one({
        "_id": assign_id,
        "examiner_id": examiner_id,
        "candidate_id": cand_id,
        "exam_id": exam_id,
    })

    # -----------------------------
    # EXAM ASSIGNMENT (assign student to exam)
    # -----------------------------
    exam_assign_id = get_next_id("exam_assignments")
    db.exam_assignments.insert_one({
        "_id": exam_assign_id,
        "candidate_id": cand_id,
        "exam_id": exam_id,
    })

    # -----------------------------
    # SAMPLE PHYSICS SUBJECTIVE QUESTIONS (10-question demo exam)
    # -----------------------------
    question_bank = [
        (
            "State Newton's three laws of motion and illustrate each law with a suitable example.",
            "The first law states inertia: bodies keep their state unless acted on by an external force. The second law is F = m*a, meaning acceleration is proportional to force and inversely proportional to mass. The third law states every action has an equal and opposite reaction.",
        ),
        (
            "Explain the principle of conservation of energy with reference to the motion of a simple pendulum.",
            "Total mechanical energy remains constant if friction is ignored. At extreme positions, potential energy is maximum and kinetic is minimum; at the mean position kinetic energy is maximum and potential is minimum.",
        ),
        (
            "What is refraction of light? Describe an everyday situation where refraction plays an important role and explain it scientifically.",
            "Refraction is bending of light when it passes between media with different refractive index due to speed change. Example: a straw in water appears bent because rays from water bend away from the normal when entering air.",
        ),
        (
            "Define electric current, potential difference, and resistance. Explain the relationship between them using Ohm's law.",
            "Current is charge flow per second (ampere), potential difference is work done per unit charge (volt), and resistance opposes current (ohm). Ohm's law: V = I*R.",
        ),
        (
            "Describe the difference between longitudinal and transverse waves, and give one real-world example of each type.",
            "Longitudinal waves have particle vibration parallel to wave travel, e.g., sound in air. Transverse waves have particle vibration perpendicular to propagation, e.g., light waves.",
        ),
        (
            "What is the difference between speed and velocity? Give an example where they differ.",
            "Speed is scalar distance per time, while velocity is vector displacement per time with direction. In circular motion at constant speed, velocity continuously changes direction.",
        ),
        (
            "Explain why the sky appears blue and the sun appears reddish at sunrise and sunset.",
            "Rayleigh scattering causes shorter wavelengths like blue to scatter more, making the sky blue. At sunrise and sunset light travels a longer path, so blue scatters away and red/orange dominate.",
        ),
        (
            "What is the law of conservation of momentum? Apply it to explain the recoil of a gun.",
            "In an isolated system total momentum remains constant. Before firing momentum is zero; after firing bullet momentum forward is balanced by equal backward gun momentum, causing recoil.",
        ),
        (
            "Define work, energy, and power. State their SI units and the relationship between them.",
            "Work is force multiplied by displacement in force direction (joule). Energy is capacity to do work (joule). Power is rate of doing work (watt), P = Work/time.",
        ),
        (
            "What is electromagnetic induction? Describe one practical application based on it.",
            "Electromagnetic induction is generation of emf when magnetic flux linked with a conductor changes. A practical application is an electric generator where rotating coils in a magnetic field induce current.",
        ),
    ]

    for text, model_answer in question_bank:
        q_id = get_next_id("questions")
        db.questions.insert_one({
            "_id": q_id,
            "exam_id": exam_id,
            "question_text": text,
            "model_answer": model_answer,
        })

    print("MongoDB seeded successfully!")
    print("Use these credentials to login:")
    print("Candidate   -> student / student123")
    print("Invigilator -> invigilator / invigilator123")
    print("Examiner    -> examiner / examiner123")
    print("Admin       -> admin / admin123")
    dept_id = get_next_id("departments")
    db.departments.insert_one({"_id": dept_id, "name": "Physics Department", "code": "PHY", "is_active": True})

    year_id = get_next_id("academic_years")
    db.academic_years.insert_one({"_id": year_id, "name": "2025-2026", "is_active": True})

    sem_id = get_next_id("semesters")
    db.semesters.insert_one({"_id": sem_id, "name": "Semester 1", "number": 1, "is_active": True})

    exam_type_id = get_next_id("exam_types")
    db.exam_types.insert_one({"_id": exam_type_id, "name": "EndSem", "weightage": 100, "is_active": True})

    subject_id = get_next_id("subjects")
    db.subjects.insert_one({
        "_id": subject_id,
        "name": "Physics",
        "code": "PHY101",
        "department_id": dept_id,
        "semester_id": sem_id,
        "credits": 4,
        "is_active": True,
    })
