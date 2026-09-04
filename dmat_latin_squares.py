import random

LETTERS_5 = list("ABCDE")
N = 5


# ---------------------------------------------------------------------------
# Step 1: generate a valid, reasonably-random full 5x5 Latin square.
# Method: take the canonical cyclic Latin square L[i][j] = (i+j) mod 5,
# then randomly permute rows, columns, and the symbol labels. Permuting any
# of these on a valid Latin square always yields another valid Latin square.
# ---------------------------------------------------------------------------
def generate_full_latin_square(rng, letters=LETTERS_5):
    n = len(letters)
    base = [[(i + j) % n for j in range(n)] for i in range(n)]

    row_perm = list(range(n))
    col_perm = list(range(n))
    sym_perm = list(range(n))
    rng.shuffle(row_perm)
    rng.shuffle(col_perm)
    rng.shuffle(sym_perm)

    grid = [[None] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            val = base[row_perm[i]][col_perm[j]]
            grid[i][j] = letters[sym_perm[val]]
    return grid


# ---------------------------------------------------------------------------
# Step 2: propagation solver — repeatedly find any blank cell where the row
# + column already exclude all but one letter (a "forced single"), fill it,
# and record the ORDER cells get solved in. This is exactly the technique
# used in the official solution walkthroughs ("only one letter remains
# possible in this row/column"). The depth at which the target cell gets
# solved (its position in the forcing order) IS the difficulty measure.
# ---------------------------------------------------------------------------
def solve_and_get_depth(revealed_grid, target_cell, letters=LETTERS_5, max_iterations=200):
    n = len(letters)
    grid = [row[:] for row in revealed_grid]
    depth = 0

    for _ in range(max_iterations):
        assigned_this_round = False
        for r in range(n):
            for c in range(n):
                if grid[r][c] is not None:
                    continue
                row_vals = {grid[r][cc] for cc in range(n) if grid[r][cc] is not None}
                col_vals = {grid[rr][c] for rr in range(n) if grid[rr][c] is not None}
                candidates = set(letters) - row_vals - col_vals
                if len(candidates) == 1:
                    grid[r][c] = next(iter(candidates))
                    depth += 1
                    assigned_this_round = True
                    if (r, c) == target_cell:
                        return depth
        if not assigned_this_round:
            return None  # stuck — target isn't forced by this reveal set at all

    return None


# ---------------------------------------------------------------------------
# Step 3: construct a puzzle by hiding a random subset of cells (excluding
# the target), then checking the resulting solve depth against the desired
# difficulty range. Retries with fresh random reveal sets until a match is
# found. Because propagation-based forcing is logically sound (if a cell's
# value is uniquely forced by elimination, no other valid completion could
# give it a different value), passing this check IS a valid uniqueness
# proof for the target cell — no separate brute-force check is needed.
# ---------------------------------------------------------------------------
DEPTH_RANGES = {"low": (1, 2), "medium": (3, 5), "high": (6, 10)}
REVEAL_COUNT_RANGES = {"low": (12, 16), "medium": (9, 13), "high": (6, 10)}


def generate_latin_square_puzzle(difficulty, rng, letters=LETTERS_5, max_attempts=800):
    lo, hi = DEPTH_RANGES[difficulty]
    reveal_lo, reveal_hi = REVEAL_COUNT_RANGES[difficulty]
    n = len(letters)

    for _ in range(max_attempts):
        full_grid = generate_full_latin_square(rng, letters)
        target = (rng.randrange(n), rng.randrange(n))

        reveal_count = rng.randint(reveal_lo, reveal_hi)
        all_other_cells = [(r, c) for r in range(n) for c in range(n) if (r, c) != target]
        rng.shuffle(all_other_cells)
        revealed_cells = set(all_other_cells[:reveal_count])

        revealed_grid = [
            [full_grid[r][c] if (r, c) in revealed_cells else None for c in range(n)]
            for r in range(n)
        ]

        depth = solve_and_get_depth(revealed_grid, target, letters)
        if depth is not None and lo <= depth <= hi:
            answer = full_grid[target[0]][target[1]]
            return revealed_grid, target, answer, depth

    return None


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def format_grid(revealed_grid, target_cell, letters=LETTERS_5):
    n = len(letters)
    lines = []
    for r in range(n):
        row_cells = []
        for c in range(n):
            if (r, c) == target_cell:
                row_cells.append("?")
            elif revealed_grid[r][c] is not None:
                row_cells.append(revealed_grid[r][c])
            else:
                row_cells.append(".")
        lines.append("  " + " | ".join(row_cells))
    lines.append(f"  (Response options: {', '.join(letters)})")
    return "\n".join(lines)


def export_to_pdf(questions_data, output_path, letters=LETTERS_5):
    """
    Writes the practice set to a PDF, rendering each Latin Square as an
    actual bordered 5x5 table (not pipe-separated text), with the '?' cell
    highlighted, matching the visual style of the real dMAT exercises.
    questions_data: list of (idx, difficulty, depth, revealed_grid, target, answer)
    """
    from reportlab.lib.pagesizes import letter as pagesize_letter
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    )
    from reportlab.lib import colors

    doc = SimpleDocTemplate(
        output_path, pagesize=pagesize_letter,
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
        spaceBefore=18, spaceAfter=8, textColor=colors.HexColor("#7A1F4B")
    )
    question_heading_style = ParagraphStyle(
        "QuestionHeading", parent=styles["Heading3"], fontSize=11, spaceAfter=6
    )
    options_style = ParagraphStyle(
        "Options", parent=styles["Normal"], fontSize=9,
        textColor=colors.grey, spaceBefore=4, spaceAfter=4
    )

    story = []
    story.append(Paragraph("dMAT-Style Latin Squares", title_style))
    story.append(Paragraph("Practice Set — no notes, mental solving only", subtitle_style))

    n = len(letters)
    cell_size = 0.42 * inch

    current_difficulty = None
    for idx, difficulty, depth, revealed_grid, target, answer in questions_data:
        if difficulty != current_difficulty:
            story.append(Paragraph(f"{difficulty.capitalize()} Difficulty", section_style))
            current_difficulty = difficulty

        block = []
        block.append(Paragraph(f"Question {idx}  (solve depth: {depth})", question_heading_style))

        table_data = []
        for r in range(n):
            row_cells = []
            for c in range(n):
                if (r, c) == target:
                    row_cells.append("?")
                elif revealed_grid[r][c] is not None:
                    row_cells.append(revealed_grid[r][c])
                else:
                    row_cells.append("")
            table_data.append(row_cells)

        grid_table = Table(
            table_data,
            colWidths=[cell_size] * n,
            rowHeights=[cell_size] * n,
        )
        table_style_cmds = [
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 13),
        ]
        # highlight the target ('?') cell
        tr, tc = target
        table_style_cmds.append(("BACKGROUND", (tc, tr), (tc, tr), colors.HexColor("#E8E8E8")))
        table_style_cmds.append(("TEXTCOLOR", (tc, tr), (tc, tr), colors.HexColor("#7A1F4B")))
        grid_table.setStyle(TableStyle(table_style_cmds))

        block.append(grid_table)
        block.append(Paragraph(f"Response options: {', '.join(letters)}", options_style))
        block.append(Spacer(1, 10))

        # keep each question's heading+grid together on one page where possible
        story.append(KeepTogether(block))

    story.append(Spacer(1, 12))
    from reportlab.platypus import PageBreak
    story.append(PageBreak())
    story.append(Paragraph("Answer Key", title_style))
    story.append(Spacer(1, 12))

    answer_rows = [["Question", "Answer", "Solve Depth"]]
    for idx, difficulty, depth, revealed_grid, target, answer in questions_data:
        answer_rows.append([f"Question {idx}", answer, str(depth)])

    ans_table = Table(answer_rows, colWidths=[1.8 * inch, 1.5 * inch, 1.5 * inch])
    ans_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
        ("TEXTCOLOR", (0, 1), (0, -1), colors.HexColor("#7A1F4B")),
    ]))
    story.append(ans_table)

    doc.build(story)
    return output_path


def generate_batch(rng, plan=None):
    """Generates the full puzzle batch. Returns list of
    (idx, difficulty, depth, revealed_grid, target, answer)."""
    if plan is None:
        plan = (
            [("low", 5)] +
            [("medium", 5)] +
            [("high", 10)]
        )

    idx = 1
    questions_data = []
    for difficulty, count in plan:
        for _ in range(count):
            result = generate_latin_square_puzzle(difficulty, rng)
            if result is None:
                print(f"Failed to generate a question for difficulty={difficulty}")
                continue
            revealed_grid, target, answer, depth = result
            questions_data.append((idx, difficulty, depth, revealed_grid, target, answer))
            idx += 1
    return questions_data


def main():
    import sys

    rng = random.Random()  # no seed -> fresh set every run
    questions_data = generate_batch(rng)

    print("=" * 60)
    print("dMAT-STYLE LATIN SQUARES — PRACTICE SET")
    print("=" * 60)
    print()

    for idx, difficulty, depth, revealed_grid, target, answer in questions_data:
        print(f"Question {idx} — Difficulty: {difficulty} (solve depth: {depth})")
        print(format_grid(revealed_grid, target))
        print()

    print("=" * 60)
    print("ANSWER KEY")
    print("=" * 60)
    for idx, difficulty, depth, revealed_grid, target, answer in questions_data:
        print(f"Question {idx}: {answer}  (solved at deduction step {depth})")

    output_path = sys.argv[1] if len(sys.argv) > 1 else "dmat_latin_squares_practice.pdf"
    export_to_pdf(questions_data, output_path)
    print()
    print(f"PDF written to: {output_path}")


if __name__ == "__main__":
    main()