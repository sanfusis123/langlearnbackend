import asyncio
from app.db.database import connect_to_mongo, close_mongo_connection
from app.models.user import User, Role, Permission
from app.models.language_learning import Language, Lesson, Quiz, UserActivityLog, UserStreak
from app.core.security import get_password_hash


async def init_db():
    await connect_to_mongo()
    
    # Create default permissions
    permissions = [
        {"name": "users.create", "resource": "users", "action": "create", "description": "Create users"},
        {"name": "users.read", "resource": "users", "action": "read", "description": "Read users"},
        {"name": "users.update", "resource": "users", "action": "update", "description": "Update users"},
        {"name": "users.delete", "resource": "users", "action": "delete", "description": "Delete users"},
    ]
    
    created_permissions = []
    for perm_data in permissions:
        perm = await Permission.find_one(Permission.name == perm_data["name"])
        if not perm:
            perm = Permission(**perm_data)
            await perm.insert()
        created_permissions.append(perm)
    
    # Create admin role
    admin_role = await Role.find_one(Role.name == "admin")
    if not admin_role:
        admin_role = Role(
            name="admin",
            description="Administrator role with all permissions",
            permissions=created_permissions
        )
        await admin_role.insert()
    
    # Create default admin user
    admin_user = await User.find_one(User.username == "admin")
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
            roles=[admin_role]
        )
        await admin_user.insert()
        print("Default admin user created - username: admin, password: admin123")
    
    # Create languages
    languages_data = [
        {"code": "en", "name": "English", "native_name": "English"},
        {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
        {"code": "fr", "name": "French", "native_name": "Français"},
        {"code": "ru", "name": "Russian", "native_name": "Русский"},
    ]
    
    created_languages = {}
    for lang_data in languages_data:
        lang = await Language.find_one(Language.code == lang_data["code"])
        if not lang:
            lang = Language(**lang_data)
            await lang.insert()
        created_languages[lang.code] = lang
        print(f"Language '{lang.name}' ready")
    
    # Create sample English lesson
    en_lang = created_languages["en"]
    sample_lesson = await Lesson.find_one(Lesson.title == "Basic Greetings")
    if not sample_lesson:
        sample_lesson = Lesson(
            title="Basic Greetings",
            description="Learn essential greetings and introductions in English",
            language=en_lang,
            level="beginner",
            order=1,
            content={
                "introduction": "In this lesson, we'll learn basic greetings used in everyday English conversations.",
                "sections": [
                    {
                        "title": "Common Greetings",
                        "content": "Hello, Hi, Good morning, Good afternoon, Good evening"
                    },
                    {
                        "title": "Introductions",
                        "content": "My name is..., Nice to meet you, How are you?"
                    }
                ]
            },
            vocabulary=[
                {"word": "Hello", "translation": "नमस्ते", "pronunciation": "heh-LOH"},
                {"word": "Good morning", "translation": "सुप्रभात", "pronunciation": "good MOR-ning"},
                {"word": "Thank you", "translation": "धन्यवाद", "pronunciation": "thank YOO"}
            ],
            grammar_points=[
                "Use 'Good morning' before noon",
                "Use 'Good afternoon' from noon to evening",
                "Use 'Good evening' after 6 PM"
            ],
            exercises=[
                {
                    "type": "fill-in-the-blank",
                    "question": "___ morning! How are you?",
                    "answer": "Good"
                }
            ],
            estimated_time_minutes=15
        )
        await sample_lesson.insert()
        print("Sample lesson created")
        
        # Create sample quiz
        sample_quiz = Quiz(
            lesson=sample_lesson,
            title="Basic Greetings Quiz",
            questions=[
                {
                    "question": "What greeting do you use before noon?",
                    "options": ["Good evening", "Good morning", "Good night", "Good afternoon"],
                    "correct_answer": "Good morning",
                    "type": "multiple-choice"
                },
                {
                    "question": "Complete: 'Nice to ___ you'",
                    "options": ["meet", "see", "greet", "know"],
                    "correct_answer": "meet",
                    "type": "multiple-choice"
                }
            ],
            passing_score=70,
            time_limit_minutes=10
        )
        await sample_quiz.insert()
        print("Sample quiz created")
    
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(init_db())