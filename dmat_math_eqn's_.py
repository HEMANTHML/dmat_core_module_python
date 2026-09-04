import random

LETTERS = ["A", "B", "C", "D"]


# ---------------------------------------------------------------------------
# Core idea: pick hidden solution values FIRST, then build equations that
# encode relationships consistent with those values, then SHUFFLE the
# equation order so the "base variable" isn't obviously first, matching the
# real dMAT exercises (e.g. Exercise 5/6 where B or C is the hidden anchor
# but appears buried in the middle of the equation list).
# ---------------------------------------------------------------------------


def make_relation(src_letter, src_val, dst_letter, rng, exclude_ops=None):
    """
    Build one equation that defines dst in terms of src, choosing an
    operation and constant/multiplier such that dst stays in [1,20] and
    integer. Returns (equation_string, dst_val, op_used).
    exclude_ops: set of op names to avoid (used to force variety across
    multiple relations sharing the same source letter).
    """
    exclude_ops = exclude_ops or set()
    ops = [op for op in ["mult", "add", "sub", "div"] if op not in exclude_ops]
    if not ops:
        ops = ["mult", "add", "sub", "div"]  # fallback if everything excluded
    rng.shuffle(ops)

    for op in ops:
        if op == "mult":
            mult = rng.randint(2, 4)
            dst_val = src_val * mult
            if 1 <= dst_val <= 20:
                return f"{mult} × {src_letter} = {dst_letter}", dst_val, "mult"

        elif op == "div":
            divisors = [d for d in range(2, 6) if src_val % d == 0 and src_val // d >= 1]
            if divisors:
                d = rng.choice(divisors)
                dst_val = src_val // d
                if 1 <= dst_val <= 20:
                    return f"{src_letter} ÷ {d} = {dst_letter}", dst_val, "div"

        elif op == "add":
            const = rng.randint(1, 15)
            dst_val = src_val + const
            if 1 <= dst_val <= 20:
                return f"{const} + {src_letter} = {dst_letter}", dst_val, "add"

        elif op == "sub":
            const = rng.randint(1, 15)
            dst_val = src_val - const
            if 1 <= dst_val <= 20:
                return f"{src_letter} - {const} = {dst_letter}", dst_val, "sub"

    # fallback: identity-ish safe operation
    const = 1
    dst_val = src_val + const if src_val + const <= 20 else src_val - const
    sign = "+" if dst_val == src_val + const else "-"
    return f"{src_letter} {sign} {const} = {dst_letter}", dst_val, "add"


def build_combined_equation(letters, values, rng, num_terms=None):
    """
    Builds one equation combining multiple letters with +/- (and occasional
    x2 coefficients for high difficulty), matching style of:
        A - B + C - D = 2
    Returns the equation string. The combined result is computed directly
    from the true hidden values, so it's automatically consistent.
    """
    if num_terms is None:
        num_terms = len(letters)
    chosen = rng.sample(letters, k=min(num_terms, len(letters)))
    rng.shuffle(chosen)

    terms = []
    total = 0
    for idx, letter in enumerate(chosen):
        if idx == 0:
            sign = 1
        else:
            sign = rng.choice([1, -1])
        coeff = rng.choice([1, 1, 1, 2])  # mostly coefficient 1, occasional 2
        terms.append((sign, coeff, letter))
        total += sign * coeff * values[letter]

    if total < 1:
        # flip overall sign convention by rebuilding with first term negative-safe swap
        # simplest fix: force first sign positive and recompute total, retry construction
        # (rare edge case) -> just take absolute fallback
        return None

    expr = ""
    for idx, (sign, coeff, letter) in enumerate(terms):
        coeff_str = f"{coeff} × " if coeff != 1 else ""
        if idx == 0:
            expr += f"{coeff_str}{letter}"
        else:
            op_str = "+" if sign == 1 else "-"
            expr += f" {op_str} {coeff_str}{letter}"

    return f"{expr} = {total}"


# ---------------------------------------------------------------------------
# LOW difficulty: 2 variables, 2 equations, direct or one-substitution style
# Mirrors: "7 + A = 14 / B - 3 = A"  and  "B ÷ 2 = A / B - A = 8"
# ---------------------------------------------------------------------------
def make_constant_anchor(letter, val, rng):
    """
    Builds a 'constant op letter = number' equation that pins the letter
    to a single numeric value on its own — the critical piece that gives
    the system enough independent information to be uniquely solvable.
    Mirrors the real dMAT style: '7 + A = 14'.
    """
    style = rng.choice(["add", "sub_from_var", "sub_from_const"])
    if style == "add":
        const = rng.randint(1, 15)
        return f"{const} + {letter} = {const + val}"
    elif style == "sub_from_var":
        const = rng.randint(1, min(val - 1, 15)) if val > 1 else 1
        return f"{letter} - {const} = {val - const}"
    else:  # sub_from_const
        const = val + rng.randint(1, 10)
        return f"{const} - {letter} = {const - val}"


def generate_low(rng, max_attempts=200):
    for _ in range(max_attempts):
        a_val = rng.randint(1, 20)

        # Equation 1: anchor A to a plain number — this is what makes A
        # uniquely solvable on its own (matches real Exercise 1 pattern).
        eq1 = make_constant_anchor("A", a_val, rng)

        # Equation 2: derive B from A via a genuine relation (mult/add/sub/div).
        eq2, b_val, _ = make_relation("A", a_val, "B", rng)
        if not (1 <= b_val <= 20):
            continue

        values = {"A": a_val, "B": b_val}
        equations = [eq1, eq2]
        rng.shuffle(equations)
        return equations, values
    return None


# ---------------------------------------------------------------------------
# MEDIUM difficulty: 3 variables, 3 equations, at least one substitution,
# occasional overlapping/redundant constraints (Exercise 3 / Exercise 4 style)
# ---------------------------------------------------------------------------
def generate_medium(rng, max_attempts=200):
    for _ in range(max_attempts):
        template = rng.choice(["chain_then_combine", "dual_path_to_shared_var"])

        if template == "chain_then_combine":
            # C -> A (relation), then A + C -> B (combined)
            c_val = rng.randint(1, 9)
            eq1, a_val, _ = make_relation("C", c_val, "A", rng)
            if not (1 <= a_val <= 20):
                continue
            values = {"A": a_val, "C": c_val}
            eq2 = build_combined_equation(["A", "C"], values, rng, num_terms=2)
            if eq2 is None:
                continue
            # derive B from a simple expression of A and C
            b_val = a_val + c_val if (a_val + c_val) <= 20 else abs(a_val - c_val)
            if not (1 <= b_val <= 20):
                continue
            eq3 = f"A + C = {b_val}" if rng.random() < 0.5 else f"2 × A - C = {2*a_val - c_val}"
            # simplify: just define B via a clean relation from A
            values["B"] = b_val
            eq3, b_val_check, _ = make_relation("A", a_val, "B", rng)
            values["B"] = b_val_check
            equations = [eq1, eq2, eq3]

        else:
            # dual_path_to_shared_var: A and B both derived independently,
            # then C depends on one of them (Exercise 4 style: two eqs pin
            # down A/B, third derives C)
            b_val = rng.randint(2, 18)
            const = rng.randint(b_val + 1, 20)
            a_val = const - b_val  # "const - B = A"
            eq1 = f"{const} - B = A"
            if not (1 <= a_val <= 20):
                continue

            # second relation must ALSO be consistent with same A, B (redundant constraint)
            if a_val != 0 and b_val % 1 == 0:
                # B ÷ n = A  requires B = n*A
                possible_n = [n for n in range(2, 6) if b_val == n * a_val]
                if not possible_n:
                    continue
                n = rng.choice(possible_n)
                eq2 = f"B ÷ {n} = A"
            else:
                continue

            eq3, c_val, _ = make_relation("A", a_val, "C", rng)
            if not (1 <= c_val <= 20):
                continue

            values = {"A": a_val, "B": b_val, "C": c_val}
            equations = [eq1, eq2, eq3]

        # Reject if any two letters ended up with the same numeric value —
        # keeps puzzles from feeling degenerate, matches real dMAT style.
        if len(set(values.values())) != len(values):
            continue

        rng.shuffle(equations)
        return equations, values
    return None


# ---------------------------------------------------------------------------
# HIGH difficulty: 4 (or 3) variables, one hidden "base" variable that
# 3 other letters depend on, plus ONE combined equation tying them together.
# Mirrors Exercise 5 (base = B) and Exercise 6 (base = C).
# ---------------------------------------------------------------------------
def generate_high(rng, num_vars=4, max_attempts=300):
    for _ in range(max_attempts):
        letters = LETTERS[:num_vars]
        base = rng.choice(letters)
        others = [l for l in letters if l != base]

        base_val = rng.randint(1, 4)  # keep small; others scale up via multipliers

        dep_equations = []
        dep_values = {base: base_val}
        used_ops = set()
        ok = True
        for other in others:
            eq, val, op_used = make_relation(base, base_val, other, rng, exclude_ops=used_ops)
            if not (1 <= val <= 20):
                ok = False
                break
            used_ops.add(op_used)
            dep_equations.append(eq)
            dep_values[other] = val
        if not ok:
            continue

        # Reject if any two letters ended up with the same numeric value —
        # real dMAT questions never have two different letters share a value,
        # since it makes the puzzle feel degenerate/repetitive.
        if len(set(dep_values.values())) != len(dep_values):
            continue

        combined = build_combined_equation(letters, dep_values, rng, num_terms=num_vars)
        if combined is None:
            continue

        equations = dep_equations + [combined]
        rng.shuffle(equations)
        return equations, dep_values
    return None


# ---------------------------------------------------------------------------
# Formatting + batch generation
# ---------------------------------------------------------------------------
def verify_unique_solution(equations, letters, expected_values):
    """
    Brute-force check: try every integer combination of the given letters
    in [1,20] and count how many satisfy ALL displayed equations exactly.
    This directly tests what the STUDENT sees, catching bugs like
    linearly-dependent equations that silently allow multiple solutions.
    """
    import itertools
    import re

    def eq_to_python(eq_str):
        # Convert display format to a Python-evaluable boolean expression.
        s = eq_str
        s = s.replace("×", "*").replace("÷", "/")
        lhs, rhs = s.split("=")
        return lhs.strip(), rhs.strip()

    parsed = [eq_to_python(e) for e in equations]

    matches = []
    ranges = [range(1, 21) for _ in letters]
    for combo in itertools.product(*ranges):
        assignment = dict(zip(letters, combo))
        ok = True
        for lhs, rhs in parsed:
            try:
                lhs_val = eval(lhs, {}, assignment)
                rhs_val = eval(rhs, {}, assignment)
                # division must also be exact for it to count as a valid dMAT answer
                if lhs_val != rhs_val:
                    ok = False
                    break
            except ZeroDivisionError:
                ok = False
                break
        if ok:
            matches.append(assignment)

    is_unique = len(matches) == 1
    matches_expected = is_unique and matches[0] == expected_values
    return is_unique, matches_expected, matches


def format_question(idx, equations):
    lines = [f"Question {idx}"]
    for eq in equations:
        lines.append(f"  {eq}")
    return "\n".join(lines)


def export_to_pdf(questions, solutions, output_path):
    """
    Writes the practice set to a PDF: a title page, one question per block
    with its equations, then a final Answer Key section on new pages.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    )
    from reportlab.lib import colors

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], fontSize=18, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"], fontSize=10, textColor=colors.grey,
        alignment=TA_CENTER, spaceAfter=20
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"], fontSize=13,
        spaceBefore=16, spaceAfter=8, textColor=colors.HexColor("#7A1F4B")
    )
    question_heading_style = ParagraphStyle(
        "QuestionHeading", parent=styles["Heading3"], fontSize=11,
        spaceBefore=10, spaceAfter=4
    )
    equation_style = ParagraphStyle(
        "Equation", parent=styles["Normal"], fontName="Courier",
        fontSize=11, leftIndent=20, spaceAfter=2
    )
    answer_style = ParagraphStyle(
        "Answer", parent=styles["Normal"], fontName="Courier",
        fontSize=10, leftIndent=10, spaceAfter=4
    )

    story = []
    story.append(Paragraph("dMAT-Style Mathematical Equations", title_style))
    story.append(Paragraph("Practice Set — no notes, no calculator, mental solving only", subtitle_style))

    current_label = None
    for i, label, equations in questions:
        if label != current_label:
            display_label = {
                "low": "Low Difficulty", "medium": "Medium Difficulty",
                "high3": "High Difficulty (3 variables)", "high4": "High Difficulty (4 variables)"
            }.get(label, label)
            story.append(Paragraph(display_label, section_style))
            current_label = label

        story.append(Paragraph(f"Question {i}", question_heading_style))
        for eq in equations:
            story.append(Paragraph(eq, equation_style))

    story.append(PageBreak())
    story.append(Paragraph("Answer Key", title_style))
    story.append(Spacer(1, 12))

    answer_rows = []
    for i, values in solutions:
        val_str = ", ".join(f"{k} = {v}" for k, v in sorted(values.items()))
        answer_rows.append([f"Question {i}", val_str])

    table = Table(answer_rows, colWidths=[1.5 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#7A1F4B")),
        ("FONTNAME", (0, 0), (0, -1), "Courier-Bold"),
    ]))
    story.append(table)

    doc.build(story)
    return output_path


def generate_question_batch(rng):
    """Generates and verifies a full 20-question batch. Returns (questions, solutions)."""
    batch_plan = (
        [("low", generate_low)] * 5 +
        [("medium", generate_medium)] * 5 +
        [("high3", lambda r: generate_high(r, num_vars=3))] * 5 +
        [("high4", lambda r: generate_high(r, num_vars=4))] * 5
    )

    questions, solutions = [], []
    for i, (label, gen_fn) in enumerate(batch_plan, start=1):
        found = False
        for attempt in range(20):
            result = gen_fn(rng)
            if result is None:
                continue
            equations, values = result
            letters = sorted(values.keys())
            is_unique, matches_expected, matches = verify_unique_solution(
                equations, letters, values
            )
            if is_unique and matches_expected:
                found = True
                break
        if not found:
            print(f"Failed to generate a verifiably-unique question {i} ({label}) after retries")
            continue
        questions.append((i, label, equations))
        solutions.append((i, values))

    return questions, solutions


def main():
    import sys

    rng = random.Random()  # no fixed seed -> fresh set every run
    questions, solutions = generate_question_batch(rng)

    print("=" * 60)
    print("dMAT-STYLE MATHEMATICAL EQUATIONS — PRACTICE SET (v2)")
    print("=" * 60)
    print()
    for i, label, equations in questions:
        print(format_question(i, equations))
        print()

    print("=" * 60)
    print("ANSWER KEY")
    print("=" * 60)
    for i, values in solutions:
        val_str = ", ".join(f"{k} = {v}" for k, v in sorted(values.items()))
        print(f"Question {i}: {val_str}")

    # PDF export: pass an output path as a command-line argument, or it
    # defaults to 'dmat_equations_practice.pdf' in the current directory.
    output_path = sys.argv[1] if len(sys.argv) > 1 else "dmat_equations_practice.pdf"
    export_to_pdf(questions, solutions, output_path)
    print()
    print(f"PDF written to: {output_path}")


if __name__ == "__main__":
    main()