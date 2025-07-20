import asyncio
from app.db.database import connect_to_mongo, close_mongo_connection
from app.models.language_learning import Language, Lesson, Quiz
import random
from datetime import datetime, timezone


async def create_english_lessons():
    """Create comprehensive English lessons"""
    language = await Language.find_one(Language.code == "en")
    if not language:
        print("English language not found!")
        return
    
    lessons_data = [
        {
            "title": "Basic Greetings",
            "description": "Learn essential greetings and introductions in English",
            "level": "beginner",
            "order": 1,
            "content": {
                "introduction": "In this lesson, we'll learn basic greetings used in everyday English conversations.",
                "sections": [
                    {
                        "title": "Common Greetings",
                        "content": "Learn how to greet people at different times of the day: Hello, Hi, Good morning, Good afternoon, Good evening"
                    },
                    {
                        "title": "Introductions",
                        "content": "Master the art of introducing yourself: My name is..., Nice to meet you, How are you?, I'm fine, thank you"
                    }
                ]
            },
            "vocabulary": [
                {"word": "Hello", "translation": "नमस्ते", "pronunciation": "heh-LOH"},
                {"word": "Good morning", "translation": "सुप्रभात", "pronunciation": "good MOR-ning"},
                {"word": "Thank you", "translation": "धन्यवाद", "pronunciation": "thank YOO"},
                {"word": "Goodbye", "translation": "अलविदा", "pronunciation": "good-BYE"},
                {"word": "Please", "translation": "कृपया", "pronunciation": "PLEEZ"}
            ],
            "grammar_points": [
                "Use 'Good morning' before noon",
                "Use 'Good afternoon' from noon to evening",
                "Use 'Good evening' after 6 PM",
                "'How are you?' is a common greeting, not a real question"
            ],
            "estimated_time_minutes": 15
        },
        {
            "title": "Numbers and Counting",
            "description": "Learn numbers from 1-100 and basic counting",
            "level": "beginner",
            "order": 2,
            "content": {
                "introduction": "Numbers are essential for daily communication. Let's learn to count in English!",
                "sections": [
                    {
                        "title": "Numbers 1-20",
                        "content": "Master the basic numbers: one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve, thirteen, fourteen, fifteen, sixteen, seventeen, eighteen, nineteen, twenty"
                    },
                    {
                        "title": "Tens and Hundreds",
                        "content": "Learn to count by tens: twenty, thirty, forty, fifty, sixty, seventy, eighty, ninety, one hundred"
                    }
                ]
            },
            "vocabulary": [
                {"word": "One", "translation": "एक", "pronunciation": "WUN"},
                {"word": "Ten", "translation": "दस", "pronunciation": "TEN"},
                {"word": "Twenty", "translation": "बीस", "pronunciation": "TWEN-tee"},
                {"word": "Hundred", "translation": "सौ", "pronunciation": "HUN-dred"},
                {"word": "Thousand", "translation": "हज़ार", "pronunciation": "THOU-zand"}
            ],
            "grammar_points": [
                "Numbers 13-19 end with 'teen'",
                "Multiples of 10 end with 'ty'",
                "Use 'and' between hundreds and tens (e.g., 'one hundred and twenty')"
            ],
            "estimated_time_minutes": 20
        },
        {
            "title": "Days and Months",
            "description": "Learn days of the week and months of the year",
            "level": "beginner",
            "order": 3,
            "content": {
                "introduction": "Understanding days and months is crucial for scheduling and planning.",
                "sections": [
                    {
                        "title": "Days of the Week",
                        "content": "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"
                    },
                    {
                        "title": "Months of the Year",
                        "content": "January, February, March, April, May, June, July, August, September, October, November, December"
                    }
                ]
            },
            "vocabulary": [
                {"word": "Monday", "translation": "सोमवार", "pronunciation": "MUN-day"},
                {"word": "Friday", "translation": "शुक्रवार", "pronunciation": "FRY-day"},
                {"word": "January", "translation": "जनवरी", "pronunciation": "JAN-yoo-ary"},
                {"word": "Today", "translation": "आज", "pronunciation": "too-DAY"},
                {"word": "Tomorrow", "translation": "कल", "pronunciation": "too-MOR-oh"}
            ],
            "grammar_points": [
                "Days of the week are always capitalized",
                "Months are always capitalized",
                "Use 'on' with days (on Monday)",
                "Use 'in' with months (in January)"
            ],
            "estimated_time_minutes": 25
        }
    ]
    
    for lesson_data in lessons_data:
        # Check if lesson already exists
        existing = await Lesson.find_one(
            Lesson.title == lesson_data["title"],
            Lesson.language.id == language.id
        )
        if not existing:
            lesson = Lesson(language=language, **lesson_data)
            await lesson.insert()
            print(f"Created lesson: {lesson.title}")
            
            # Create quiz for each lesson
            quiz_questions = generate_quiz_questions(lesson_data)
            quiz = Quiz(
                lesson=lesson,
                title=f"{lesson.title} Quiz",
                questions=quiz_questions,
                passing_score=70,
                time_limit_minutes=10
            )
            await quiz.insert()
            print(f"Created quiz for: {lesson.title}")


async def create_hindi_lessons():
    """Create Hindi lessons"""
    language = await Language.find_one(Language.code == "hi")
    if not language:
        print("Hindi language not found!")
        return
    
    lessons_data = [
        {
            "title": "हिंदी वर्णमाला (Hindi Alphabet)",
            "description": "Learn the Hindi alphabet - Devanagari script",
            "level": "beginner",
            "order": 1,
            "content": {
                "introduction": "Hindi uses the Devanagari script. Let's learn the basic vowels and consonants.",
                "sections": [
                    {
                        "title": "स्वर (Vowels)",
                        "content": "अ आ इ ई उ ऊ ए ऐ ओ औ अं अः"
                    },
                    {
                        "title": "व्यंजन (Consonants)",
                        "content": "क ख ग घ ङ, च छ ज झ ञ, ट ठ ड ढ ण"
                    }
                ]
            },
            "vocabulary": [
                {"word": "अ", "translation": "a", "pronunciation": "uh"},
                {"word": "आ", "translation": "aa", "pronunciation": "aah"},
                {"word": "क", "translation": "ka", "pronunciation": "kuh"},
                {"word": "ख", "translation": "kha", "pronunciation": "khuh"},
                {"word": "ग", "translation": "ga", "pronunciation": "guh"}
            ],
            "grammar_points": [
                "Hindi has 11 vowels and 33 consonants",
                "Each consonant has an inherent 'a' sound",
                "Vowels can be written as independent letters or as diacritical marks"
            ],
            "estimated_time_minutes": 30
        },
        {
            "title": "बुनियादी अभिवादन (Basic Greetings)",
            "description": "Learn common Hindi greetings and phrases",
            "level": "beginner",
            "order": 2,
            "content": {
                "introduction": "Let's learn how to greet people in Hindi!",
                "sections": [
                    {
                        "title": "Common Greetings",
                        "content": "नमस्ते (Hello), आप कैसे हैं? (How are you?), मैं ठीक हूं (I am fine)"
                    },
                    {
                        "title": "Polite Phrases",
                        "content": "धन्यवाद (Thank you), कृपया (Please), माफ़ कीजिये (Excuse me)"
                    }
                ]
            },
            "vocabulary": [
                {"word": "नमस्ते", "translation": "Hello", "pronunciation": "nuh-muh-stay"},
                {"word": "धन्यवाद", "translation": "Thank you", "pronunciation": "dhun-yuh-vaad"},
                {"word": "अलविदा", "translation": "Goodbye", "pronunciation": "ul-vee-daa"},
                {"word": "हाँ", "translation": "Yes", "pronunciation": "haan"},
                {"word": "नहीं", "translation": "No", "pronunciation": "nuh-heen"}
            ],
            "grammar_points": [
                "नमस्ते can be used for both hello and goodbye",
                "आप is the formal 'you', तुम is informal",
                "Add जी after names to show respect"
            ],
            "estimated_time_minutes": 20
        }
    ]
    
    for lesson_data in lessons_data:
        existing = await Lesson.find_one(
            Lesson.title == lesson_data["title"],
            Lesson.language.id == language.id
        )
        if not existing:
            lesson = Lesson(language=language, **lesson_data)
            await lesson.insert()
            print(f"Created lesson: {lesson.title}")
            
            quiz_questions = generate_quiz_questions(lesson_data)
            quiz = Quiz(
                lesson=lesson,
                title=f"{lesson.title} Quiz",
                questions=quiz_questions,
                passing_score=70,
                time_limit_minutes=10
            )
            await quiz.insert()
            print(f"Created quiz for: {lesson.title}")


async def create_french_lessons():
    """Create French lessons"""
    language = await Language.find_one(Language.code == "fr")
    if not language:
        print("French language not found!")
        return
    
    lessons_data = [
        {
            "title": "Salutations de base",
            "description": "Learn basic French greetings",
            "level": "beginner",
            "order": 1,
            "content": {
                "introduction": "French greetings are essential for polite conversation.",
                "sections": [
                    {
                        "title": "Greetings",
                        "content": "Bonjour (Hello/Good day), Bonsoir (Good evening), Salut (Hi - informal)"
                    },
                    {
                        "title": "Polite phrases",
                        "content": "S'il vous plaît (Please), Merci (Thank you), De rien (You're welcome)"
                    }
                ]
            },
            "vocabulary": [
                {"word": "Bonjour", "translation": "Hello", "pronunciation": "bon-ZHOOR"},
                {"word": "Merci", "translation": "Thank you", "pronunciation": "mer-SEE"},
                {"word": "Au revoir", "translation": "Goodbye", "pronunciation": "oh ruh-VWAR"},
                {"word": "Oui", "translation": "Yes", "pronunciation": "wee"},
                {"word": "Non", "translation": "No", "pronunciation": "nohn"}
            ],
            "grammar_points": [
                "Use 'Bonjour' until evening, then switch to 'Bonsoir'",
                "Tu vs Vous: Tu is informal, Vous is formal/plural",
                "Always use 's'il vous plaît' when making requests"
            ],
            "estimated_time_minutes": 20
        },
        {
            "title": "Les nombres",
            "description": "Learn French numbers 1-20",
            "level": "beginner",
            "order": 2,
            "content": {
                "introduction": "Numbers are fundamental for shopping, telling time, and more.",
                "sections": [
                    {
                        "title": "Numbers 1-10",
                        "content": "un, deux, trois, quatre, cinq, six, sept, huit, neuf, dix"
                    },
                    {
                        "title": "Numbers 11-20",
                        "content": "onze, douze, treize, quatorze, quinze, seize, dix-sept, dix-huit, dix-neuf, vingt"
                    }
                ]
            },
            "vocabulary": [
                {"word": "Un", "translation": "One", "pronunciation": "uhn"},
                {"word": "Deux", "translation": "Two", "pronunciation": "duh"},
                {"word": "Trois", "translation": "Three", "pronunciation": "twah"},
                {"word": "Dix", "translation": "Ten", "pronunciation": "dees"},
                {"word": "Vingt", "translation": "Twenty", "pronunciation": "van"}
            ],
            "grammar_points": [
                "Numbers 1-16 have unique names",
                "17-19 are formed with 'dix' + number",
                "French uses spaces in large numbers where English uses commas"
            ],
            "estimated_time_minutes": 25
        }
    ]
    
    for lesson_data in lessons_data:
        existing = await Lesson.find_one(
            Lesson.title == lesson_data["title"],
            Lesson.language.id == language.id
        )
        if not existing:
            lesson = Lesson(language=language, **lesson_data)
            await lesson.insert()
            print(f"Created lesson: {lesson.title}")
            
            quiz_questions = generate_quiz_questions(lesson_data)
            quiz = Quiz(
                lesson=lesson,
                title=f"{lesson.title} Quiz",
                questions=quiz_questions,
                passing_score=70,
                time_limit_minutes=10
            )
            await quiz.insert()
            print(f"Created quiz for: {lesson.title}")


async def create_russian_lessons():
    """Create Russian lessons"""
    language = await Language.find_one(Language.code == "ru")
    if not language:
        print("Russian language not found!")
        return
    
    lessons_data = [
        {
            "title": "Русский алфавит",
            "description": "Learn the Russian Cyrillic alphabet",
            "level": "beginner",
            "order": 1,
            "content": {
                "introduction": "Russian uses the Cyrillic alphabet with 33 letters.",
                "sections": [
                    {
                        "title": "Vowels",
                        "content": "А, Е, Ё, И, О, У, Ы, Э, Ю, Я"
                    },
                    {
                        "title": "Consonants",
                        "content": "Б, В, Г, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ"
                    }
                ]
            },
            "vocabulary": [
                {"word": "А", "translation": "A", "pronunciation": "ah"},
                {"word": "Б", "translation": "B", "pronunciation": "beh"},
                {"word": "В", "translation": "V", "pronunciation": "veh"},
                {"word": "Г", "translation": "G", "pronunciation": "geh"},
                {"word": "Д", "translation": "D", "pronunciation": "deh"}
            ],
            "grammar_points": [
                "Russian has 10 vowels and 21 consonants",
                "Ъ (hard sign) and Ь (soft sign) modify pronunciation",
                "Some letters look like Latin but sound different"
            ],
            "estimated_time_minutes": 30
        },
        {
            "title": "Основные приветствия",
            "description": "Basic Russian greetings",
            "level": "beginner",
            "order": 2,
            "content": {
                "introduction": "Learn essential Russian greetings for daily use.",
                "sections": [
                    {
                        "title": "Greetings",
                        "content": "Здравствуйте (Hello formal), Привет (Hi informal), Доброе утро (Good morning)"
                    },
                    {
                        "title": "Polite phrases",
                        "content": "Спасибо (Thank you), Пожалуйста (Please/You're welcome), Извините (Excuse me)"
                    }
                ]
            },
            "vocabulary": [
                {"word": "Здравствуйте", "translation": "Hello", "pronunciation": "ZDRAHST-vuy-tyeh"},
                {"word": "Спасибо", "translation": "Thank you", "pronunciation": "spah-SEE-bah"},
                {"word": "До свидания", "translation": "Goodbye", "pronunciation": "dah svee-DAH-nee-yah"},
                {"word": "Да", "translation": "Yes", "pronunciation": "dah"},
                {"word": "Нет", "translation": "No", "pronunciation": "nyet"}
            ],
            "grammar_points": [
                "Use Вы (formal you) with strangers and elders",
                "Use ты (informal you) with friends and children",
                "Russians often skip 'please' in casual requests"
            ],
            "estimated_time_minutes": 20
        }
    ]
    
    for lesson_data in lessons_data:
        existing = await Lesson.find_one(
            Lesson.title == lesson_data["title"],
            Lesson.language.id == language.id
        )
        if not existing:
            lesson = Lesson(language=language, **lesson_data)
            await lesson.insert()
            print(f"Created lesson: {lesson.title}")
            
            quiz_questions = generate_quiz_questions(lesson_data)
            quiz = Quiz(
                lesson=lesson,
                title=f"{lesson.title} Quiz",
                questions=quiz_questions,
                passing_score=70,
                time_limit_minutes=10
            )
            await quiz.insert()
            print(f"Created quiz for: {lesson.title}")


def generate_quiz_questions(lesson_data):
    """Generate quiz questions based on lesson content"""
    questions = []
    
    # Vocabulary questions
    if lesson_data.get("vocabulary"):
        for vocab in lesson_data["vocabulary"][:3]:  # Take first 3 vocabulary items
            questions.append({
                "question": f"What does '{vocab['word']}' mean?",
                "options": [
                    vocab['translation'],
                    "Water",
                    "Food",
                    "House"
                ],
                "correct_answer": vocab['translation'],
                "type": "multiple-choice"
            })
    
    # Grammar questions
    if lesson_data.get("grammar_points"):
        for point in lesson_data["grammar_points"][:2]:  # Take first 2 grammar points
            # Create a simple true/false question
            questions.append({
                "question": f"True or False: {point}",
                "options": ["True", "False"],
                "correct_answer": "True",
                "type": "multiple-choice"
            })
    
    return questions[:5]  # Limit to 5 questions per quiz


async def seed_all_lessons():
    """Seed lessons for all languages"""
    await connect_to_mongo()
    
    print("Starting lesson seeding...")
    
    await create_english_lessons()
    await create_hindi_lessons()
    await create_french_lessons()
    await create_russian_lessons()
    
    print("Lesson seeding completed!")
    
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed_all_lessons())