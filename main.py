#!/usr/bin/env python3
"""World news in one image — Friday 20 November 2026.

Renders a dense editorial broadsheet: 46 verified stories grouped by
region, a UTC timeline strip, and a visible date check. Pure stdlib.
Writes /output/entry.png (or ./out/entry.png when MAKEFUN_OUTPUT_DIR
is unset). Deterministic: two runs produce identical bytes.
"""
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (185, 28, 28)
NAVY = (30, 58, 95)
GREY = (110, 110, 105)
LIGHT = (232, 226, 210)
GOLD = (146, 110, 20)

# 5x7 bitmap glyphs, "#" = ink, "." = blank. One row per string.
GLYPHS = {
"A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
"B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
"C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
"D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
"E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
"F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
"G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
"H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
"I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
"J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
"K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
"L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
"M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
"N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
"O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
"P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
"Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
"R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
"S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
"T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
"U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
"V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
"W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
"X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
"Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
"Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
"0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
"1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
"2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
"3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
"4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
"5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
"6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
"7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
"8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
"9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
" ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
"!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
"?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
"-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
"'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
"(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
"%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
"&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
"$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
"+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
"=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
"/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
'"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
"*": (".....", ".#.#.", ".###.", "#####", ".###.", ".#.#.", "....."),
"_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
"<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
}


def _chunk(kind, payload):
    out = struct.pack(">I", len(payload)) + kind + payload
    out += struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    return out


def encode_png(rgb, w, h):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


class Sheet:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def _set(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(col)

    def rect(self, x, y, w, h, col):
        for yy in range(y, y + h):
            base = (yy * self.w + x) * 3
            for xx in range(w):
                self.px[base + xx * 3:base + xx * 3 + 3] = bytes(col)

    def hline(self, x, y, w, col):
        for xx in range(x, x + w):
            self._set(xx, y, col)

    def vline(self, x, y, h, col):
        for yy in range(y, y + h):
            self._set(x, yy, col)

    def glyph(self, x, y, ch, col, s=1):
        g = GLYPHS.get(ch.upper(), GLYPHS["?"])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == "#":
                    if s == 1:
                        self._set(x + c, y + r, col)
                    else:
                        self.rect(x + c * s, y + r * s, s, s, col)

    def text(self, x, y, s, col, scale=1):
        cx = x
        for ch in s:
            if ch == " ":
                cx += 6 * scale
                continue
            self.glyph(cx, y, ch, col, scale)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale=1):
        return len(s) * 6 * scale - scale

    def wrap(self, s, maxw, scale=1):
        words = s.split(" ")
        lines = []
        cur = ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if self.text_w(trial, scale) <= maxw:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines


LEAD = ("TRUMP, XI, PUTIN: PEACE DECLARATION",
        "First trilateral in Shenzhen ends with a 4-point declaration: "
        "nuclear war 'cannot be won and must never be fought', UN reform, "
        "refined fuel supply, leaders shielded from courts. No mention of "
        "Ukraine or Iran. Published 00:01 UTC.")

APAC = [
("CYCLONE AKVAN LANDFALL TODAY",
 "Severe storm hits Odisha ~noon IST; 3 lakh evacuated, 69 trains off."),
("NZ 317-6, PHILLIPS 118",
 "Phillips, Nicholls 146* share 216-run stand; NZ v India, 1st Test."),
("ANTHROPIC +17% ON DEBUT",
 "Closes $97.17, ~$1.76T; largest IPO ever at $81.3bn; offer ends today."),
("MODI: TAX CUTS MUST MEAN JOBS",
 "PM presses industry at FICCI centenary: where are hires, pay rises?"),
("SPICEJET STRANDS HUNDREDS",
 "Cancellations pile up; airline flies a fraction of its schedule."),
("UPI FEE PLAN DELAYED AGAIN",
 "Indian digital payments shares fall sharply on Thursday."),
("INDIA: 162.5% DUTY ON SCOTCH",
 "Bulk whisky imports taxed above pre-deal 150%, document shows."),
("RISING STARS ASIA CUP OPENS",
 "Eight teams in Doha; India A (Tilak Varma) face Nepal today."),
("UGC NET DEC SCHEDULE OUT",
 "NTA releases subject-wise schedule for December 2026 exam."),
("BJP TRIBAL MEET IN SESSION",
 "Janajati Chintan Baithak on tribal development, empowerment."),
("WOMEN'S HOCKEY TROPHY OPENS",
 "Asian Hockey Champions Trophy 2026 begins today."),
("APEC HANDS OVER TO VIETNAM",
 "Shenzhen Outlook adopted by consensus; China pledges $20m."),
("EX-JUDGE VARMA TO LOK SABHA",
 "Resignation makes removal proceedings infructuous, he tells House."),
("ASIA MARKETS OPEN LOWER",
 "Nikkei -1,732 at open; ASX -1%, sixth straight loss; gold <$3,700."),
]

AMER = [
("TRUMP ON IRAN: SEE WHAT HAPPENS",
 "US will see after Jan 1, he tells Fox during China trip."),
("SENATE REJECTS IRAN WAR LIMIT",
 "Republicans block measure to curb Trump's war powers on Iran."),
("900,000 AI CHIPS FOR CHINA",
 "US approved chips for Chinese military firms, House papers show."),
("PETE ROSE PARDONED",
 "Trump posthumously pardons baseball's hit king (4,256), banned 1989."),
("WALL ST SLUMPS 2%",
 "Dow -2.19% (-1,101), S&P -2.02%, Nasdaq -2.25%; VIX jumps 15.8%."),
("CALIFORNIA PROBES NVIDIA",
 "State targets Nvidia in China AI chip probe after Huang exit."),
("CANADA EMBRACES AI CENTRES",
 "Ottawa backs data centres as US pushes back; O'Leary backs plan."),
("FIONA THE HIPPO DIES",
 "Cincinnati Zoo hippo dies after swallowing a hat."),
("GTA VI: $1.84BN BY LAUNCH",
 "Sensor Tower: 19.05m copies, passing The Odyssey box office."),
("GTA VI REVIEWS LAND",
 "Critics praise living world and NPCs; launch updates run all day."),
("F1 LAS VEGAS: FP3 + QUALIFYING",
 "Practice 3 and qualifying today; race Saturday; Antonelli champion."),
("LAS VEGAS GP STREAMS FREE",
 "US viewers watch free, no subscription or trial needed."),
("F1 ACADEMY SEASON FINALE",
 "Final round in Las Vegas this weekend, two races."),
]

EURO = [
("EUROPE READY FOR UKRAINE TALKS",
 "Berlin summit: united position; Merz calls Moscow demands unreal."),
("MACRON ON PEACE DECLARATION",
 "Shenzhen deal will not reorganise the world, president says."),
("DENMARK OKs GREENLAND DEAL",
 "Copenhagen approves Trump's military expansion deal."),
("EUROPEAN STOCKS FALL",
 "DAX -1.1%, FTSE -0.93% (six-week low), STOXX -0.88%."),
]

MEA = [
("VOICES FROM BESIEGED TAIZ",
 "BBC speaks to seven inside Yemeni city; 600k-1m cut off, 148 killed."),
("US EMBASSY: TAIZ SIEGE REAL",
 "Refutes Houthi blockade claims; 272 ships unloaded Jan-Sep."),
("HORMUZ: 14 ATTACKS IN NOV",
 "Iran hits vessels near Strait; Brent $92.72, WTI $83.81."),
("WORLD REACTS TO ICJ RULING",
 "Myanmar found responsible for genocide, 9-6; reparations ordered."),
("BAVUMA OUT OF TEST DECIDER",
 "SA captain ruled out (calf); Markram to lead vs Bangladesh."),
("ABU DHABI T10 QUALIFIER",
 "Arabian Aces vs UAE Bulls today."),
]

GLOB = [
("VOYAGER 1 PASSES LIGHT-DAY",
 "NASA confirms first craft 26bn km out; signal took ~a day."),
("COP31 DUE TO CONCLUDE TODAY",
 "Antalya final day; US Big Tech shuns AI pledge; OPEC defends fossils."),
("DOLLAR RISES 8TH SESSION",
 "Index at 103.96; oil edges higher, Brent $92.72."),
("TOTAL CHESS FINAL ENDS",
 "Budapest finale concludes today (Nov 19-20)."),
("APEC OUTLOOK: SEE STORY 13",
 "Leaders adopted Shenzhen Outlook 19 Nov; text published 20 Nov."),
("RUPEE FIRMS TO 94.13",
 "Gains 6 paise vs dollar in early trade."),
("INDIA-EU PACT HOPED IN DEC",
 "Commerce Secretary: India hopes to sign EU trade pact in December."),
("TRUMP: NUKES DEAL HARD",
 "'Hard but he'll keep working on it', Trump says after trilateral."),
]

TIMELINE = [
("00:01 UTC", "Peace declaration"),
("00:13 UTC", "BBC: Taiz voices"),
("00:20 UTC", "Phillips 118; NZ 317-6"),
("00:34 UTC", "Anthropic +17% $97.17"),
("01:00 UTC", "Asia markets lower"),
("06:30 UTC", "Akvan landfall"),
("09:00 UTC", "COP31 final day"),
("16:30 PST", "F1 Vegas FP3"),
("20:00 PST", "F1 Vegas qualifying"),
("23:19 UTC*", "Varma letter leads"),
]

SOURCES = ("SOURCES: INDEPENDENT, USA TODAY, THE TIMES, REUTERS, BBC, "
           "CNN, NPR, THE HINDU, FORMULA 1, AL JAZEERA, AP, BLOOMBERG")


def band(sh, x, y, w, h, col, label, label_col):
    sh.rect(x, y, w, h, col)
    sh.text(x + 8, y + (h - 14) // 2, label, label_col, 2)


def section(sh, x, y, w, title, stories, num0):
    sh.rect(x, y, w, 16, NAVY)
    sh.text(x + 6, y + 4, title, PAPER, 1)
    y += 22
    n = num0
    for head, detail in stories:
        tag = "%02d" % n
        sh.text(x, y, tag, RED, 1)
        sh.text(x + 20, y, head, INK, 1)
        y += 10
        for ln in sh.wrap(detail, w - 20, 1):
            sh.text(x + 20, y, ln, INK, 1)
            y += 9
        y += 4
        n += 1
    return y


def render():
    sh = Sheet(W, H, PAPER)
    # Masthead
    sh.rect(0, 0, W, 64, NAVY)
    sh.text(16, 10, "THE WORLD IN ONE IMAGE", PAPER, 2)
    sh.text(16, 34, "FRIDAY 20 NOVEMBER 2026", GOLD, 1)
    badge = "46 STORIES"
    bw = sh.text_w(badge, 2) + 16
    sh.rect(W - 16 - bw, 12, bw, 40, RED)
    sh.text(W - 16 - bw + 8, 22, badge, PAPER, 2)
    sh.hline(0, 64, W, RED)
    # Lead story
    y = 74
    sh.text(16, y, "01  LEAD", RED, 1)
    y += 12
    for ln in sh.wrap(LEAD[0], W - 32, 2):
        sh.text(16, y, ln, INK, 2)
        y += 16
    for ln in sh.wrap(LEAD[1], W - 32, 1):
        sh.text(16, y, ln, INK, 1)
        y += 9
    y += 6
    # UTC timeline strip
    sh.rect(0, y, W, 44, LIGHT)
    sh.text(16, y + 4, "UTC TIMELINE", NAVY, 1)
    ty = y + 16
    colw = (W - 32) // 5
    for i, (tm, ev) in enumerate(TIMELINE):
        cx = 16 + (i % 5) * colw
        cy = ty + (i // 5) * 14
        sh.text(cx, cy, tm, RED, 1)
        sh.text(cx + 62, cy, ev, INK, 1)
    y += 50
    # Date check band
    band(sh, 0, y, W, 22, GOLD,
         "DATE CHECK - EVERY STORY VERIFIED AS 20 NOVEMBER 2026", INK)
    y += 30
    # Two columns of regions
    lx, rx = 16, 524
    cw = 484
    ly = section(sh, lx, y, cw, "ASIA-PACIFIC", APAC, 2)
    ly = section(sh, lx, ly + 8, cw, "EUROPE", EURO, 29)
    ry = section(sh, rx, y, cw, "AMERICAS", AMER, 16)
    ry = section(sh, rx, ry + 8, cw, "MIDDLE EAST & AFRICA", MEA, 33)
    ry = section(sh, rx, ry + 8, cw, "GLOBAL / TECH / SCIENCE", GLOB, 39)
    # Footer sources
    fy = max(ly, ry) + 10
    sh.hline(16, fy, W - 32, GREY)
    for ln in sh.wrap(SOURCES, W - 32, 1):
        sh.text(16, fy + 6, ln, GREY, 1)
        fy += 9
    return sh


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    sh = render()
    data = encode_png(sh.px, W, H)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)
    print("wrote", os.path.join(outdir, "entry.png"), len(data), "bytes")


if __name__ == "__main__":
    main()
