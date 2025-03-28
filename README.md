# Quiz-Master
# Quiz Master - V1

## Author: Sumit Kumar  
**Email:** 22f3002869@ds.study.iitm.ac.in  / nehra59378@gmail.com

## Project Overview
Quiz Master - V1 is a multi-user exam preparation platform designed to help students practice quizzes based on different subjects and chapters. It includes role-based access for users and administrators, quiz management, scoring, and analytical insights through summary charts.

## Technologies Used
- Python
- Flask
- Flask SQLAlchemy
- Flask-Login
- Jinja2 Templates
- Bootstrap (HTML & CSS Styling)
- SQLite (Data Storage)
- Chart.js (Data Visualization)

## Database Schema
The database consists of the following entities:

### 1. Admin
- Stores admin details
- **Key fields:** `id`, `username`, `email`, `password`, `full_name`, `phone_number`, `date_created`, `role`

### 2. User
- Stores user details and authentication information
- **Key fields:** `id`, `username`, `email`, `password`, `full_name`, `qualification`, `dob`, `role`, `is_active`, `date_created`, `is_admin`

### 3. Subject
- Represents different subjects
- **Key fields:** `id`, `name`, `description`
- **Relation:** One-to-Many with Chapter, Quiz

### 4. Chapter
- Represents chapters within a subject
- **Key fields:** `id`, `name`, `description`, `subject_id`
- **Relation:** One-to-Many with Quiz

### 5. Quiz
- A quiz under a specific chapter
- **Key fields:** `id`, `title`, `subject_id`, `chapter_id`, `date_of_quiz`, `time_duration`, `remarks`
- **Relation:** One-to-Many with Question, Score, UserAnswer

### 6. Question
- Represents a question in a quiz
- **Key fields:** `id`, `quiz_id`, `question_statement`, `option1`, `option2`, `option3`, `option4`, `correct_option`
- **Relation:** One-to-Many with UserAnswer

### 7. Score
- Stores user quiz attempts and scores
- **Key fields:** `id`, `quiz_id`, `user_id`, `time_stamp_of_attempt`, `total_score`, `is_correct`

### 8. UserAnswer
- Stores user responses for each question in a quiz
- **Key fields:** `id`, `user_id`, `quiz_id`, `question_id`, `selected_option`, `is_correct`

## Architecture Design
The project follows the **Model-View-Controller (MVC)** architecture:

- **Controllers:** Contains route handlers for Home, Admin, and User functionalities.
- **Templates:** Contains Jinja2 HTML templates structured into subfolders.
- **Models:** Defines database models as per the schema.
- **Static:** Contains Images, CSS, and JavaScript files.
- **Database:** SQLite database file.
- **Application:** Configuration files.

## Main Features and Functionality

### Admin Controls
- Manage subjects, chapters, quizzes, and users.
- View detailed analytics through summary charts.
- Monitor quiz participation and user performance.

### Users
- Register and log in to take quizzes.
- View past quiz scores and performance.
- Profile section to update personal details and change passwords.
- Summary charts displaying quiz performance and statistics.


## Video Demonstration

[![Watch the Video](https://img.youtube.com/vi/dQw4w9WgXcQ/0.jpg)](https://drive.google.com/file/d/1-U62BpfIovZoIIgEQvImaFLGwSX0NGMu/view?usp=sharing)

[Click here to watch the video](https://drive.google.com/file/d/1-U62BpfIovZoIIgEQvImaFLGwSX0NGMu/view?usp=sharing)


---
This `README.md` provides an overview of Quiz Master - V1, covering its functionality, database schema, and implementation details.

