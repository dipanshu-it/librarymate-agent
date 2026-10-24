"""Library logic: plain Python, no AI. Data is saved in library_db.json."""
import json, os
from datetime import date, timedelta

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library_db.json")
LOAN_DAYS = 14
FINE_PER_DAY = 2  # rupees

BOOKS = [
    {"id": 1, "title": "Python Crash Course", "author": "Eric Matthes", "topic": "python programming beginner", "copies": 3},
    {"id": 2, "title": "Hands-On Machine Learning", "author": "Aurelien Geron", "topic": "machine learning ai data science", "copies": 2},
    {"id": 3, "title": "Introduction to Machine Learning with Python", "author": "Andreas Mueller", "topic": "machine learning python beginner", "copies": 2},
    {"id": 4, "title": "Deep Learning", "author": "Ian Goodfellow", "topic": "deep learning neural networks ai advanced", "copies": 1},
    {"id": 5, "title": "Artificial Intelligence: A Modern Approach", "author": "Stuart Russell", "topic": "artificial intelligence ai", "copies": 2},
    {"id": 6, "title": "Introduction to Algorithms", "author": "Thomas Cormen", "topic": "algorithms data structures dsa", "copies": 3},
    {"id": 7, "title": "Data Structures Using C", "author": "Reema Thareja", "topic": "data structures c programming dsa", "copies": 4},
    {"id": 8, "title": "Let Us C", "author": "Yashavant Kanetkar", "topic": "c programming beginner", "copies": 5},
    {"id": 9, "title": "Operating System Concepts", "author": "Abraham Silberschatz", "topic": "operating systems os", "copies": 2},
    {"id": 10, "title": "Database System Concepts", "author": "Abraham Silberschatz", "topic": "database dbms sql", "copies": 3},
    {"id": 11, "title": "Computer Networks", "author": "Andrew Tanenbaum", "topic": "networks computer networks cn", "copies": 2},
    {"id": 12, "title": "Head First Java", "author": "Kathy Sierra", "topic": "java programming beginner oop", "copies": 3},
    {"id": 13, "title": "Clean Code", "author": "Robert C. Martin", "topic": "software engineering coding best practices", "copies": 1},
    {"id": 14, "title": "Discrete Mathematics and Its Applications", "author": "Kenneth Rosen", "topic": "discrete mathematics maths", "copies": 3},
    {"id": 15, "title": "Web Development with Node and Express", "author": "Ethan Brown", "topic": "web development javascript node", "copies": 2},
    {"id": 16, "title": "Eloquent JavaScript", "author": "Marijn Haverbeke", "topic": "javascript web development beginner", "copies": 2},
    {"id": 17, "title": "Computer Organization and Architecture", "author": "William Stallings", "topic": "computer architecture coa", "copies": 2},
    {"id": 18, "title": "Cryptography and Network Security", "author": "William Stallings", "topic": "security cryptography cyber", "copies": 1},
]
STUDENTS = {"2201": "Aman Verma", "2202": "Riya Sharma", "2203": "Karan Singh", "2204": "Neha Gupta", "2205": "Dipanshu Gupta"}


def _load():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f:
            return json.load(f)
    return {"loans": []}  # each loan: student_id, book_id, issued, due, returned


def _save(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def _book(book_id):
    return next((b for b in BOOKS if b["id"] == int(book_id)), None)


def _available(db, book_id):
    out = sum(1 for l in db["loans"] if l["book_id"] == int(book_id) and not l["returned"])
    return _book(book_id)["copies"] - out


def search_books(query: str) -> dict:
    words = [w for w in query.lower().replace(",", " ").split() if len(w) > 2]
    db = _load()
    scored = []
    for b in BOOKS:
        text = f'{b["title"]} {b["author"]} {b["topic"]}'.lower()
        score = sum(1 for w in words if w in text)
        if score:
            scored.append((score, b))
    scored.sort(key=lambda x: -x[0])
    results = [{"id": b["id"], "title": b["title"], "author": b["author"],
                "available_copies": _available(db, b["id"])} for _, b in scored[:5]]
    return {"query": query, "results": results} if results else {"query": query, "results": [], "note": "No matching books found."}


def check_availability(book_id: int) -> dict:
    b = _book(book_id)
    if not b:
        return {"error": f"Book {book_id} not found."}
    n = _available(_load(), book_id)
    return {"id": b["id"], "title": b["title"], "available_copies": n, "available": n > 0}


def issue_book(student_id: str, book_id: int) -> dict:
    student_id = str(student_id)
    if student_id not in STUDENTS:
        return {"error": f"Student ID {student_id} not found. Valid demo IDs: {', '.join(STUDENTS)}"}
    b = _book(book_id)
    if not b:
        return {"error": f"Book {book_id} not found."}
    db = _load()
    mine = [l for l in db["loans"] if l["student_id"] == student_id and not l["returned"]]
    if len(mine) >= 3:
        return {"error": "Limit reached: a student can hold at most 3 books."}
    if any(l["book_id"] == b["id"] for l in mine):
        return {"error": "You already have this book."}
    if _available(db, b["id"]) <= 0:
        return {"error": f'"{b["title"]}" has no copies available right now. Try another book.'}
    today = date.today()
    loan = {"student_id": student_id, "book_id": b["id"], "issued": str(today),
            "due": str(today + timedelta(days=LOAN_DAYS)), "returned": None}
    db["loans"].append(loan)
    _save(db)
    return {"status": "issued", "student": STUDENTS[student_id], "title": b["title"], "due_date": loan["due"]}


def return_book(student_id: str, book_id: int, days_late_override: int = None) -> dict:
    student_id = str(student_id)
    db = _load()
    for l in db["loans"]:
        if l["student_id"] == student_id and l["book_id"] == int(book_id) and not l["returned"]:
            today = date.today()
            late = (today - date.fromisoformat(l["due"])).days
            if days_late_override is not None:  # for demo purposes
                late = int(days_late_override)
            late = max(late, 0)
            l["returned"] = str(today)
            l["fine"] = late * FINE_PER_DAY
            _save(db)
            return {"status": "returned", "title": _book(book_id)["title"], "days_late": late, "fine_rupees": l["fine"]}
    return {"error": "No active loan found for that student and book."}


def my_dues(student_id: str) -> dict:
    student_id = str(student_id)
    if student_id not in STUDENTS:
        return {"error": f"Student ID {student_id} not found."}
    db = _load()
    today = date.today()
    items, total = [], 0
    for l in db["loans"]:
        if l["student_id"] == student_id and not l["returned"]:
            late = max((today - date.fromisoformat(l["due"])).days, 0)
            fine = late * FINE_PER_DAY
            total += fine
            items.append({"title": _book(l["book_id"])["title"], "due": l["due"], "days_late": late, "fine_rupees": fine})
    return {"student": STUDENTS[student_id], "borrowed": items, "total_fine_rupees": total}
