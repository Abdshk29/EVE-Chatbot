import nltk
nltk.download('punkt_tab')
import pandas as pd
from fuzzywuzzy import process
from autocorrect import Speller
from flask import Flask, request, jsonify, render_template
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
import re

# Initialize the Flask app
app = Flask(__name__)

# Initialize the spell checker, stemmer, and lemmatizer
spell = Speller()
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Load course data
try:
    courses_df = pd.read_csv('D:\BS-AI 5th Semester\Programming for AI\Project\Prog for AI Project 22-NTU-CS-1358 Group 7\Prog for AI project 22-NTU-CS-1358 Group 7\data.csv')
    print("CSV loaded successfully.")
except Exception as e:
    print(f"Error loading CSV: {e}")

courses = {}

for _, row in courses_df.iterrows():
    if pd.notna(row['Course title']):
        main_name = row['Course title']
        aliases = row['Aliases'].split(',') if pd.notna(row['Aliases']) else []
        courses[main_name.lower()] = {
            "aliases": [alias.strip().lower() for alias in aliases],
            "Name": row['Course title'],
            "category": row['category'],
            "duration": row['duration'],
            "discount": row['discount'],
            "course_level": row['course level']
        }

# Check if courses are loaded correctly
print(f"Courses loaded: {len(courses)}")

# Extract categories from the course data
categories = list(set(course['category'] for course in courses.values()))
print(f"Categories extracted: {categories}")

# Function to normalize input and handle spelling mistakes
def normalize_text(user_input):
    corrected_text = spell(user_input)  # Correct spelling using autocorrect library
    return corrected_text.lower()

# Function to tokenize text using NLTK
def tokenize_text(text):
    tokens = nltk.word_tokenize(text)
    return tokens

# Function to clean the user message (remove punctuation, stopwords, and apply stemming/lemmatization)
def clean_message(message, use_stemming=True, use_lemmatization=False):
    message = re.sub(r'[^\w\s]', '', message)

    # Tokenize the message
    tokens = word_tokenize(message.lower())  # Tokenize and convert to lowercase

    # Load stopwords and remove them from the tokens
    stop_words = set(stopwords.words('english'))
    cleaned_message = [word for word in tokens if word not in stop_words]

    # Apply stemming or lemmatization
    if use_stemming:
        cleaned_message = [stemmer.stem(word) for word in cleaned_message]  # Apply stemming
    elif use_lemmatization:
        cleaned_message = [lemmatizer.lemmatize(word) for word in cleaned_message]  # Apply lemmatization

    return ' '.join(cleaned_message)

# Fuzzy matching for course categories
def get_courses_by_category(category_name):
    category_name = normalize_text(category_name)  # Normalize input for matching
    matched_courses = [
        details for course, details in courses.items()
        if normalize_text(details['category']) == category_name
    ]
    return matched_courses

# Fuzzy matching for course names or aliases
def get_course_info(course_name):
    normalized_query = normalize_text(course_name)
    print(f"Normalized Query: '{normalized_query}'")

    # Check for exact match with course names (lowercase)
    if normalized_query in courses:
        return courses[normalized_query]

    # Use fuzzy matching for course names and aliases
    all_course_names = list(courses.keys())
    all_aliases = [alias for details in courses.values() for alias in details['aliases']]
    all_options = all_course_names + all_aliases

    # Perform fuzzy matching with a threshold score
    best_match = process.extractOne(normalized_query, all_options)
    if best_match and best_match[1] > 70:  # Match found with sufficient score
        match_text = best_match[0]

        # Check if the best match corresponds to a course or alias
        for course, details in courses.items():
            if match_text == course or match_text in details["aliases"]:
                return details

    return None

KEYWORDS = {
    "Aoa" : "Walaikum Salam!",
    "Assalam Alaikum" : "Walaikum Salam! How Can I Help You?",
    "What is your name" : "My name is Eve.An AI assistant here to help you , in choosing the best courses that aligns with your interset.",
    "What is your purpose" : "My purpose is to assist you in finding the best courses and answering your queries",
    "Who designed you" : "Very Special Personalities of BS AI 5th",
    "Why were you developed" : "To present me as an AI model to Mr. Abdul Basit.",
    "fees": "Our course fees vary depending on the program. Please contact us at 03218886640 for fee details.",
    "cost": "Course prices depend on the program you choose. For fee details, visit Edify or contact us at 03218886640.",
    "schedule": "Our classes are scheduled in both morning and evening slots to accommodate different preferences. You can decide your own timings for most of our courses.",
    "location": "We are located on the 4th Floor, College of IT Building, Susan Road, Faisalabad.",
    "contact": "You can reach us at: Phone: 03218886640 or visit us at our campus.",
    "apply": "To apply for a course, visit our website or contact us at 03218886640.",
    "freelancing":"Edify offers specialized freelancing classes to help you kickstart your career.<br> <br>If you enroll in any of our courses, the freelancing classes are absolutely free.<br> Alternatively, you can join our paid freelancing class, which doesn’t require enrollment in any other course.<br> <br>Learn how to successfully promote your skills and start earning on platforms like Fiverr and Upwork and LinkedIn!",
    "fiverr": "Fiverr is a popular platform where freelancers can offer services starting at $5. If you're interested in learning how to set up a successful Fiverr profile, we offer courses that teach freelancing strategies, branding, and pricing your services. <br>",
    "upwork": "Upwork is another great freelancing platform for professionals in fields like programming, design, and writing. Our courses can help you with the skills you need to land your first job on Upwork, as well as tips on how to make your profile stand out.",
    "discount": "We offer discounts on some of our courses from time to time. Enjoy a 10% discount on every course, valid for the next 3 days only—hurry, don't miss out!",
    "internship": "Edify offers both paid and unpaid internships based on your skill level. If you are interested, do contact us at 03218886640.",
    "job": "If you're looking for job opportunities, we provide career assistance services, including job placement support and guidance. Send your resume and contact us at 03218886640.",
    "earning ": "We offer a range of courses that can help you develop skills to start earning, such as freelancing, digital marketing, web development, and more.<br> These courses are designed to help you build a portfolio and find clients or employers.",
    "course": "We offer a variety of courses in fields such as: <br>-Artificial Intelligence<br>-E-commerce<br>-Art and Design<br>-Digital Marketing.<br> Each course is designed to equip you with practical skills and knowledge, and includes modules on Spoken English and Freelancing to help you build a successful career.<br>These courses are designed to help you build a portfolio and find clients or employers.",
    "program": "We offer a variety of programs in fields such as: <br>-Artificial Intelligence<br>-E-commerce<br>-Art and Design<br>-Digital Marketing.<br> Each course is designed to equip you with practical skills and knowledge, and includes modules on Spoken English and Freelancing to help you build a successful career.<br>These courses are designed to help you build a portfolio and find clients or employers.",
    "hi": "Hello! How can I assist you today? If you're looking for course information, type the course name or category you're interested in.",
    "hello": "Hello! How can I assist you today? If you're looking for course information, type the course name or category you're interested in.",
    "hey": "Hey there! Need help with course details or anything else? Feel free to ask.",
    "thankyou": "You're welcome! Let me know if you have any other questions or need further assistance.",
    "thank you": "You're welcome! Let me know if you have any other questions or need further assistance.",
    "goodbye": "Goodbye! Feel free to come back if you have more questions later.",
    "help": "I’m here to help! You can ask me about course details, fees, schedules, internships, and more. Just let me know what you need.",
    "welcome": "Welcome! How can I assist you today?",
    "ok": "Okay.",
    "Great":"I'm Glad you liked it.",
    "good" : "Thankyou.If there is anything I can help you with?",
    "No": "I'm sorry, If I didn't understand you well. Can you tell me specifically what are you asking?",
    "interested": "Oh That's great! Contact us at 03218886640 and confirm your seat without wasting any time.",
    "what courses do you offer": "We offer a variety of courses in fields such as: <br>-Artificial Intelligence<br>-E-commerce<br>-Art and Design<br>-Digital Marketing<br>-Freelancing Programs<br>-Development Programs.<br> Each course is designed to equip you with practical skills and knowledge, and includes modules on Spoken English and Freelancing to help you build a successful career.",
    "class timings": "Our classes are offered in both morning and evening slots to accommodate different schedules. You can also select your own preferences.",
    "exam": "Exams are conducted at the end of each course to assess your knowledge. You’ll be informed in advance about the exam schedule and format.",
    "project": "Projects are conducted at the end of each course to assess your knowledge. You’ll be informed in advance about the Project details and format.",
    "certificate": "Upon successful completion of your course, you will receive a certificate that you can showcase to potential employers.",
    "duration": "Course durations vary depending on the program. Typically, courses range from 4 weeks to 6 months. Let me know which course you're interested in, and I'll provide the exact duration.",
    "time limit": "Course durations vary depending on the program. Typically, courses range from 4 weeks to 6 months. Let me know which course you're interested in, and I'll provide the exact duration.",
    "student support": "We provide dedicated student support throughout your learning journey, including help with assignments, projects, and career advice. Reach out anytime for assistance.",
    "workshops": "We regularly hold workshops on various topics to help students gain additional skills. Keep an eye on our website for upcoming workshop announcements.",
    "student community": "By joining our courses, you’ll become part of a vibrant student community where you can network, collaborate, and learn from each other.",
    "scholarships": "We offer scholarships for eligible students. Let me know if you're interested, and I can share the application process and requirements.",
    "refund policy": "We offer a refund policy under certain conditions. Please refer to our website for the detailed refund policy or contact our support team for assistance.",
    "payment methods": "We accept various payment methods , including credit cards, bank transfers, and online payment platforms. Let me know if you need assistance with payment.",
    "financial aid": "We offer financial aid to qualified students. Please provide some details about your situation, and I’ll share the eligibility criteria and application process.",
    "reviews": "Many of our students have shared positive feedback about their experiences. You can check out reviews on our website or read testimonials from students who have completed similar courses.",
    "admission": "Our admissions are always open, but right now we are offering a 10% discount on all of our courses. The discount will end in 3 days. Hurry up! Book your seat.",
    "Micro-Degree": "Edify offers a comprehensive 1-year Micro-Degree program designed to equip you with in-demand skills and earning potential, combining cutting-edge education with practical freelancing expertise to help you excel in today's competitive market.",
    "micro degree": "Edify offers a comprehensive 1-year Micro-Degree program designed to equip you with in-demand skills and earning potential, combining cutting-edge education with practical freelancing expertise to help you excel in today's competitive market.",
    "Software Engineering With AI": "Edify's Software Engineering Micro-Degree is a comprehensive 1-year program designed to equip you with the skills needed to thrive in the tech industry. The program covers:<br>-Full-Stack Web Development<br> -Mobile app development using Kotlin and Java<br> -WordPress development<br> Alongside core software engineering subjects like OOP, DBMS, SDLC, and algorithms. <br><br>Additionally, the program includes Spoken English to enhance communication skills and a Freelancing module to help you monetize your expertise on platforms like Fiverr and Upwork, making it a perfect blend of technical education and career readiness.",
    "SE micro degree": "Edify's Software Engineering Micro-Degree is a comprehensive 1-year program designed to equip you with the skills needed to thrive in the tech industry. The program covers:<br>-Full-Stack Web Development<br> -Mobile app development using Kotlin and Java<br> -WordPress development<br> Alongside core software engineering subjects like OOP, DBMS, SDLC, and algorithms. <br><br>Additionally, the program includes Spoken English to enhance communication skills and a Freelancing module to help you monetize your expertise on platforms like Fiverr and Upwork, making it a perfect blend of technical education and career readiness.",
    "SE degree": "Edify's Software Engineering Micro-Degree is a comprehensive 1-year program designed to equip you with the skills needed to thrive in the tech industry. The program covers:<br>-Full-Stack Web Development<br> -Mobile app development using Kotlin and Java<br> -WordPress development<br> Alongside core software engineering subjects like OOP, DBMS, SDLC, and algorithms. <br><br>Additionally, the program includes Spoken English to enhance communication skills and a Freelancing module to help you monetize your expertise on platforms like Fiverr and Upwork, making it a perfect blend of technical education and career readiness.",
    "Ecommerce With AI": "Edify's E-commerce Micro-Degree is a comprehensive 1-year program designed to empower you with the skills to excel in the rapidly growing world of online business.<br><br> This program includes in-depth training on: <br>-TikTok Shop management<br> -Shopify store setup and optimization<br>-Amazon Full Stack expertise<br><br> Additionally, it offers a robust foundation in Digital Marketing, enabling you to drive traffic and boost sales. <br>The program also includes Spoken English to enhance your communication skills and a Freelancing module to help you monetize your expertise on platforms like Fiverr and Upwork.",
    "ecommerce micro degree": "Edify's E-commerce Micro-Degree is a comprehensive 1-year program designed to empower you with the skills to excel in the rapidly growing world of online business.<br><br> This program includes in-depth training on: <br>-TikTok Shop management<br> -Shopify store setup and optimization<br>-Amazon Full Stack expertise<br><br> Additionally, it offers a robust foundation in Digital Marketing, enabling you to drive traffic and boost sales. <br>The program also includes Spoken English to enhance your communication skills and a Freelancing module to help you monetize your expertise on platforms like Fiverr and Upwork.",
    "e-commerce degree": "Edify's E-commerce Micro-Degree is a comprehensive 1-year program designed to empower you with the skills to excel in the rapidly growing world of online business.<br><br> This program includes in-depth training on: <br>-TikTok Shop management<br> -Shopify store setup and optimization<br>-Amazon Full Stack expertise<br><br> Additionally, it offers a robust foundation in Digital Marketing, enabling you to drive traffic and boost sales. <br>The program also includes Spoken English to enhance your communication skills and a Freelancing module to help you monetize your expertise on platforms like Fiverr and Upwork.",
    "Art and Design With AI": "Edify's Art and Design Micro-Degree is a 1-year program crafted to provide you with the creative and technical skills needed to succeed in the design industry.<br> The program covers :<br>-3D modeling<br>-Video editing<br> -2D animation<br> -UI/UX designing<br>-Graphic designing <br><br> In addition to these core subjects, you'll also enhance your communication skills with a Spoken English course and learn how to build a successful freelancing career through our Freelancing module, preparing you to thrive as a professional in the dynamic world of art and design.",
    "art design micro degree": "Edify's Art and Design Micro-Degree is a 1-year program crafted to provide you with the creative and technical skills needed to succeed in the design industry.<br> The program covers :<br>-3D modeling<br>-Video editing<br> -2D animation<br> -UI/UX designing<br>-Graphic designing <br><br> In addition to these core subjects, you'll also enhance your communication skills with a Spoken English course and learn how to build a successful freelancing career through our Freelancing module, preparing you to thrive as a professional in the dynamic world of art and design.",
    "Digital Marketing with AI": "Edify's Digital Marketing Micro-Degree is a 1-year program designed to equip you with the essential skills to excel in the online marketing world. <br>The program includes in-depth training in:<br> -SEO<br>-Email marketing<br>-Google AdWords<br>-Content writing<br>-Social media marketing<br><br> Alongside these technical skills, you'll also enhance your communication with a Spoken English course and gain insights into building a successful freelancing career.",
    "marketing degree": "Edify's Digital Marketing Micro-Degree is a 1-year program designed to equip you with the essential skills to excel in the online marketing world. <br>The program includes in-depth training in:<br> -SEO<br>-Email marketing<br>-Google AdWords<br>-Content writing<br>-Social media marketing<br><br> Alongside these technical skills, you'll also enhance your communication with a Spoken English course and gain insights into building a successful freelancing career.",
    "digital degree micro": "Edify's Digital Marketing Micro-Degree is a 1-year program designed to equip you with the essential skills to excel in the online marketing world. <br>The program includes in-depth training in:<br> -SEO<br>-Email marketing<br>-Google AdWords<br>-Content writing<br>-Social media marketing<br><br> Alongside these technical skills, you'll also enhance your communication with a Spoken English course and gain insights into building a successful freelancing career.",
    "Art and design programs":"Edify offers a creative and technical Art and Design program that includes: <br>-3D Modeling<br>-Video Editing<br>-2D Animation<br>-UI/UX Designing<br>-Graphic Designing. <br><br.This program is designed to help you develop the skills needed to create stunning visual content, design user-friendly interfaces, and work with industry-standard tools in the dynamic world of art and design.",
    "Art and design details": "Edify offers a creative and technical Art and Design program that includes: <br>-3D Modeling<br>-Video Editing<br>-2D Animation<br>-UI/UX Designing<br>-Graphic Designing. <br><br.This program is designed to help you develop the skills needed to create stunning visual content, design user-friendly interfaces, and work with industry-standard tools in the dynamic world of art and design.",
    "Art": "Edify offers a creative and technical Art and Design program that includes: <br>-3D Modeling<br>-Video Editing<br>-2D Animation<br>-UI/UX Designing<br>-Graphic Designing. <br><br.This program is designed to help you develop the skills needed to create stunning visual content, design user-friendly interfaces, and work with industry-standard tools in the dynamic world of art and design.",
    "design": "Edify offers a creative and technical Art and Design program that includes: <br>-3D Modeling<br>-Video Editing<br>-2D Animation<br>-UI/UX Designing<br>-Graphic Designing. <br><br.This program is designed to help you develop the skills needed to create stunning visual content, design user-friendly interfaces, and work with industry-standard tools in the dynamic world of art and design.",
    "Art and design ": "Edify offers a creative and technical Art and Design program that includes: <br>-3D Modeling<br>-Video Editing<br>-2D Animation<br>-UI/UX Designing<br>-Graphic Designing. <br><br.This program is designed to help you develop the skills needed to create stunning visual content, design user-friendly interfaces, and work with industry-standard tools in the dynamic world of art and design.",
    "language programs": "Edify offers a comprehensive Language Program focused on Spoken English. This program is designed to help you improve your communication skills, gain confidence in speaking, and enhance your fluency, making you more effective in both personal and professional settings.",
    "language programs detail": "Edify offers a comprehensive Language Program focused on Spoken English. This program is designed to help you improve your communication skills, gain confidence in speaking, and enhance your fluency, making you more effective in both personal and professional settings.",
    "AI programs": "Edify offers cutting-edge AI programs to help you stay ahead in the tech industry. Our programs include:<br>-Data Science<br>-Generative AI<br>-AI Automation<br>-API Development<br>All designed to equip you with the skills needed to excel in the rapidly evolving field of artificial intelligence.<br> Whether you want to analyze data, create AI models, or develop automated systems, Edify has the right program for you.",
    "AI": "Edify offers cutting-edge AI programs to help you stay ahead in the tech industry. Our programs include:<br>-Data Science<br>-Generative AI<br>-AI Automation<br>-API Development<br>All designed to equip you with the skills needed to excel in the rapidly evolving field of artificial intelligence.<br> Whether you want to analyze data, create AI models, or develop automated systems, Edify has the right program for you.",
    "ai": "Edify offers cutting-edge AI programs to help you stay ahead in the tech industry. Our programs include:<br>-Data Science<br>-Generative AI<br>-AI Automation<br>-API Development<br>All designed to equip you with the skills needed to excel in the rapidly evolving field of artificial intelligence.<br> Whether you want to analyze data, create AI models, or develop automated systems, Edify has the right program for you.",
    "Artificial intelligence": "Edify offers cutting-edge AI programs to help you stay ahead in the tech industry. Our programs include:<br>-Data Science<br>-Generative AI<br>-AI Automation<br>-API Development<br>All designed to equip you with the skills needed to excel in the rapidly evolving field of artificial intelligence.<br> Whether you want to analyze data, create AI models, or develop automated systems, Edify has the right program for you.",
    "artificial intelligence" : "Edify offers cutting-edge AI programs to help you stay ahead in the tech industry. Our programs include:<br>-Data Science<br>-Generative AI<br>-AI Automation<br>-API Development<br>All designed to equip you with the skills needed to excel in the rapidly evolving field of artificial intelligence.<br> Whether you want to analyze data, create AI models, or develop automated systems, Edify has the right program for you.",
    "Digital marketing": "Edify offers a comprehensive Digital Marketing program that covers key areas such as: <br>-SEO<br>-Email Marketing<br>-Google AdWords<br>-Content Writing<br>-Social Media Marketing.<br><br> Our program is designed to equip you with the skills to create effective marketing strategies, drive online traffic, and grow your brand across various digital platforms.",
    "Digital marketing details": "Edify offers a comprehensive Digital Marketing program that covers key areas such as: <br>-SEO<br>-Email Marketing<br>-Google AdWords<br>-Content Writing<br>-Social Media Marketing.<br><br> Our program is designed to equip you with the skills to create effective marketing strategies, drive online traffic, and grow your brand across various digital platforms.",
    "marketing": "Edify offers a comprehensive Digital Marketing program that covers key areas such as: <br>-SEO<br>-Email Marketing<br>-Google AdWords<br>-Content Writing<br>-Social Media Marketing.<br><br> Our program is designed to equip you with the skills to create effective marketing strategies, drive online traffic, and grow your brand across various digital platforms.",
    "digital marketing": "Edify offers a comprehensive Digital Marketing program that covers key areas such as: <br>-SEO<br>-Email Marketing<br>-Google AdWords<br>-Content Writing<br>-Social Media Marketing.<br><br> Our program is designed to equip you with the skills to create effective marketing strategies, drive online traffic, and grow your brand across various digital platforms.",
    "Digital marketing program": "Edify offers a comprehensive Digital Marketing program that covers key areas such as: <br>-SEO<br>-Email Marketing<br>-Google AdWords<br>-Content Writing<br>-Social Media Marketing.<br><br> Our program is designed to equip you with the skills to create effective marketing strategies, drive online traffic, and grow your brand across various digital platforms.",
    "E commerce": "Edify offers a specialized E-commerce program that includes: <br>-TikTok Shop<br>-Shopify Store Setup and Optimization<br>-Amazon Full Stack.<br><br>This program is designed to equip you with the skills to build and manage successful online stores, leverage social media platforms for sales, and handle the full e-commerce process on Amazon.",
    "E commerce details": "Edify offers a specialized E-commerce program that includes: <br>-TikTok Shop<br>-Shopify Store Setup and Optimization<br>-Amazon Full Stack.<br><br>This program is designed to equip you with the skills to build and manage successful online stores, leverage social media platforms for sales, and handle the full e-commerce process on Amazon.",
    "Development": "Edify offers a comprehensive Development program that includes:<br>-WordPress<br>-App Development with Java<br>-App Development with Kotlin<br>-Web Development.<br><br>This program is designed to provide you with hands-on experience and the skills necessary to build websites, mobile apps, and powerful online platforms, preparing you for a successful career in software development.",
    "Development details": "Edify offers a comprehensive Development program that includes:<br>-WordPress<br>-App Development with Java<br>-App Development with Kotlin<br>-Web Development.<br><br>This program is designed to provide you with hands-on experience and the skills necessary to build websites, mobile apps, and powerful online platforms, preparing you for a successful career in software development.",
    "E commerce programs": "Edify offers a specialized E-commerce program that includes: <br>-TikTok Shop<br>-Shopify Store Setup and Optimization<br>-Amazon Full Stack.<br><br>This program is designed to equip you with the skills to build and manage successful online stores, leverage social media platforms for sales, and handle the full e-commerce process on Amazon.",
    "Development programs": "Edify offers a comprehensive Development program that includes:<br>-WordPress<br>-App Development with Java<br>-App Development with Kotlin<br>-Web Development.<br><br>This program is designed to provide you with hands-on experience and the skills necessary to build websites, mobile apps, and powerful online platforms, preparing you for a successful career in software development."
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()

    if 'message' in data:
        user_message = data['message'].strip().lower()

        # Tokenize and clean the user message
        tokens = word_tokenize(user_message)
        print(f"Tokens: {tokens}")

        # Load stopwords properly from NLTK
        stop_words = set(stopwords.words('english'))

        # Preprocess: Remove extra words that may be irrelevant (stop words removal)
        cleaned_message = ' '.join(
            [word for word in tokens if word not in stop_words])  # Remove stopwords
        print(f"Cleaned Message: {cleaned_message}")

        # Get course names, aliases, and categories for matching
        all_course_names = list(courses.keys()) if 'courses' in globals() else[]
        all_aliases = [alias for details in courses.values() for alias in details.get('aliases',[])]
        all_categories = [normalize_text(details['category']) for details in courses.values()]
        all_options = all_course_names + all_aliases + all_categories

        # Perform fuzzy matching for category, course, and keyword (adjust thresholds for longer sentences)
        category_match = process.extractOne(cleaned_message, all_categories, score_cutoff=50)
        category_score = category_match[1] if category_match else 0
        category_text = category_match[0] if category_match else ""

        course_match = process.extractOne(cleaned_message, all_course_names + all_aliases, score_cutoff=50)
        course_score = course_match[1] if course_match else 0
        course_text = course_match[0] if course_match else ""

        keyword_match = process.extractOne(cleaned_message, KEYWORDS.keys(), score_cutoff=50) if 'KEYWORDS' in globals() else None
        keyword_score = keyword_match[1] if keyword_match else 0
        keyword_text = keyword_match[0] if keyword_match else ""

        print(f"Category Match: {category_text}, Score: {category_score}")
        print(f"Course Match: {course_text}, Score: {course_score}")
        print(f"Keyword Match: {keyword_text}, Score: {keyword_score}")

        # Priority logic: Match the highest scoring option
        if category_score > max(course_score, keyword_score) and category_score > 50:
            matched_courses = get_courses_by_category(category_text)
            if matched_courses:
                formatted_courses = '<br>'.join(f"- {course['Name']}" for course in matched_courses)
                return jsonify({
                    "reply": f"Courses under '{category_text}' category:<br>{formatted_courses}"
                })
            else:
                return jsonify({
                    "reply": f"Sorry, no courses found under that category. Would you like to try a different one?"
                })

        if course_score > keyword_score and course_score > 40:
            for course, details in courses.items():
                if course_text == course or course_text in details['aliases']:
                    return jsonify({
                        "reply": f"Course Details: <br>"
                                 f"Course Name: {details['Name']}<br>"
                                 f"Category: {details['category']}<br>"
                                 f"Duration: {details['duration']}<br>"
                                 f"Discount: {details['discount']}<br>"
                                 f"Level: {details['course_level']}"
                    })

        if keyword_score > course_score and keyword_score > 40:
            return jsonify({"reply": KEYWORDS[keyword_text]})

        # If no match found, general information
        return jsonify({
            "reply": "I am sorry, I have no information about this in my Dataset.For further information reach us at <br>Phone: 03218886640<br>or Visit us at 4th Floor, College of IT Building, Susan Road, Faisalabad."
        })

    # Handle other question types
    if 'questionType' in data:
        question_type = data['questionType']

        if question_type == 'courses':
            formatted_categories = '<br>'.join(f"- {category}" for category in categories)
            return jsonify({
                "reply": f"We offer courses in the following categories:<br>{formatted_categories}<br>"
                         f"Please type the category you're interested in, and I'll show you the courses available."
            })

        if question_type == 'contact':
            return jsonify({
                "reply": "You can reach us at:<br>Phone: 03218886640<br>Visit: 4th Floor, College of IT Building, Susan Road, Faisalabad."
            })

    if question_type == 'about':
        return jsonify({
            "reply": "Edify offers:<br>"
                     "- Cutting-edge tech courses tailored to meet the demands of today's fast-evolving industry.<br>"
                     "- Taught by seasoned professionals.<br>"
                     "- Hands-on learning in a well-equipped, modern classroom environment.<br>"
                     "- From foundational skills to advanced expertise, Edify ensures students are empowered to excel."
        })

    if question_type == 'micro_degree':
        return jsonify({
            "reply": "Micro-Degree programs are comprehensive 1-year courses designed to equip you with industry-ready skills.<br>"
                     "Programs offered include:<br><br>"
                     "- Software Engineering with AI<br>"
                     "- Art and Design with AI<br>"
                     "- Digital Marketing with AI<br>"
                     "- E-commerce with AI<br><br>"
                     "Each program also includes:<br>"
                     "- A Spoken English language course to enhance communication skills<br>"
                     "- A Freelancing course to help you build a successful career in the freelance market.<br><br>"
                     "These programs are perfect for individuals looking to excel in their fields with a strong foundation in AI and practical skills.<br><br>"
                     "Please select the one you're interested in. So, I can provide you further details"
        })

    return jsonify({
        "reply": "For further information reach us at <br>Phone: 03218886640<br>or Visit us at 4th Floor, College of IT Building, Susan Road, Faisalabad."
    })


if __name__ == '__main__':
    app.run(debug=True)