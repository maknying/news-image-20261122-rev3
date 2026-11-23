#!/usr/bin/env python3
"""The World in One Page — 22 November 2026 (rev3).

A one-page newspaper front page drawn entirely by this program: 45
real, source-checked stories from Sunday 22 November 2026, grouped
into 7 regions, with a masthead, a lead story, four columns and a
day-in-numbers band.

Rev3 is a legibility rebuild. Compared with the previous revision:
headlines grow from 13px to 15px bold, summaries from 10px to 12px,
leading and story gaps open up, the copy is tightened so every story
fits in at most two headline lines and two summary lines, and the
columns are balanced by an exact partition instead of a greedy fill.
Every fact was re-checked against live reporting before this build.

Standard library only. All glyphs come from the pre-rendered atlas
(atlas.bin, built by build_atlas.py from DejaVu fonts), so the program
needs no network and no installed fonts. Run it twice and the PNG
bytes are identical.

Usage:  python3 main.py            # writes out/entry.png
        MAKEFUN_OUTPUT_DIR=/output python3 main.py
"""

import binascii
import hashlib
import math
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------- geometry
PAGE_W = 1024
PAGE_H = 1024
MARGIN = 36
CONTENT_W = PAGE_W - 2 * MARGIN     # 952
NCOLS = 4
COL_GAP = 14
COL_W = (CONTENT_W - (NCOLS - 1) * COL_GAP) // NCOLS   # 227
BODY_TOP = 240
BODY_BOTTOM = 982                   # 742 px of body

PAPER = (250, 247, 238)
INK = (18, 18, 18)
RED = (139, 26, 26)
RULE_FAINT = (150, 142, 126)

# Face ids match build_atlas.py.
F_MASTHEAD = 0   # serif bold 44
F_LEAD_HEAD = 1  # serif bold 30
F_LEAD_DECK = 2  # serif 14
F_HEAD = 3       # serif bold 15
F_SECTION = 4    # sans bold 12
F_SUMMARY = 5    # sans 12
F_FOOTER = 6     # sans 10
F_DATE = 7       # sans bold 11

HEAD_LEADING = 17
SUMMARY_LEADING = 16
STORY_GAP = 11
HEADER_H = 18

# ---------------------------------------------------------------- copy
MASTHEAD = "THE WORLD IN ONE PAGE"
DATELINE_L = "SUNDAY, 22 NOVEMBER 2026"
DATELINE_R = "45 STORIES \u2022 7 REGIONS"

LEAD = {
    "kicker": "LEAD \u2014 CLIMATE \u2022 ANTALYA",
    "headline": "COP31 collapses with no deal",
    "deck": ("The EU, Britain, Panama and others reject a final text that "
             "omits fossil fuels. President Murat Kurum concedes \u2018no "
             "agreement\u2019 as the Antalya talks run the longest in "
             "history."),
}

# Every story: short headline (<= ~50 chars, 2 lines at 15px) and a
# one- or two-line summary (<= ~72 chars, 2 lines at 12px). Facts were
# re-verified against live reporting on 23 Nov 2026; see SOURCES.md.
STORIES = [
    {"section": "MIDDLE EAST",
     "headline": "Iran hits US bases",
     "summary": "IRGC claims strikes on two US bases; Bahrain says defences held."},
    {"section": "MIDDLE EAST",
     "headline": "Tankers hit near Hormuz",
     "summary": "Two strikes on tankers near Khasab; a third hits a mine and burns."},
    {"section": "MIDDLE EAST",
     "headline": "Trump seeks Iran deal",
     "summary": "Trump wants a \u2018permanent\u2019 deal that outlasts his presidency."},
    {"section": "MIDDLE EAST",
     "headline": "Iran masses 14 tankers",
     "summary": "Over 14 tankers stage off Kharg Island to challenge a US blockade."},
    {"section": "MIDDLE EAST",
     "headline": "Eisenkot invites Likud",
     "summary": "In Israel\u2019s coalition talks, Eisenkot invites Netanyahu\u2019s Likud."},
    {"section": "EUROPE",
     "headline": "Missiles land in Poland",
     "summary": "Three Kh-101 missiles fall in the south-east; Tusk calls it provocation."},
    {"section": "EUROPE",
     "headline": "Finland: war \u2018spilling over\u2019",
     "summary": "Drones hit the Russian ship Sparta II; its crew of 16 is evacuated."},
    {"section": "EUROPE",
     "headline": "Estonia to shut border",
     "summary": "Estonia will close its border; Moscow decries a \u2018new Iron Curtain\u2019."},
    {"section": "EUROPE",
     "headline": "EU, Indonesia sign pact",
     "summary": "After ten years of talks, CEPA frees 98.5% of tariff lines."},
    {"section": "EUROPE",
     "headline": "Germany rallies allies",
     "summary": "Wadephul says the Berlin gathering sends Moscow a unified message."},
    {"section": "EUROPE",
     "headline": "Poland fires up Patriots",
     "summary": "Poland activates Patriot defences after Russian airspace violations."},
    {"section": "RUSSIA & UKRAINE",
     "headline": "Lviv strike kills 2",
     "summary": "A barrage hits Lviv; two killed, ten hurt; Kyiv cites 400+ drones."},
    {"section": "RUSSIA & UKRAINE",
     "headline": "UK\u2013Ukraine drone deal",
     "summary": "Kyiv and London agree joint production of strike drones in Britain."},
    {"section": "RUSSIA & UKRAINE",
     "headline": "109 bridge strikes",
     "summary": "Russia struck Ukrainian bridges 109 times, Zelenskyy says."},
    {"section": "RUSSIA & UKRAINE",
     "headline": "Bulgaria backs India plan",
     "summary": "Bulgaria backs India\u2019s ceasefire plan for the Black Sea and energy."},
    {"section": "RUSSIA & UKRAINE",
     "headline": "Crimean Bridge strain",
     "summary": "Moscow admits bridge transport is harder after three strikes in a week."},
    {"section": "THE AMERICAS",
     "headline": "\u2018El Chapo Isidro\u2019 captured",
     "summary": "Mexican forces seize a most-wanted cartel boss; 11 killed in the raid."},
    {"section": "THE AMERICAS",
     "headline": "Bolsonaro taken to ICU",
     "summary": "Ex-president Bolsonaro, under house arrest, is in intensive care."},
    {"section": "THE AMERICAS",
     "headline": "FBI probes database hack",
     "summary": "The FBI probes an apparent hack of its crime database; USDA also hit."},
    {"section": "THE AMERICAS",
     "headline": "Pentagon curbs Canada",
     "summary": "The Pentagon limits \u2018social activities\u2019 with Canada\u2019s military."},
    {"section": "THE AMERICAS",
     "headline": "Trilateral summit fallout",
     "summary": "After the Shenzhen trilateral, Trump again calls Putin a friend."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "Banten factory fire kills 3",
     "summary": "A candy factory fire in Banten kills three; 36 workers are missing."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "Twin volcanoes erupt",
     "summary": "Ibu and Semeru erupt hours apart, ash hundreds of metres high."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "Modi opens Nitish Setu",
     "summary": "Modi inaugurates Nitish Setu bridge linking Patna and Vaishali in Bihar."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "Quake hits Qinghai",
     "summary": "A 5.6 quake jolts Delingha City in Qinghai; depth 10 km."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "Hong Kong Election vote",
     "summary": "About 5,700 voters elect members of Hong Kong\u2019s Election Committee."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "India's record 629-6 in NZ",
     "summary": "Pant\u2019s century lifts India to 629-6 in Wellington, a record in New Zealand."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "Mastung raids kill 15",
     "summary": "Security forces kill 15 militants in two Mastung operations."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "China's second cruise ship",
     "summary": "Adora Flora City leaves Guangzhou on a six-day maiden voyage."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "Shenzhou-24 rehearsal",
     "summary": "Shenzhou-24 rehearsal done; it will carry the first Pakistani astronaut."},
    {"section": "ASIA\u2013PACIFIC",
     "headline": "China slams FCC ban",
     "summary": "Beijing opposes a US ban on China Mobile, Telecom and Unicom."},
    {"section": "MARKETS, TECH & SPORT",
     "headline": "Leapmotor profit dives",
     "summary": "Leapmotor Q3 profit falls 73% to 40m yuan despite record sales."},
    {"section": "MARKETS, TECH & SPORT",
     "headline": "Foreign cash floods tech",
     "summary": "Foreign investment in Chinese technology rises 31 percent."},
    {"section": "MARKETS, TECH & SPORT",
     "headline": "Huawei launches OSTA",
     "summary": "Huawei unveils AI phone brand OSTA, first handset at 5,499 yuan."},
    {"section": "MARKETS, TECH & SPORT",
     "headline": "Alibaba cloud outlook cut",
     "summary": "Alibaba cuts its cloud outlook amid export controls, its CEO says."},
    {"section": "MARKETS, TECH & SPORT",
     "headline": "Signal blocks screenshots",
     "summary": "Signal blocks screenshots, citing an \u2018existential threat\u2019 from AI."},
    {"section": "MARKETS, TECH & SPORT",
     "headline": "UN fails on \u2018killer robots\u2019",
     "summary": "The UN fails to agree rules on autonomous \u2018killer robot\u2019 weapons."},
    {"section": "MARKETS, TECH & SPORT",
     "headline": "Verstappen wins in Vegas",
     "summary": "Verstappen wins a wild Las Vegas GP by 0.6s after 35 lead changes."},
    {"section": "AFRICA & SCIENCE",
     "headline": "M6.8 quake off Timor",
     "summary": "A 6.8 quake hits 105 km north-east of Lospalos, the USGS says."},
    {"section": "AFRICA & SCIENCE",
     "headline": "Mlambo-Ngcuka dies at 71",
     "summary": "Ex-deputy president dies at 71 after a medical procedure."},
    {"section": "AFRICA & SCIENCE",
     "headline": "South Africa murders fall",
     "summary": "Murders fall by 204, but killings still average 60 a day."},
    {"section": "AFRICA & SCIENCE",
     "headline": "Senegal budget by decree",
     "summary": "Faye imposes the 2026 budget by decree after parliament rejects it."},
    {"section": "AFRICA & SCIENCE",
     "headline": "Egypt nears IMF payout",
     "summary": "Egypt reaches a staff-level IMF deal, unlocking about $2.3bn."},
    {"section": "AFRICA & SCIENCE",
     "headline": "Sodium cloud at Europa",
     "summary": "Keck astronomers trace the sodium cloud around Jupiter\u2019s moon Europa."},
]

NUMBERS = ("THE DAY IN NUMBERS \u2014 2 killed in Lviv \u2022 11 dead in "
           "Sinaloa \u2022 36 missing in Banten \u2022 35 lead changes in "
           "Vegas \u2022 $2.3bn for Egypt")

FOOTER_L = ("Sources: Reuters \u2022 AP \u2022 AFP \u2022 BBC \u2022 CNN "
            "\u2022 USGS \u2022 NYT \u2022 Euronews \u2022 Al Jazeera "
            "\u2022 Xinhua \u2022 ANTARA \u2022 FIA \u2022 Formula1.com")
FOOTER_R = "Compiled 22 Nov 2026 \u2022 No. 45"


# ---------------------------------------------------------------- atlas
# Binary layout written by build_atlas.py:
#   magic 8s, u32 face_count,
#   per face: u32 id, u32 size, u16 ascent, u16 descent, u32 glyphs,
#   per glyph: u32 face_id, u32 codepoint, i16 off_x, i16 off_y,
#              u16 advance, u16 w, u16 h, u32 data_off, u32 data_len,
#   pixel blob (8-bit grayscale).
_GLYPH_ROW = struct.Struct("<IhhHHHHII")
_FACE_ROW = struct.Struct("<IIHHI")


class GlyphAtlas(object):
    """Read-only view over an atlas.bin produced by build_atlas.py."""

    def __init__(self, path):
        with open(path, "rb") as fh:
            raw = fh.read()
        if raw[:8] != b"ATLS0001":
            raise ValueError("bad atlas magic")
        pos = 8
        (nfaces,) = struct.unpack_from("<I", raw, pos)
        pos += 4
        self.metrics = {}
        self.table = {}
        pending = []
        for _ in range(nfaces):
            fid, size, asc, desc, count = _FACE_ROW.unpack_from(raw, pos)
            pos += _FACE_ROW.size
            self.metrics[fid] = (size, asc, desc)
            pending.append(count)
        rows = []
        for count in pending:
            for _ in range(count):
                rows.append(_GLYPH_ROW.unpack_from(raw, pos))
                pos += _GLYPH_ROW.size
        blob = pos
        for fid, cp, ox, oy, adv, w, h, off, ln in rows:
            self.table[(fid, cp)] = (ox, oy, adv, w, h,
                                     raw[blob + off: blob + off + ln])

    def glyph_for(self, face, ch):
        found = self.table.get((face, ord(ch)))
        if found is None:
            found = self.table[(face, ord("?"))]
        return found

    def width(self, face, text):
        return sum(self.glyph_for(face, ch)[2] for ch in text)

    def line_height(self, face):
        _size, asc, desc = self.metrics[face]
        return asc + desc

    def wrap(self, face, text, max_w, limit):
        """Greedy word wrap capped at `limit` lines.

        Returns (lines, truncated): the last line gains an ellipsis
        when text is cut, and truncated reports whether that happened.
        """
        words = text.split(" ")
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if self.width(face, trial) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        cut = False
        if len(lines) > limit:
            cut = True
            lines = lines[:limit]
            last = lines[-1]
            while last and self.width(face, last + "\u2026") > max_w:
                last = last[:-1]
            lines[-1] = last + "\u2026"
        return lines, cut


# ---------------------------------------------------------------- canvas
class Sheet(object):
    """An RGB pixel buffer with tiny drawing primitives."""

    def __init__(self):
        self.buf = bytearray(PAPER * (PAGE_W * PAGE_H))

    def _px(self, x, y, color, alpha=255):
        if 0 <= x < PAGE_W and 0 <= y < PAGE_H:
            i = (y * PAGE_W + x) * 3
            if alpha >= 255:
                self.buf[i:i + 3] = bytes(color)
            elif alpha > 0:
                for c in range(3):
                    base = self.buf[i + c]
                    self.buf[i + c] = (color[c] * alpha +
                                       base * (255 - alpha)) // 255

    def fill(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(PAGE_W, x + w), min(PAGE_H, y + h)
        for yy in range(y0, y1):
            base = (yy * PAGE_W + x0) * 3
            self.buf[base:base + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def hrule(self, x, y, w, color, thick=1):
        self.fill(x, y, w, thick, color)

    def vrule(self, x, y, h, color, thick=1):
        self.fill(x, y, thick, h, color)

    def draw_text(self, atlas, x, y_top, face, text, color=INK):
        """Draw text anchored at (x, y_top); y_top is the ascender top."""
        cx = x
        for ch in text:
            ox, oy, adv, w, h, data = atlas.glyph_for(face, ch)
            if w and h:
                gx, gy = cx + ox, y_top + oy
                for row in range(h):
                    src = row * w
                    for col in range(w):
                        a = data[src + col]
                        if a:
                            self._px(gx + col, gy + row, color, a)
            cx += adv
        return cx

    def draw_lines(self, atlas, x, y_top, face, lines, leading, color=INK):
        y = y_top
        for line in lines:
            self.draw_text(atlas, x, y, face, line, color)
            y += leading
        return y

    def draw_globe(self, cx, cy, r, color=INK):
        """Line globe: outer circle, two meridians, two parallels."""
        def dot(px, py):
            self._px(px, py, color)
            self._px(px + 1, py, color)
            self._px(px, py + 1, color)
            self._px(px + 1, py + 1, color)
        steps = 360
        for i in range(steps):
            t = 2.0 * math.pi * i / steps
            c, s = math.cos(t), math.sin(t)
            dot(int(cx + r * c), int(cy + r * s))                 # rim
            dot(int(cx + r * 0.42 * c), int(cy + r * s))          # meridian
            dot(int(cx + r * c), int(cy + r * 0.42 * s))          # equator band
            for fy, fr in ((-0.55, 0.83), (0.55, 0.83)):
                dot(int(cx + r * fr * c),
                    int(cy + r * fy + r * 0.20 * s))              # parallels


# ---------------------------------------------------------------- measure
def measure_story(atlas, story):
    """Wrap a story and return its block height plus wrapped lines."""
    head, head_cut = atlas.wrap(F_HEAD, story["headline"], COL_W, 2)
    summ, summ_cut = atlas.wrap(F_SUMMARY, story["summary"], COL_W, 2)
    height = (len(head) * HEAD_LEADING + len(summ) * SUMMARY_LEADING
              + STORY_GAP)
    return {"story": story, "head": head, "summ": summ,
            "height": height, "cut": head_cut or summ_cut}


def balance(blocks, ncols, limit):
    """Split blocks into ncols columns, minimising the tallest column.

    Exact dynamic program over prefix sums; deterministic.
    Returns a list of column block-lists. Raises if even the best
    split overflows `limit`.
    """
    n = len(blocks)
    pref = [0]
    for b in blocks:
        pref.append(pref[-1] + b["height"])
    INF = 10 ** 9
    # best[k][i]: smallest possible tallest column for first i blocks
    # in k columns; cut[k][i]: where the last column starts.
    best = [[INF] * (n + 1) for _ in range(ncols + 1)]
    cut = [[0] * (n + 1) for _ in range(ncols + 1)]
    best[0][0] = 0
    for k in range(1, ncols + 1):
        for i in range(k, n + 1):
            for j in range(k - 1, i):
                col_h = pref[i] - pref[j]
                worst = max(best[k - 1][j], col_h)
                if worst < best[k][i]:
                    best[k][i] = worst
                    cut[k][i] = j
    if best[ncols][n] > limit:
        raise SystemExit("OVERFLOW: best split needs %d px, have %d"
                         % (best[ncols][n], limit))
    cols = []
    i = n
    for k in range(ncols, 0, -1):
        j = cut[k][i]
        cols.append(blocks[j:i])
        i = j
    cols.reverse()
    return cols, best[ncols][n]


# ---------------------------------------------------------------- paint
def paint(sheet, atlas):
    report = {"columns": [], "truncated": []}
    # --- masthead
    name_w = atlas.width(F_MASTHEAD, MASTHEAD)
    sheet.draw_text(atlas, (PAGE_W - name_w) // 2, 16, F_MASTHEAD, MASTHEAD)
    sheet.draw_text(atlas, MARGIN, 72, F_DATE, DATELINE_L)
    right_w = atlas.width(F_DATE, DATELINE_R)
    sheet.draw_text(atlas, PAGE_W - MARGIN - right_w, 72, F_DATE, DATELINE_R)
    sheet.hrule(MARGIN, 90, CONTENT_W, INK, 2)
    sheet.hrule(MARGIN, 94, CONTENT_W, INK, 1)

    # --- lead story + globe
    sheet.draw_text(atlas, MARGIN, 104, F_DATE, LEAD["kicker"], RED)
    head, _ = atlas.wrap(F_LEAD_HEAD, LEAD["headline"], 740, 2)
    y = sheet.draw_lines(atlas, MARGIN, 122, F_LEAD_HEAD, head, 36)
    deck, _ = atlas.wrap(F_LEAD_DECK, LEAD["deck"], 740, 2)
    sheet.draw_lines(atlas, MARGIN, y + 6, F_LEAD_DECK, deck, 18)
    sheet.draw_globe(878, 166, 46)
    cap = "THE WORLD \u2014 22 NOV 2026"
    cap_w = atlas.width(F_FOOTER, cap)
    sheet.draw_text(atlas, 878 - cap_w // 2, 220, F_FOOTER, cap)
    sheet.hrule(MARGIN, 234, CONTENT_W, INK, 2)

    # --- body columns
    blocks = [measure_story(atlas, s) for s in STORIES]
    for idx, b in enumerate(blocks):
        if b["cut"]:
            report["truncated"].append(idx + 1)
    # Reserve room for section headers: one per section change plus
    # one repeat header at the top of a continuing column.
    body_h = BODY_BOTTOM - BODY_TOP
    cols, tallest = balance(blocks, NCOLS, body_h - 4 * HEADER_H)
    for ci, col in enumerate(cols):
        x = MARGIN + ci * (COL_W + COL_GAP)
        if ci:
            gx = x - COL_GAP // 2 - 1
            sheet.vrule(gx, BODY_TOP, body_h, RULE_FAINT)
        y = BODY_TOP
        prev_section = None
        for b in col:
            sec = b["story"]["section"]
            if sec != prev_section:
                sheet.draw_text(atlas, x, y, F_SECTION, sec, RED)
                sheet.hrule(x, y + 16, COL_W, INK, 1)
                y += HEADER_H
                prev_section = sec
            y = sheet.draw_lines(atlas, x, y, F_HEAD, b["head"],
                                 HEAD_LEADING)
            y = sheet.draw_lines(atlas, x, y, F_SUMMARY, b["summ"],
                                 SUMMARY_LEADING)
            y += STORY_GAP
        report["columns"].append((len(col), y - BODY_TOP))
        if y > BODY_BOTTOM:
            raise SystemExit("OVERFLOW: column %d reaches y=%d" % (ci, y))

    # --- numbers band + footer
    sheet.hrule(MARGIN, 988, CONTENT_W, INK, 1)
    sheet.hrule(MARGIN, 1008, CONTENT_W, INK, 1)
    num_w = atlas.width(F_SECTION, NUMBERS)
    sheet.draw_text(atlas, (PAGE_W - num_w) // 2, 992, F_SECTION, NUMBERS)
    sheet.draw_text(atlas, MARGIN, 1014, F_FOOTER, FOOTER_L)
    foot_w = atlas.width(F_FOOTER, FOOTER_R)
    sheet.draw_text(atlas, PAGE_W - MARGIN - foot_w, 1014, F_FOOTER, FOOTER_R)
    report["tallest_content"] = tallest
    return report


# ---------------------------------------------------------------- png
def _chunk(tag, data):
    blob = struct.pack(">I", len(data)) + tag + data
    return blob + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)


def encode_png(sheet):
    raw = bytearray()
    for row in range(PAGE_H):
        raw.append(0)
        raw += sheet.buf[row * PAGE_W * 3:(row + 1) * PAGE_W * 3]
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", PAGE_W, PAGE_H,
                                       8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return bytes(png)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    atlas = GlyphAtlas(os.path.join(here, "atlas.bin"))
    sheet = Sheet()
    report = paint(sheet, atlas)
    png = encode_png(sheet)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else "out"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png)
    digest = hashlib.sha256(png).hexdigest()
    print("wrote %s (%d bytes, sha256 %s)" % (path, len(png), digest))
    print("stories=%d columns=%s tallest_content=%d"
          % (len(STORIES) + 1, report["columns"], report["tallest_content"]))
    if report["truncated"]:
        print("WARNING truncated stories: %s" % report["truncated"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
