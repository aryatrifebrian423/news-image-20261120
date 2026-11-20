#!/usr/bin/env python3
"""Entry program for news-image-20261120 (make.fun).

Draws a one-page editorial poster summing up the world news of
Friday 20 November 2026: 46 verified stories grouped by region,
a lead banner on the Trump-Xi-Putin peace declaration, a UTC
timeline strip and a visible date check. Writes the image to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Pure Python 3 standard library: a row-slice pixel canvas, a small
5x7 bitmap font defined below, flat pictograms, and a zlib/struct
PNG encoder. No network, no clock, no randomness: every run writes
the same bytes.
"""
import os
import struct
import sys
import zlib
from pathlib import Path

W = H = 1024
PAPER = (246, 241, 230)
CARD = (255, 255, 255)
INK = (22, 22, 22)
NAVY = (26, 48, 84)
NAVY_DARK = (16, 32, 58)
RED = (176, 32, 26)
GOLD = (196, 156, 36)
GREY = (104, 102, 94)
FAINT = (238, 233, 219)
ROW_ALT = (241, 236, 224)
SKY = (150, 194, 218)
SEA = (56, 102, 146)
TEAL = (16, 126, 120)
GREEN = (44, 136, 62)
ORANGE = (212, 108, 30)
PURPLE = (92, 62, 138)

# ------------------------------------------------------------------ font --
# 5x7 bitmap font. Every glyph is 7 strings of 5 cells ("#" = ink).
# Text is rendered upper-case; lower-case input is upper-cased first.
# Chars covered: A-Z 0-9 space . , : ; ! ? ' " - ( ) / % $ + = & *
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00110", "00110", "00110", "00110", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10010", "01110", "01001", "11110", "00100"),
    "+": ("00000", "00100", "01110", "00100", "00000", "00000", "00000"),
    "=": ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "*": ("00000", "01010", "00100", "01110", "00100", "01010", "00000"),
}
BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


def text_width(s, scale):
    """Pixel width of s rendered at scale (6 px per char cell)."""
    return len(s) * 6 * scale


def clip(s, max_chars):
    """Hard clip; story copy is written to fit, this is a safety net."""
    return s if len(s) <= max_chars else s[:max_chars]


# ---------------------------------------------------------------- canvas --
class Canvas:
    """RGB pixel buffer with row-slice fills (fast, deterministic)."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def _row(self, y, x0, x1, color):
        if y < 0 or y >= self.h:
            return
        x0 = max(x0, 0)
        x1 = min(x1, self.w)
        if x1 <= x0:
            return
        i = (y * self.w + x0) * 3
        self.px[i:i + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            self._row(yy, x, x + w, color)

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def hline(self, x, y, length, color, t=1):
        self.rect(x, y, length, t, color)

    def vline(self, x, y, length, color, t=1):
        self.rect(x, y, t, length, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.rect(x - t // 2, y - t // 2, t, t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            half = int((r * r - (yy - cy) ** 2) ** 0.5)
            self._row(yy, cx - half, cx + half + 1, color)

    def ring(self, cx, cy, r, color, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= r * r:
                    self.set(xx, yy, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            dx = int(rx * (1 - ((yy - cy) / ry) ** 2) ** 0.5)
            self._row(yy, cx - dx, cx + dx + 1, color)

    def dot_grid(self, x0, y0, x1, y1, step, color):
        for yy in range(y0, y1, step):
            for xx in range(x0, x1, step):
                self.set(xx, yy, color)

    def text(self, x, y, s, color, scale):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, BLANK)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def text_centre(self, cx, y, s, color, scale):
        self.text(cx - text_width(s, scale) // 2, y, s, color, scale)


def png_bytes(canvas):
    """Encode the canvas as a PNG (filter 0 rows, zlib level 9)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# ------------------------------------------------------------- pictograms --
def draw_three_flags(cv, x, y):
    """US, China and Russia flags side by side (lead pictogram)."""
    fw, fh = 46, 30
    # US: stripes + blue canton with four stars.
    for i in range(5):
        cv.rect(x, y + i * 6, fw, 6, RED if i % 2 == 0 else CARD)
    cv.rect(x, y, 20, 18, NAVY)
    for dx, dy in ((5, 4), (14, 4), (5, 11), (14, 11)):
        cv.disc(x + dx, y + dy, 2, CARD)
    cv.frame(x, y, fw, fh, INK, 1)
    # China: red field, one big gold star, four small ones.
    cx = x + fw + 6
    cv.rect(cx, y, fw, fh, RED)
    cv.disc(cx + 11, y + 10, 5, GOLD)
    for dx, dy in ((25, 6), (31, 12), (25, 18), (19, 14)):
        cv.disc(cx + dx, y + dy, 2, GOLD)
    cv.frame(cx, y, fw, fh, INK, 1)
    # Russia: white, blue, red horizontal bands.
    rx = x + 2 * (fw + 6)
    cv.rect(rx, y, fw, 10, CARD)
    cv.rect(rx, y + 10, fw, 10, SEA)
    cv.rect(rx, y + 20, fw, 10, RED)
    cv.frame(rx, y, fw, fh, INK, 1)


def draw_globe(cv, cx, cy, r):
    """Small wireframe globe for the numbers panel."""
    cv.ring(cx, cy, r, SEA, 3)
    cv.ellipse(cx, cy, r, int(r * 0.45), SEA)
    cv.ellipse(cx, cy, int(r * 0.45), r, SEA)
    cv.hline(cx - r, cy, 2 * r, SEA, 2)


# ------------------------------------------------------------------ data --
# 46 numbered stories, verified 20 Nov 2026. Story 43 was merged into
# story 13 (same APEC declaration), so it appears as a one-line pointer.
# Each item: (number, headline <= 35 chars, detail <= 74 chars or None).
ASIA = ("ASIA-PACIFIC", RED, [
    (2, "CYCLONE AKVAN HITS ODISHA",
     "Landfall at noon IST near Gopalpur; 3 lakh evacuated, 69 trains cancelled."),
    (3, "PHILLIPS 118 AS NZ REACH 317-6",
     "Day 2, 1st Test, Wellington; 216-run stand rescues NZ from 70-5."),
    (4, "ANTHROPIC SHARES SOAR ON DEBUT",
     "Closed $97.17, +17%; opened $111.50. Largest IPO ever at $81.3bn."),
    (5, "MODI TO INDUSTRY: WHERE ARE JOBS?",
     "'We cut tax, but where are the hires, salary hikes?' FICCI centenary."),
    (6, "SPICEJET CUTS STRAND PASSENGERS",
     "Hundreds stranded over past days; airline flies a fraction of schedule."),
    (7, "UPI FEE PLAN DELAYED AGAIN",
     "Indian digital payments shares fell sharply on Thursday."),
    (8, "INDIA DUTY ON SCOTCH WHISKY 162.5%",
     "Effective duty and tax on bulk imports, above 150% pre-trade deal."),
    (9, "RISING STARS ASIA CUP BEGINS",
     "Eight teams in Doha; India A open vs Nepal today, 20 Nov."),
    (10, "UGC NET DECEMBER SCHEDULE OUT",
     "NTA releases subject-wise schedule for December 2026 exam."),
    (11, "BJP HOLDS TRIBAL DEVELOPMENT MEET",
     "Janajati Chintan Baithak on tribal development and empowerment."),
    (12, "WOMEN'S ASIAN HOCKEY TROPHY OPENS",
     "Women's Asian Hockey Champions Trophy 2026 begins today."),
    (13, "APEC HANDS OVER TO VIETNAM FOR 2027",
     "Leaders adopted Shenzhen Outlook; text out 20 Nov. China pledges $20m."),
    (14, "EX-JUDGE VARMA FIGHTS REMOVAL CASE",
     "Says resignation ends removal case; letter leads the morning press."),
    (15, "ASIA MARKETS OPEN LOWER",
     "Nikkei down 1,732; ASX -1%, sixth straight loss; gold under $3,700."),
])
AMERICAS = ("AMERICAS", NAVY, [
    (16, "TRUMP ON IRAN: 'SEE WHAT HAPPENS'",
     "US will 'see what happens' after Jan 1, Trump tells Fox in China."),
    (17, "SENATE REJECTS IRAN WAR-POWERS CURB",
     "Republicans vote down measure to limit Trump's war powers on Iran."),
    (18, "900,000 AI CHIPS FOR CHINA MILITARY",
     "Approved chips for Chinese military firms, new House documents show."),
    (19, "TRUMP PARDONS PETE ROSE",
     "Posthumous pardon for hit king (4,256 hits), banned since 1989."),
    (20, "WALL STREET SLUMPS 2%",
     "Dow -2.19% (-1,101), S&P -2.02%, Nasdaq -2.25%; VIX jumps to 28.44."),
    (21, "CALIFORNIA PROBES NVIDIA OVER CHINA",
     "State targets Nvidia in China AI chip probe after Huang's departure."),
    (22, "CANADA EMBRACES AI DATA CENTRES",
     "Ottawa backs data centres while US pushes back; O'Leary among backers."),
    (23, "FIONA THE HIPPO DIES AT ZOO",
     "Cincinnati Zoo hippo dies after swallowing a hat, BBC reports."),
    (24, "GTA VI: $1.84BN BY LAUNCH DAY",
     "Sensor Tower: 19.05m copies, passing The Odyssey's $1.805bn box office."),
    (25, "GTA VI REVIEWS PRAISE LIVING WORLD",
     "Critics hail NPCs and world; launch live updates run through the day."),
    (26, "F1 LAS VEGAS: FP3 AND QUALIFYING",
     "Practice 3 and qualifying today; Antonelli already champion."),
    (27, "LAS VEGAS GP TO STREAM FREE IN US",
     "No subscription or trial needed, in a major broadcast change."),
    (28, "F1 ACADEMY CLOSES SEASON IN VEGAS",
     "Final round this weekend, two races to decide the title."),
])
EUROPE = ("EUROPE", TEAL, [
    (29, "EUROPE READY FOR UKRAINE TALKS",
     "Berlin summit: united position, Merz calls Moscow demands unrealistic."),
    (30, "MACRON DISMISSES PEACE DECLARATION",
     "Says Shenzhen declaration will not 'reorganise the world'."),
    (31, "DENMARK OKS GREENLAND MILITARY DEAL",
     "Copenhagen approves Trump's Greenland military expansion deal."),
    (32, "EUROPEAN STOCKS FALL",
     "DAX -1.1%, FTSE -0.93% at six-week low, STOXX 600 -0.88%."),
])
MEA = ("MIDDLE EAST & AFRICA", ORANGE, [
    (33, "VOICES FROM BESIEGED TAIZ",
     "'I tell my son it's just fireworks', BBC hears inside the city."),
    (34, "US EMBASSY: TAIZ SIEGE IS REAL",
     "Refutes Houthi blockade claims; 272 ships unloaded at Hodeidah Jan-Sep."),
    (35, "14 HORMUZ ATTACKS IN NOVEMBER",
     "UKMTO count via Bloomberg; Brent $92.72. IEA: largest energy shock ever."),
    (36, "WORLD REACTS TO ICJ MYANMAR RULING",
     "9-6 genocide verdict; Myanmar to pay reparations. Maldives welcomes it."),
    (37, "BAVUMA OUT OF BANGLADESH DECIDER",
     "Calf strain rules SA captain out; Markram to lead. SA top Test table."),
    (38, "ABU DHABI T10 QUALIFIER TODAY",
     "Arabian Aces vs UAE Bulls in today's qualifier."),
])
GLOBAL = ("GLOBAL / TECH / SCIENCE", PURPLE, [
    (39, "VOYAGER 1 PASSES ONE LIGHT-DAY",
     "NASA confirms 26bn km milestone; signal took about a day to reach Earth."),
    (40, "COP31 DUE TO CONCLUDE TODAY",
     "Final day in Antalya; US Big Tech shuns AI pledge, only Alibaba signed."),
    (41, "DOLLAR RISES FOR 8TH SESSION",
     "Dollar index 103.96; oil edges higher, Brent $92.72, WTI $83.81."),
    (42, "TOTAL CHESS FINAL ENDS IN BUDAPEST",
     "Nov 19-20 final concludes today in Budapest."),
    (43, "MERGED INTO 13 ABOVE - APEC OUTLOOK", None),
    (44, "RUPEE FIRMS TO 94.13 VS DOLLAR",
     "Rupee up 6 paise in early trade on Friday, 20 Nov."),
    (45, "INDIA EYES EU TRADE PACT IN DECEMBER",
     "Commerce Secretary Agrawal tells ANI a deal is hoped for in December."),
    (46, "TRUMP: NUCLEAR DEAL 'WILL BE HARD'",
     "'He'll keep working on it', Trump says after the trilateral summit."),
])
# (time, one-line label) in time order. Times are UTC unless noted.
TIMELINE = [
    ("00:01 UTC", "Peace declaration published"),
    ("00:13 UTC", "BBC: voices from Taiz"),
    ("00:20 UTC", "Phillips century; NZ 317-6"),
    ("00:34 UTC", "Anthropic closes +17%"),
    ("01:00 UTC", "Asia markets open lower"),
    ("06:30 UTC", "Cyclone Akvan landfall"),
    ("09:00 UTC", "COP31 final day, Antalya"),
    ("16:30 PST", "F1 Las Vegas: Practice 3"),
    ("20:00 PST", "F1 Las Vegas: qualifying"),
    ("23:19 UTC*", "Varma letter leads press"),
]
COL_W = 480
ITEM_H = 22


def draw_region_header(cv, x, y, name, color, count_label):
    cv.rect(x, y, COL_W, 20, color)
    cv.text(x + 10, y + 3, name, CARD, 2)
    w = text_width(count_label, 2)
    cv.text(x + COL_W - 10 - w, y + 3, count_label, CARD, 2)


def draw_item(cv, x, y, num, headline, detail, color, alt):
    if alt:
        cv.rect(x, y - 1, COL_W, ITEM_H, ROW_ALT)
    if detail is None:  # one-line pointer (story 43, merged into 13)
        cv.text(x, y + 2, "%02d" % num, color, 1)
        cv.text(x + 24, y + 2, headline, GREY, 1)
        return 12
    cv.text(x, y, "%02d" % num, color, 2)
    cv.text(x + 36, y, clip(headline, 35), INK, 2)
    cv.text(x + 36, y + 13, clip(detail, 74), GREY, 1)
    return ITEM_H


def draw_region(cv, x, y, region, start_alt=False):
    name, color, items = region
    draw_region_header(cv, x, y, name, color, "%d STORIES" % len(items))
    y += 20
    alt = start_alt
    for num, headline, detail in items:
        y += draw_item(cv, x, y, num, headline, detail, color, alt)
        alt = not alt
    return y


def draw_numbers_panel(cv, x, y, w, h):
    cv.rect(x, y, w, h, CARD)
    cv.frame(x, y, w, h, NAVY, 2)
    cv.rect(x + 2, y + 2, w - 4, 22, NAVY)
    cv.text(x + 12, y + 8, "BY THE NUMBERS", CARD, 2)
    draw_globe(cv, x + w - 34, y + 36, 20)
    rows = [("46 STORIES", "ACROSS 5 REGIONS"),
            ("10 MOMENTS", "ON THE UTC TIMELINE"),
            ("11 OUTLETS", "NAMED IN THE SOURCES LINE"),
            ("1 DAY", "FRIDAY 20 NOVEMBER 2026")]
    yy = y + 30
    for big, small in rows:
        cv.text(x + 12, yy, big, RED, 2)
        cv.text(x + 12 + text_width(big, 2) + 8, yy + 3, small, GREY, 1)
        yy += 20
    return y + h


def build_poster():
    cv = Canvas(W, H, PAPER)
    cv.dot_grid(16, 14, 1008, 1008, 16, FAINT)

    # Masthead.
    cv.rect(16, 14, 992, 86, NAVY)
    cv.rect(16, 14, 992, 6, GOLD)
    cv.text(36, 28, "THE WORLD IN ONE IMAGE", CARD, 3)
    cv.text(36, 60, "FRIDAY 20 NOVEMBER 2026", GOLD, 4)
    cv.vline(812, 22, 70, GOLD, 3)
    cv.text(848, 24, "46", CARD, 7)
    cv.text(848, 78, "STORIES", CARD, 2)

    # Sub-band: the count, the verification, the timeline, the date check.
    cv.hline(16, 106, 992, GOLD, 2)
    cv.text_centre(512, 110, "46 STORIES - VERIFIED - UTC TIMELINE - DATE CHECK",
                   NAVY, 2)
    cv.hline(16, 126, 992, GOLD, 2)

    # Lead banner: story 1, the Shenzhen peace declaration.
    cv.rect(16, 132, 992, 108, CARD)
    cv.frame(16, 132, 992, 108, NAVY, 2)
    cv.rect(18, 134, 988, 24, RED)
    cv.text(28, 141, "LEAD - THE SHENZHEN DECLARATION - PUBLISHED 00:01 UTC 20 NOV",
            CARD, 2)
    draw_three_flags(cv, 28, 168)
    cv.text(49, 204, "US - CHINA - RUSSIA", GREY, 1)
    cv.text(196, 162, "TRUMP, XI AND PUTIN DECLARE PEACE", INK, 3)
    cv.text(196, 190, "90-MINUTE TRILATERAL IN SHENZHEN; A 4-POINT PACT",
            INK, 2)
    cv.text(196, 207, "NUCLEAR WAR 'CANNOT BE WON AND MUST NEVER BE FOUGHT'",
            INK, 2)
    cv.text(196, 224, "UN REFORM, MORE FUEL SUPPLY; NO MENTION OF UKRAINE OR IRAN",
            INK, 2)

    # Story columns: A = Asia-Pacific + Middle East & Africa,
    # B = Americas + Europe + Global / Tech / Science.
    draw_region(cv, 16, 246, ASIA)
    draw_region(cv, 16, 578, MEA)
    draw_region(cv, 528, 246, AMERICAS)
    draw_region(cv, 528, 556, EUROPE)
    draw_region(cv, 528, 668, GLOBAL)
    draw_numbers_panel(cv, 16, 738, COL_W, 114)

    # UTC timeline strip: two rows of five moments.
    cv.rect(16, 872, 992, 82, CARD)
    cv.frame(16, 872, 992, 82, NAVY, 2)
    cv.text(28, 879, "UTC TIMELINE - 20 NOVEMBER 2026 - TIMES UTC UNLESS NOTED - *19 NOV OVERNIGHT",
            NAVY, 2)
    cv.hline(28, 897, 968, GOLD, 2)
    for i, (when, label) in enumerate(TIMELINE):
        row = i // 5
        col = i % 5
        cx = 28 + col * 196
        ty = 901 + row * 28
        cv.text(cx, ty, when, RED, 2)
        cv.text(cx, ty + 14, label, INK, 1)

    # Footer: date check + sources.
    cv.text_centre(512, 962, "DATE CHECK - EVERY STORY VERIFIED AS 20 NOVEMBER 2026",
                   INK, 2)
    cv.text_centre(512, 984,
                   "SOURCES: REUTERS, BBC, AP, AFP, THE HINDU, INDIA TODAY, "
                   "NDTV, FORBES, SENSOR TOWER, IMD, NASA", GREY, 1)
    cv.hline(16, 1004, 992, GOLD, 2)
    return png_bytes(cv)


def main() -> int:
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"
    data = build_poster()
    target.write_bytes(data)
    print("wrote %s (%d bytes)" % (target, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
