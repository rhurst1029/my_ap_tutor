"""
Generate two PDFs from a student's practice problem set:
  1. bella_session{N}_questions.pdf  — tasks + starter code + self-check guiding questions
  2. bella_session{N}_solutions.pdf  — solutions + explanations + follow-up challenges + references

Usage: python scripts/generate_practice_pdf.py bella 3
"""
import json, sys, re
from pathlib import Path
from fpdf import FPDF

ROOT = Path(__file__).parent.parent

# ── Per-problem self-check guiding questions (questions PDF) ──────────────────
GUIDING_QUESTIONS = {
    "p1": [
        "What value should I initialize min to, and why can't I use 0?",
        "Which index should my loop start at, and why not index 0?",
        "What condition do I check inside the loop before updating min?",
    ],
    "p2": [
        "What variable do I need to declare before the loop starts?",
        "What is the exact condition that causes count to increment?",
        "What is the difference between > and >= here — does it matter for this problem?",
    ],
    "p3": [
        "What does the outer loop control (rows, columns, or something else)?",
        "How does the inner loop's stopping condition relate to the outer variable i?",
        "When does the newline get printed — inside the inner loop or outside?",
    ],
    "p4": [
        "Which fields should be private, and what does private actually prevent?",
        "What is the difference between a constructor and a regular method?",
        "What must withdraw check BEFORE subtracting? What should it do if the check fails?",
    ],
    "p5": [
        "Why do I need a temporary variable to swap two array elements?",
        "When should the while loop stop — what condition means the two pointers have met?",
        "What happens to the middle element in an odd-length array? Does it need to be moved?",
    ],
}

# ── Per-topic online references (solutions PDF) ───────────────────────────────
REFERENCES = {
    "arrays": [
        ("W3Schools — Java Arrays",
         "https://www.w3schools.com/java/java_arrays.asp",
         "Short, beginner-friendly overview of array syntax, indexing, and loops."),
        ("GeeksForGeeks — Arrays in Java",
         "https://www.geeksforgeeks.org/arrays-in-java/",
         "Covers declaration, initialization, traversal, and common patterns with examples."),
        ("Oracle Java Tutorials — Arrays",
         "https://docs.oracle.com/javase/tutorial/java/nutsandbolts/arrays.html",
         "Official Java documentation on array basics and multidimensional arrays."),
    ],
    "loops": [
        ("W3Schools — Java For Loop",
         "https://www.w3schools.com/java/java_for_loop.asp",
         "Clear examples of for, while, and nested loops with interactive exercises."),
        ("GeeksForGeeks — Loops in Java",
         "https://www.geeksforgeeks.org/loops-in-java/",
         "Covers all loop types with worked examples including nested loop patterns."),
        ("AP CSA Unit 4 — Iteration (Khan Academy)",
         "https://www.khanacademy.org/computing/ap-computer-science-principles",
         "Iteration unit with practice problems aligned to AP CSA exam style."),
    ],
    "classes_and_objects": [
        ("W3Schools — Java Classes and Objects",
         "https://www.w3schools.com/java/java_classes.asp",
         "Step-by-step intro to creating classes, constructors, and object instances."),
        ("GeeksForGeeks — Classes and Objects in Java",
         "https://www.geeksforgeeks.org/classes-objects-java/",
         "Detailed explanation of encapsulation, private fields, and access modifiers."),
        ("Oracle — Object-Oriented Programming Concepts",
         "https://docs.oracle.com/javase/tutorial/java/concepts/index.html",
         "Official tutorial covering objects, classes, inheritance, and encapsulation."),
    ],
    "methods": [
        ("W3Schools — Java Methods",
         "https://www.w3schools.com/java/java_methods.asp",
         "Covers method declaration, parameters, return types, and calling methods."),
        ("GeeksForGeeks — Methods in Java",
         "https://www.geeksforgeeks.org/methods-in-java/",
         "In-depth coverage of static vs instance methods, return values, and overloading."),
    ],
    "2d_arrays": [
        ("W3Schools — Java Multidimensional Arrays",
         "https://www.w3schools.com/java/java_arrays_multi.asp",
         "Clear intro to 2D array syntax, row/column indexing, and nested loop traversal."),
        ("GeeksForGeeks — Multidimensional Arrays in Java",
         "https://www.geeksforgeeks.org/multidimensional-arrays-in-java/",
         "Covers declaration, initialization patterns, and common 2D array algorithms."),
    ],
    "arraylist": [
        ("W3Schools — Java ArrayList",
         "https://www.w3schools.com/java/java_arraylist.asp",
         "Quick-start guide covering add, remove, get, size, and looping over an ArrayList."),
        ("GeeksForGeeks — ArrayList in Java",
         "https://www.geeksforgeeks.org/arraylist-in-java/",
         "Covers the difference between remove(int index) and remove(Object o) with examples."),
    ],
    "strings": [
        ("W3Schools — Java Strings",
         "https://www.w3schools.com/java/java_strings.asp",
         "All common String methods including substring, indexOf, length, and charAt."),
        ("GeeksForGeeks — String in Java",
         "https://www.geeksforgeeks.org/strings-in-java/",
         "Covers immutability, String methods, and common interview-style String problems."),
    ],
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_student_dir(name: str) -> Path:
    safe = re.sub(r'[^\w]', '_', name.lower().strip())
    return ROOT / "data" / "students" / f"{safe}_data"

def s(text: str) -> str:
    """Sanitize text to latin-1 safe characters."""
    return (str(text)
        .replace('\u2014', '--').replace('\u2013', '-')
        .replace('\u2018', "'").replace('\u2019', "'")
        .replace('\u201c', '"').replace('\u201d', '"')
        .replace('\u2022', '*').replace('\u2026', '...')
        .encode('latin-1', errors='replace').decode('latin-1')
    )

# ── Colour palette ────────────────────────────────────────────────────────────
BRAND_BLUE  = (30,  90,  160)
BRAND_LIGHT = (220, 232, 248)
GRAY_BG     = (248, 248, 248)
GRAY_TEXT   = (90,  90,  90)
CODE_BG     = (245, 245, 245)
CODE_BORDER = (200, 200, 200)
BLACK       = (20,  20,  20)
GREEN_DARK  = (20,  110,  55)
GREEN_BG    = (228, 248, 234)
ORANGE      = (175,  80,   0)
ORANGE_BG   = (255, 243, 220)
PURPLE      = (90,  40,  150)
PURPLE_BG   = (240, 232, 255)
TEAL        = (0,   110, 120)
TEAL_BG     = (224, 246, 248)

# ── Base PDF class ────────────────────────────────────────────────────────────

class BasePDF(FPDF):
    subtitle = ""
    student_label = ""
    header_color = BRAND_BLUE

    def header(self):
        self.set_fill_color(*self.header_color)
        self.rect(0, 0, 210, 20, 'F')
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_xy(12, 5)
        self.cell(130, 8, s(self.subtitle))
        self.set_font("Helvetica", "", 8)
        self.set_xy(0, 5)
        self.cell(198, 8, s(self.student_label), align="R")
        self.ln(20)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY_TEXT)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_label(self, text, fg, bg):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*fg)
        self.set_fill_color(*bg)
        self.set_x(14)
        self.cell(0, 6, f"  {text}  ", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(1)

    def body_text(self, text, indent=14, w=182):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*BLACK)
        self.set_x(indent)
        self.multi_cell(w, 5.5, s(text))
        self.ln(1)

    def small_label(self, text, indent=14):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*GRAY_TEXT)
        self.set_x(indent)
        self.cell(0, 5, s(text), new_x="LMARGIN", new_y="NEXT")

    def code_block(self, code_text, indent=14):
        if not code_text:
            return
        lines = code_text.split("\n")
        line_h, pad = 4.8, 4
        block_h = len(lines) * line_h + pad * 2
        x0, y0, w = indent, self.get_y(), 182
        self.set_fill_color(*CODE_BG)
        self.set_draw_color(*CODE_BORDER)
        self.rect(x0, y0, w, block_h, 'FD')
        self.set_font("Courier", "", 8.5)
        self.set_text_color(40, 40, 120)
        for line in lines:
            self.set_xy(x0 + pad, self.get_y() if self.get_y() > y0 else y0 + pad)
            self.cell(w - pad * 2, line_h, s(line), new_x="LMARGIN", new_y="NEXT")
        self.set_y(y0 + block_h + 2)
        self.ln(1)

    def divider(self):
        self.set_draw_color(*CODE_BORDER)
        self.line(14, self.get_y(), 196, self.get_y())
        self.ln(4)

    def problem_header(self, index, title, topic, difficulty):
        diff_colors = {
            "easy":   (20, 130, 60),
            "medium": (150, 90, 0),
            "hard":   (160, 20, 20),
        }
        fg = diff_colors.get(difficulty, diff_colors["medium"])
        self.set_fill_color(*BRAND_BLUE)
        self.rect(14, self.get_y(), 182, 10, 'F')
        self.set_xy(18, self.get_y() + 1.5)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.cell(140, 7, s(f"Problem {index}:  {title}"))
        self.set_font("Helvetica", "", 8)
        self.cell(36, 7, f"{topic}  |  {difficulty}", align="R",
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def check_page(self, needed=40):
        if self.get_y() > 267 - needed:
            self.add_page()


# ── Questions PDF ─────────────────────────────────────────────────────────────

def build_questions_pdf(data: dict, student_name: str, iteration: int) -> Path:
    problems = data["problems"]

    pdf = BasePDF(orientation="P", unit="mm", format="A4")
    pdf.subtitle = "AP CSA Practice -- Questions"
    pdf.student_label = f"Bella  |  Session {iteration}  |  April 12, 2026"
    pdf.header_color = BRAND_BLUE
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(14, 24, 14)
    pdf.add_page()

    # Cover block
    pdf.set_fill_color(*BRAND_LIGHT)
    pdf.rect(14, pdf.get_y(), 182, 30, 'F')
    pdf.set_xy(18, pdf.get_y() + 5)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*BRAND_BLUE)
    pdf.cell(0, 8, "Practice Problems -- Questions", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(18)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRAY_TEXT)
    topics = ", ".join(data.get("weak_topics_targeted", []))
    pdf.cell(0, 6, f"Topics: {topics}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(18)
    pdf.cell(0, 6, f"{len(problems)} problems  |  Write your solutions in IntelliJ before checking the answer key",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GRAY_TEXT)
    pdf.set_x(14)
    pdf.multi_cell(182, 5,
        "For each problem: read the task, answer the self-check questions in your head "
        "or on paper, then write your Java code in IntelliJ. Only open the Solutions "
        "file once you have a working (or attempted) solution.")
    pdf.ln(7)

    for i, prob in enumerate(problems, 1):
        pdf.check_page(needed=70)

        pdf.problem_header(i, prob["title"], prob["topic"], prob["difficulty"])

        # Task
        pdf.section_label("TASK", (10, 80, 140), BRAND_LIGHT)
        pdf.body_text(prob["task"])
        pdf.ln(1)

        # Starter code
        if prob.get("starter_code"):
            pdf.small_label("Starter code (copy this into IntelliJ):")
            pdf.code_block(prob["starter_code"])

        # Self-check guiding questions
        pdf.check_page(needed=40)
        pdf.section_label("BEFORE YOU CODE -- Ask yourself:", *[PURPLE, PURPLE_BG])
        guiding = GUIDING_QUESTIONS.get(prob["id"], [])
        for j, q in enumerate(guiding, 1):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*BLACK)
            pdf.set_x(18)
            # Question number
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*PURPLE)
            pdf.cell(7, 5.5, f"{j}.")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*BLACK)
            pdf.set_x(25)
            pdf.multi_cell(171, 5.5, s(q))
            pdf.ln(0.5)

        # Answer space hint
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.set_x(14)
        pdf.cell(0, 5, "Write your solution in IntelliJ, then check bella_session3_solutions.pdf",
                 new_x="LMARGIN", new_y="NEXT")

        pdf.ln(4)
        pdf.divider()

    out = get_student_dir(student_name) / f"bella_session{iteration}_questions.pdf"
    pdf.output(str(out))
    return out


# ── Solutions PDF ─────────────────────────────────────────────────────────────

def build_solutions_pdf(data: dict, student_name: str, iteration: int) -> Path:
    problems = data["problems"]

    pdf = BasePDF(orientation="P", unit="mm", format="A4")
    pdf.subtitle = "AP CSA Practice -- Solutions & References"
    pdf.student_label = f"Bella  |  Session {iteration}  |  April 12, 2026"
    pdf.header_color = GREEN_DARK
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(14, 24, 14)
    pdf.add_page()

    # Cover block
    pdf.set_fill_color(*GREEN_BG)
    pdf.rect(14, pdf.get_y(), 182, 30, 'F')
    pdf.set_xy(18, pdf.get_y() + 5)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*GREEN_DARK)
    pdf.cell(0, 8, "Practice Problems -- Solutions & References", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(18)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRAY_TEXT)
    pdf.cell(0, 6, "Review this file AFTER attempting each problem on your own.",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(18)
    pdf.cell(0, 6,
             "Each solution includes an explanation and links to read more on the topic.",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    for i, prob in enumerate(problems, 1):
        pdf.check_page(needed=70)

        pdf.problem_header(i, prob["title"], prob["topic"], prob["difficulty"])

        # Brief task recap
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.set_x(14)
        # Truncate task for recap
        task_short = s(prob["task"])[:180] + ("..." if len(prob["task"]) > 180 else "")
        pdf.multi_cell(182, 5, f"Task recap: {task_short}")
        pdf.ln(3)

        # Solution code
        pdf.section_label("SOLUTION", *[GREEN_DARK, GREEN_BG])
        pdf.code_block(prob["solution"])

        # Explanation
        pdf.check_page(needed=30)
        pdf.small_label("How it works:")
        pdf.body_text(prob["solution_explanation"])
        pdf.ln(1)

        # Follow-up challenges
        pdf.check_page(needed=35)
        pdf.section_label("FOLLOW-UP CHALLENGES", *[ORANGE, ORANGE_BG])
        for j, challenge in enumerate(prob.get("follow_up_challenges", []), 1):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*ORANGE)
            pdf.set_x(18)
            pdf.cell(7, 5.5, f"{j}.")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*BLACK)
            pdf.set_x(25)
            pdf.multi_cell(171, 5.5, s(challenge))
            pdf.ln(0.5)

        # References
        pdf.check_page(needed=40)
        pdf.ln(2)
        pdf.section_label("READ MORE ON THIS TOPIC", *[TEAL, TEAL_BG])
        refs = REFERENCES.get(prob["topic"], [])
        if not refs:
            pdf.body_text("See GeeksForGeeks or W3Schools for Java tutorials on this topic.")
        else:
            for ref_title, ref_url, ref_desc in refs:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*TEAL)
                pdf.set_x(16)
                pdf.cell(0, 5, s(ref_title), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*BRAND_BLUE)
                pdf.set_x(16)
                pdf.cell(0, 4.5, s(ref_url), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "I", 8.5)
                pdf.set_text_color(*GRAY_TEXT)
                pdf.set_x(16)
                pdf.multi_cell(178, 4.5, s(ref_desc))
                pdf.ln(2)

        pdf.ln(3)
        pdf.divider()

    out = get_student_dir(student_name) / f"bella_session{iteration}_solutions.pdf"
    pdf.output(str(out))
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    student   = sys.argv[1] if len(sys.argv) > 1 else "bella"
    iteration = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    student_dir   = get_student_dir(student)
    practice_path = student_dir / f"practice_{iteration}.json"

    if not practice_path.exists():
        print(f"ERROR: No practice file at {practice_path}")
        sys.exit(1)

    data = json.loads(practice_path.read_text())

    q_path = build_questions_pdf(data, student, iteration)
    print(f"Questions PDF -> {q_path}")

    s_path = build_solutions_pdf(data, student, iteration)
    print(f"Solutions PDF -> {s_path}")

if __name__ == "__main__":
    main()
