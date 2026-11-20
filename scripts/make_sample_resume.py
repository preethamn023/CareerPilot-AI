"""Generate a realistic sample resume PDF for testing and demo purposes."""
import fitz

RESUME_TEXT = """Rahul Sharma
rahul.sharma@example.com | +91 98765 43210 | Bengaluru, Karnataka

OBJECTIVE
Final-year MCA student seeking a software developer role where I can apply my
skills in Python, web development and databases to build reliable products.

EDUCATION
MCA - Master of Computer Applications, Bangalore University, 2023 - 2026, CGPA 8.6
BCA - Bachelor of Computer Applications, Bangalore University, 2020 - 2023, CGPA 8.9

TECHNICAL SKILLS
Programming Languages: Python, Java, JavaScript, SQL
Web: HTML, CSS, React, Node.js, Express
Databases: MySQL, MongoDB
Tools: Git, GitHub, VS Code, Postman, Linux

PROJECTS
Student Attendance Portal - Developed a full-stack web application using React,
Node.js, Express and MySQL to digitalise attendance for 4 departments. Built REST
APIs with JWT authentication and role-based access for 3 user types. Reduced
manual attendance work by about 70 percent for faculty.
Expense Tracker App - Built a Python and SQLite desktop application with
matplotlib reports and category-wise budgets. Implemented data export to CSV.
Chat Application - Created a real-time chat app using Node.js, Socket.IO and
MongoDB supporting group chats and typing indicators.

INTERNSHIPS
Web Development Intern, TechSolutions Pvt Ltd, Bangalore (Jun 2025 - Aug 2025)
Worked on internal dashboards with React and REST APIs, fixed 20+ UI bugs and
wrote unit tests for frontend components.

CERTIFICATIONS
Full Stack Web Development - NPTEL (2025)
Python for Data Science - Coursera (2024)

ACHIEVEMENTS
Winner, Smart India Hackathon internal round (2024)
Top 5 percent in Bangalore University coding contest
"""

JD_TEXT = """Software Engineer (Fresher) - CloudPay Solutions, Bengaluru

We are hiring: Software Engineer - Fresher

About the role:
CloudPay Solutions is looking for enthusiastic freshers to join our engineering
team in Bengaluru. You will build and maintain web applications and work with
modern cloud technologies.

Responsibilities:
- Develop and maintain web applications using Python and Django or Flask
- Build responsive user interfaces with React
- Write clean, tested and maintainable code
- Work with relational databases such as PostgreSQL
- Participate in code reviews and agile ceremonies
- Deploy and operate services using Docker and basic AWS

Requirements:
- Bachelor or Master degree in Computer Science or related field (B.Tech / MCA / BCA)
- 0-2 years of experience; strong academic projects count
- Solid understanding of Python and JavaScript
- Knowledge of SQL databases
- Familiarity with Git version control
- Good communication and teamwork skills

Preferred skills (nice to have):
- Docker, Kubernetes
- AWS or other cloud platforms
- CI/CD pipelines
- TypeScript
- Machine Learning basics
"""


def build_resume_pdf(path: str) -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    margin = 50
    y = margin
    for line in RESUME_TEXT.splitlines():
        if not line.strip():
            y += 6
            continue
        size = 13 if line.isupper() and len(line) < 60 else 10
        font = "helv"
        page.insert_text((margin, y), line, fontname=font, fontsize=size)
        y += size + 5
        if y > 800:
            page = doc.new_page(width=595, height=842)
            y = margin
    doc.save(path)
    doc.close()


def build_scanned_pdf(path: str) -> None:
    """A PDF with a blank page (no text) - simulates a scanned resume."""
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    doc.save(path)
    doc.close()


if __name__ == "__main__":
    build_resume_pdf("/tmp/sample_resume.pdf")
    build_scanned_pdf("/tmp/sample_scanned.pdf")
    print("PDFs written to /tmp/sample_resume.pdf and /tmp/sample_scanned.pdf")
    with open("/tmp/sample_jd.txt", "w") as f:
        f.write(JD_TEXT)
    print("JD written to /tmp/sample_jd.txt")
