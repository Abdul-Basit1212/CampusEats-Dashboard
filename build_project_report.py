from __future__ import annotations

from pathlib import Path
from textwrap import wrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"c:\Users\dondo\Documents\VS Code\Campus Eats App")
SCREENSHOTS = ROOT / "Screenshots"
OUTPUT_PDF = ROOT / "CampusEats_Project_Report.pdf"

PAGE_W = 1754
PAGE_H = 1240
MARGIN = 70
GAP = 34
SIDEBAR_W = 650
HEADER_H = 118
FOOTER_H = 54

ORANGE = (255, 107, 53)
SLATE = (1, 22, 39)
TEXT = (33, 37, 41)
MUTED = (104, 112, 122)
BORDER = (224, 228, 233)
PANEL = (247, 249, 251)
ACCENT = (235, 245, 255)
WHITE = (255, 255, 255)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend([
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
        ])
    else:
        candidates.extend([
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
        ])
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()

FONT_TITLE = load_font(52, bold=True)
FONT_SECTION = load_font(28, bold=True)
FONT_BODY = load_font(22, bold=False)
FONT_BODY_BOLD = load_font(22, bold=True)
FONT_SMALL = load_font(18, bold=False)
FONT_SMALL_BOLD = load_font(18, bold=True)
FONT_TINY = load_font(15, bold=False)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        current = ""
        for word in paragraph.split():
            trial = f"{current} {word}".strip()
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], font, fill, max_width: int, line_gap: int = 8) -> int:
    x, y = xy
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += draw.textbbox((x, y), line, font=font)[3] - draw.textbbox((x, y), line, font=font)[1] + line_gap
    return y


def draw_bullets(draw: ImageDraw.ImageDraw, bullets: list[str], xy: tuple[int, int], max_width: int) -> int:
    x, y = xy
    for bullet in bullets:
        prefix = "• "
        bullet_lines = wrap_text(draw, bullet, FONT_BODY, max_width - 34)
        if not bullet_lines:
            continue
        draw.text((x, y), prefix, font=FONT_BODY_BOLD, fill=ORANGE)
        draw.text((x + 30, y), bullet_lines[0], font=FONT_BODY, fill=TEXT)
        line_height = draw.textbbox((0, 0), bullet_lines[0], font=FONT_BODY)[3] - draw.textbbox((0, 0), bullet_lines[0], font=FONT_BODY)[1]
        y += line_height + 10
        for cont in bullet_lines[1:]:
            draw.text((x + 30, y), cont, font=FONT_BODY, fill=TEXT)
            line_height = draw.textbbox((0, 0), cont, font=FONT_BODY)[3] - draw.textbbox((0, 0), cont, font=FONT_BODY)[1]
            y += line_height + 8
        y += 4
    return y


def fit_image(image_path: Path, max_w: int, max_h: int) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    ratio = min(max_w / image.width, max_h / image.height)
    new_size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def create_page(title: str, subtitle: str, bullets: list[str], screenshot_name: str | None = None, footer: str = "") -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), WHITE)
    draw = ImageDraw.Draw(page)

    draw.rectangle((0, 0, PAGE_W, 18), fill=ORANGE)
    draw.rectangle((0, PAGE_H - FOOTER_H, PAGE_W, PAGE_H), fill=PANEL)
    draw.line((MARGIN, HEADER_H + 6, PAGE_W - MARGIN, HEADER_H + 6), fill=BORDER, width=2)

    draw.text((MARGIN, 34), title, font=FONT_TITLE, fill=SLATE)
    subtitle_y = draw_wrapped(draw, subtitle, (MARGIN, 94), FONT_SMALL, MUTED, PAGE_W - 2 * MARGIN)

    content_top = max(HEADER_H + 24, subtitle_y + 26)

    if screenshot_name:
        screenshot_path = SCREENSHOTS / screenshot_name
        if screenshot_path.exists():
            image_area_x = MARGIN + SIDEBAR_W + GAP
            image_area_y = content_top
            image_area_w = PAGE_W - image_area_x - MARGIN
            image_area_h = PAGE_H - image_area_y - FOOTER_H - MARGIN
            shot = fit_image(screenshot_path, image_area_w, image_area_h)
            # Center in its box
            x = image_area_x + max(0, (image_area_w - shot.width) // 2)
            y = image_area_y + max(0, (image_area_h - shot.height) // 2)
            page.paste(shot, (x, y))
            draw.rounded_rectangle((image_area_x - 10, image_area_y - 10, image_area_x + image_area_w + 10, image_area_y + image_area_h + 10), radius=18, outline=BORDER, width=2)
        else:
            draw.text((MARGIN + SIDEBAR_W + GAP, content_top), f"Missing screenshot: {screenshot_name}", font=FONT_BODY, fill=ORANGE)

    # Text panel on the left
    panel_x = MARGIN
    panel_y = content_top
    panel_w = SIDEBAR_W
    panel_h = PAGE_H - panel_y - FOOTER_H - MARGIN
    draw.rounded_rectangle((panel_x, panel_y, panel_x + panel_w, panel_y + panel_h), radius=20, fill=PANEL, outline=BORDER, width=2)

    text_x = panel_x + 22
    y = panel_y + 18
    y = draw_wrapped(draw, "What this page shows", (text_x, y), FONT_SECTION, SLATE, panel_w - 44)
    y += 8
    y = draw_bullets(draw, bullets, (text_x, y), panel_w - 44)

    if footer:
        draw.text((MARGIN, PAGE_H - FOOTER_H + 16), footer, font=FONT_TINY, fill=MUTED)
    else:
        draw.text((MARGIN, PAGE_H - FOOTER_H + 16), "CampusEats Project Report", font=FONT_TINY, fill=MUTED)
    draw.text((PAGE_W - MARGIN - 250, PAGE_H - FOOTER_H + 16), "Generated from the live Streamlit app", font=FONT_TINY, fill=MUTED)
    return page


pages: list[Image.Image] = []

cover = Image.new("RGB", (PAGE_W, PAGE_H), WHITE)
draw = ImageDraw.Draw(cover)
draw.rectangle((0, 0, PAGE_W, 18), fill=ORANGE)
draw.text((MARGIN, 62), "CampusEats Dashboard Project Report", font=FONT_TITLE, fill=SLATE)
draw.text((MARGIN, 136), "A detailed, screenshot-backed overview of the full multi-role business intelligence platform.", font=FONT_SMALL, fill=MUTED)
draw.rounded_rectangle((MARGIN, 208, PAGE_W - MARGIN, 520), radius=24, fill=PANEL, outline=BORDER, width=2)
cover_lines = [
    "This project combines Streamlit dashboards, SQLAlchemy-backed data access, SQLite persistence, role-based authentication, and ML/AI features for campus food operations.",
    "It includes a global command center, campus-level operations dashboard, stall-level analytics, a RandomForest-based sales forecaster, and a Gemini-powered business advisor.",
    "The screenshots in this report were taken from the live app running inside the project venv, and they are saved in the Screenshots folder.",
]
y = 246
for line in cover_lines:
    y = draw_wrapped(draw, line, (MARGIN + 28, y), FONT_BODY, TEXT, PAGE_W - 2 * MARGIN - 60) + 18

draw.text((MARGIN + 28, 556), "Core stack", font=FONT_SECTION, fill=SLATE)
stack_items = [
    "Streamlit UI and navigation",
    "SQLite database via SQLAlchemy",
    "Plotly and Folium visualizations",
    "Pandas / NumPy data processing",
    "scikit-learn forecasting",
    "Google Gemini chat assistant",
]
col_x = MARGIN + 28
col_y = 606
for item in stack_items:
    draw.text((col_x, col_y), f"• {item}", font=FONT_BODY, fill=TEXT)
    col_y += 40

draw.text((MARGIN, PAGE_H - FOOTER_H + 16), "CampusEats Project Report", font=FONT_TINY, fill=MUTED)
draw.text((PAGE_W - MARGIN - 260, PAGE_H - FOOTER_H + 16), "Generated from the live Streamlit app", font=FONT_TINY, fill=MUTED)
pages.append(cover)

pages.append(create_page(
    "Authentication & Data Layer",
    "The app starts at Home.py with a two-step role login flow. It loads environment variables, authenticates against the database, and keeps cached query helpers in database.py.",
    [
        "Three-role login gateway: Global Admin, Campus Incharge, and Stall Owner.",
        "Demo mode accepts placeholder hashes, which is why the live screenshot can be reproduced without secrets.",
        "Session state stores user role, campus ID, entity ID, and display name for route control.",
        "SQLAlchemy provides the database engine; cached fetch helpers reduce repeated reads and keep reruns responsive.",
        "The project uses the attached SQLite file, so the dashboards render real figures instead of mock placeholders.",
    ],
    screenshot_name="00_home.png",
    footer="Authentication gateway and project data layer"
))

pages.append(create_page(
    "Global Admin Dashboard",
    "This page is the platform-wide command center. It summarizes overall revenue, active students, wallet top-ups, and the broader platform economy.",
    [
        "Platform KPIs for revenue, active students, average order value, and wallet top-ups.",
        "30-day revenue trend with a 7-day rolling average overlay.",
        "Hourly order and revenue pattern analysis.",
        "Order type, payment method, top stalls, and popular items breakdowns.",
        "Campus revenue map and table-style drilldowns for platform-wide management.",
    ],
    screenshot_name="01_global_admin.png",
    footer="Global admin overview, trend analysis, and platform benchmarking"
))

pages.append(create_page(
    "Campus HQ Dashboard",
    "Campus Incharge users get a campus-scoped operations view, with admin users able to switch campuses from the sidebar selector.",
    [
        "Today’s revenue, today’s orders, active stalls, and available riders.",
        "Campus-specific 30-day revenue trend and category/payment breakdowns.",
        "Peak order hours chart for staffing and dispatch planning.",
        "Delivery partner performance and top student spender tables.",
        "Live campus map, stall markers, and rider markers with location context.",
        "A stall leaderboard plus an intervention center for cancellations and low ratings.",
    ],
    screenshot_name="02_campus_hq.png",
    footer="Campus operations, intervention monitoring, riders, and maps"
))

pages.append(create_page(
    "Stall Dashboard",
    "The stall owner dashboard focuses on unit economics, menu performance, customer feedback, and item-level conversion problems.",
    [
        "Financial analytics for today’s subtotal, GST, tips, net today, all-time revenue, and completed orders.",
        "Rush-hour heatmap showing demand by hour and day of week.",
        "Menu intelligence with top-selling items and category revenue share.",
        "Dead weight report highlighting items frequently added to carts but rarely completed.",
        "Customer feedback section with rating distribution and review filtering.",
    ],
    screenshot_name="03_stall_dashboard.png",
    footer="Stall-level revenue, menu intelligence, and customer sentiment"
))

pages.append(create_page(
    "AI Forecaster",
    "This module uses a RandomForestRegressor trained on historical orders to predict demand and recommend operational preparation for a specific day and hour.",
    [
        "Prediction inputs include day of week, month, and a cumulative day counter.",
        "The page outputs predicted orders per hour, average revenue per order, and estimated hourly revenue.",
        "Top items likely to sell are inferred from historical hourly patterns.",
        "A 7-day forecast bar chart and historical daily-order chart show trend direction.",
        "Feature importances help explain what the model is using internally.",
    ],
    screenshot_name="05_ai_forecaster.png",
    footer="Machine-learning forecasting and demand planning"
))

pages.append(create_page(
    "AI Business Advisor",
    "The advisor page gathers 14 days of financial context, reviews, competitor benchmarks, and stall metadata before sending the prompt to Gemini.",
    [
        "The advisor collects daily metrics, review summaries, and same-category competitors for context.",
        "Starter prompts help the user ask about revenue drops, busiest days, cancellations, and promotions.",
        "Response caching reduces repeated API calls within the same session.",
        "The code includes explicit handling for quota, API key, model-not-found, and safety-filter failures.",
        "This turns the dashboard into an explainable decision-support tool instead of a static reporting screen.",
    ],
    screenshot_name="04_ai_advisor.png",
    footer="Gemini-powered business advice, context preview, and chat UI"
))

# Optional final summary page to ensure extra depth
summary = Image.new("RGB", (PAGE_W, PAGE_H), WHITE)
draw = ImageDraw.Draw(summary)
draw.rectangle((0, 0, PAGE_W, 18), fill=ORANGE)
draw.text((MARGIN, 62), "Project Notes & Validation", font=FONT_TITLE, fill=SLATE)
draw.rounded_rectangle((MARGIN, 206, PAGE_W - MARGIN, 980), radius=24, fill=PANEL, outline=BORDER, width=2)
summary_text = [
    "The live app uses the project venv and the existing CampusEats.db database file.",
    "All screenshots were saved to the Screenshots folder and embedded into this report.",
    "The code base is organized around Home.py, database.py, and four role-driven pages under pages/.",
    "The dashboards emphasize real KPIs, campus operations, stall economics, forecasting, and AI-assisted analysis.",
    "The report was generated to be readable standalone, with enough detail to explain both what the app does and how the major views fit together.",
]
y = 250
y = draw_wrapped(draw, "Validation summary", (MARGIN + 28, y), FONT_SECTION, SLATE, PAGE_W - 2 * MARGIN - 56) + 14
for item in summary_text:
    y = draw_wrapped(draw, f"• {item}", (MARGIN + 28, y), FONT_BODY, TEXT, PAGE_W - 2 * MARGIN - 56) + 8

draw.text((MARGIN + 28, 770), "Key files reviewed", font=FONT_SECTION, fill=SLATE)
key_files = [
    "Home.py",
    "database.py",
    "pages/1_Global_Admin.py",
    "pages/2_Campus_HQ.py",
    "pages/3_Stall_Dashboard.py",
    "pages/4_AI_Forecaster_Advisor.py",
]
ky = 826
for item in key_files:
    draw.text((MARGIN + 40, ky), f"• {item}", font=FONT_BODY, fill=TEXT)
    ky += 34

draw.text((MARGIN, PAGE_H - FOOTER_H + 16), "CampusEats Project Report", font=FONT_TINY, fill=MUTED)
draw.text((PAGE_W - MARGIN - 250, PAGE_H - FOOTER_H + 16), "Generated from the live Streamlit app", font=FONT_TINY, fill=MUTED)
pages.append(summary)

rgb_pages = [page.convert("RGB") for page in pages]
rgb_pages[0].save(
    OUTPUT_PDF,
    "PDF",
    save_all=True,
    append_images=rgb_pages[1:],
    resolution=150.0,
)

print(f"Created {OUTPUT_PDF}")
