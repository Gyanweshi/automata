from __future__ import annotations

import html
import zipfile
from datetime import datetime, timezone
from pathlib import Path


OUT = Path("docs/fur-love-india-launch-strategy-deck.pptx")
LOGO = Path(r"C:\Users\Devan\Downloads\FA_Fur_Love_Wordmark_BW.png")
SLIDE_W = 12192000
SLIDE_H = 6858000


def emu(inches: float) -> int:
    return int(inches * 914400)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


class Slide:
    def __init__(self, bg: str = "F6F1E8") -> None:
        self.bg = bg
        self.items: list[str] = []
        self._id = 2
        self.needs_logo = False

    def next_id(self) -> int:
        self._id += 1
        return self._id

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str,
        line: str | None = None,
        radius: bool = False,
        alpha: int | None = None,
    ) -> None:
        sid = self.next_id()
        geom = "roundRect" if radius else "rect"
        fill_xml = f'<a:solidFill><a:srgbClr val="{fill}">'
        if alpha is not None:
            fill_xml += f'<a:alpha val="{alpha}"/>'
        fill_xml += "</a:srgbClr></a:solidFill>"
        line_xml = '<a:ln><a:noFill/></a:ln>' if line is None else (
            f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        )
        self.items.append(
            f"""
            <p:sp>
              <p:nvSpPr><p:cNvPr id="{sid}" name="Shape {sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
              <p:spPr>
                <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
                <a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>
                {fill_xml}{line_xml}
              </p:spPr>
              <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
            </p:sp>
            """
        )

    def oval(self, x: float, y: float, w: float, h: float, fill: str, line: str | None = None, alpha: int | None = None) -> None:
        sid = self.next_id()
        fill_xml = f'<a:solidFill><a:srgbClr val="{fill}">'
        if alpha is not None:
            fill_xml += f'<a:alpha val="{alpha}"/>'
        fill_xml += "</a:srgbClr></a:solidFill>"
        line_xml = '<a:ln><a:noFill/></a:ln>' if line is None else (
            f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        )
        self.items.append(
            f"""
            <p:sp>
              <p:nvSpPr><p:cNvPr id="{sid}" name="Oval {sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
              <p:spPr>
                <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
                <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
                {fill_xml}{line_xml}
              </p:spPr>
              <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
            </p:sp>
            """
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str = "7A5BA8", width: int = 19050) -> None:
        sid = self.next_id()
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        flips = ""
        if x2 < x1:
            flips += ' flipH="1"'
        if y2 < y1:
            flips += ' flipV="1"'
        self.items.append(
            f"""
            <p:cxnSp>
              <p:nvCxnSpPr><p:cNvPr id="{sid}" name="Line {sid}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
              <p:spPr>
                <a:xfrm{flips}><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
                <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
                <a:ln w="{width}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln>
              </p:spPr>
            </p:cxnSp>
            """
        )

    def text(
        self,
        text: str,
        x: float,
        y: float,
        w: float,
        h: float,
        size: int = 32,
        color: str = "161514",
        bold: bool = False,
        italic: bool = False,
        font: str = "Aptos Display",
        align: str = "l",
        all_caps: bool = False,
        tracking: int = 0,
    ) -> None:
        sid = self.next_id()
        attrs = f'sz="{size * 100}"'
        if bold:
            attrs += ' b="1"'
        if italic:
            attrs += ' i="1"'
        if tracking:
            attrs += f' spc="{tracking}"'
        value = text.upper() if all_caps else text
        paras = value.split("\n")
        p_xml = ""
        for line in paras:
            p_xml += (
                f'<a:p><a:pPr algn="{align}"/>'
                f'<a:r><a:rPr {attrs}><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
                f'<a:latin typeface="{font}"/></a:rPr><a:t>{esc(line)}</a:t></a:r></a:p>'
            )
        self.items.append(
            f"""
            <p:sp>
              <p:nvSpPr><p:cNvPr id="{sid}" name="Text {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
              <p:spPr>
                <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln>
              </p:spPr>
              <p:txBody><a:bodyPr wrap="square" anchor="t"><a:spAutoFit/></a:bodyPr><a:lstStyle/>{p_xml}</p:txBody>
            </p:sp>
            """
        )

    def pic(self, x: float, y: float, w: float, h: float, rid: str = "rId2", name: str = "Logo") -> None:
        sid = self.next_id()
        if rid == "rId2":
            self.needs_logo = True
        self.items.append(
            f"""
            <p:pic>
              <p:nvPicPr><p:cNvPr id="{sid}" name="{esc(name)}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
              <p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
              <p:spPr>
                <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
              </p:spPr>
            </p:pic>
            """
        )

    def logo(self, dark: bool = True) -> None:
        if dark:
            self.pic(0.55, 0.35, 1.35, 0.32, "rId2", "Fur Love Wordmark")
        else:
            self.text("FUR LOVE", 0.55, 0.35, 1.35, 0.25, 10, "FAF8F4", True, all_caps=True, tracking=6000)

    def footer(self, num: str, dark: bool = True) -> None:
        color = "D9D3CA" if dark else "6B6660"
        self.line(0.55, 6.83, 12.75, 6.83, color, 7620)
        self.text(num, 12.28, 6.98, 0.42, 0.18, 8, "6B6660" if dark else "D9D3CA")

    def dog_placeholder(self, x: float, y: float, w: float, h: float, label: str, dark: bool = False) -> None:
        base = "161514" if dark else "EFE7D7"
        stroke = "B8A3D6" if not dark else "FAF8F4"
        self.rect(x, y, w, h, base, stroke)
        self.oval(x + w * 0.58, y + h * 0.16, w * 0.24, h * 0.2, "E8C8C2", None, 70000)
        self.line(x + 0.35, y + 0.45, x + w - 0.35, y + h - 0.45, "C9AFDE", 15240)
        self.line(x + w - 0.35, y + 0.45, x + 0.35, y + h - 0.45, "C9AFDE", 15240)
        self.text("DOG / PRODUCT IMAGE", x + 0.35, y + 0.35, w - 0.7, 0.25, 10, "7A5BA8" if not dark else "EADEF3", True, all_caps=True, tracking=5000)
        self.text(label, x + 0.35, y + h - 0.82, w - 0.7, 0.45, 16, "161514" if not dark else "FAF8F4", True)

    def full_image_placeholder(self, label: str, dark: bool = True) -> None:
        base = "161514" if dark else "EFE7D7"
        line = "4A2E78" if dark else "B8A3D6"
        text = "FAF8F4" if dark else "161514"
        self.rect(0, 0, 13.333, 7.5, base, None)
        self.oval(8.1, 0.65, 3.2, 2.55, "E8C8C2", None, 42000)
        self.oval(0.9, 4.2, 2.4, 1.85, "A8B398", None, 30000)
        self.line(0.65, 0.7, 12.65, 6.8, line, 10160)
        self.line(12.65, 0.7, 0.65, 6.8, line, 10160)
        self.text("FULL-BLEED DOG / PRODUCT IMAGE", 0.72, 0.78, 4.6, 0.22, 9, "B8A3D6" if dark else "7A5BA8", True, all_caps=True, tracking=4500)
        self.text(label, 0.72, 6.34, 7.8, 0.32, 14, text, True)

    def scrim(self, side: str = "left", dark: bool = True) -> None:
        fill = "161514" if dark else "F6F1E8"
        if side == "left":
            self.rect(0, 0, 6.25, 7.5, fill, None, alpha=72000)
        elif side == "right":
            self.rect(7.0, 0, 6.333, 7.5, fill, None, alpha=72000)
        elif side == "bottom":
            self.rect(0, 4.25, 13.333, 3.25, fill, None, alpha=78000)
        elif side == "center":
            self.rect(2.0, 1.1, 9.3, 5.3, fill, None, alpha=76000)

    def xml(self) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="{self.bg}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(self.items)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def campaign_slide(
    num: int,
    eyebrow: str,
    title: str,
    body: str,
    image: str,
    zone: str = "left",
    dark_photo: bool = True,
    text_dark: bool = False,
) -> Slide:
    s = Slide("161514" if dark_photo else "EFE7D7")
    s.full_image_placeholder(image, dark=dark_photo)
    s.scrim(zone, dark=not text_dark)
    logo_dark = text_dark
    s.logo(dark=logo_dark)
    main = "161514" if text_dark else "FAF8F4"
    sub = "3C3935" if text_dark else "D9D3CA"
    accent = "7A5BA8" if text_dark else "E8C8C2"
    if zone == "right":
        x, y = 7.45, 1.28
    elif zone == "bottom":
        x, y = 0.78, 4.72
    elif zone == "center":
        x, y = 2.48, 1.72
    else:
        x, y = 0.78, 1.28
    s.text(eyebrow, x, y, 4.3, 0.25, 10, accent, True, all_caps=True, tracking=5000)
    s.text(title, x, y + 0.48, 5.4 if zone != "center" else 7.9, 1.55, 43, main, True)
    s.text(body, x + 0.02, y + 2.42, 4.95 if zone != "center" else 7.0, 0.72, 19, sub)
    s.footer(f"{num:02d}", dark=text_dark)
    return s


def build_slides() -> list[Slide]:
    slides: list[Slide] = []
    slides.append(campaign_slide(
        1,
        "India launch strategy",
        "Fur Love,\nFor Love",
        "A beauty-led launch for dogs who are loved deeply.",
        "Hero dog portrait with product cue. Keep calm space on left.",
        zone="left",
        dark_photo=True,
    ))
    slides.append(campaign_slide(
        2,
        "The gap",
        "Pet love has changed.\nPet care has not caught up.",
        "This is the gap Fur Love can own in India.",
        "Pet parent and dog, intimate close-up. Warm daylight.",
        zone="right",
        dark_photo=True,
    ))
    slides.append(campaign_slide(
        3,
        "The tension",
        "The category still looks functional.",
        "Most pet grooming launches look instructional, cute, or noisy. Fur Love should feel like a ritual people aspire to keep.",
        "Pet shelf/product clutter image. Text calm zone on left.",
        zone="left",
        dark_photo=True,
    ))
    slides.append(campaign_slide(
        4,
        "The opening",
        "Make dog care feel like beauty care.",
        "Show texture, touch, packaging, coat finish, and softness before asking people to remember SKUs.",
        "Beauty-style product texture with dog fur",
        zone="bottom",
        dark_photo=True,
    ))

    slides.append(campaign_slide(
        5,
        "Communication thought",
        "Fur Love,\nFor Love",
        "Not a line about grooming. A line about the standard of care love deserves.",
        "Dog face close-up, soft eye contact. Cream towel, no clutter.",
        zone="center",
        dark_photo=True,
    ))

    slides.append(campaign_slide(
        6,
        "The tone",
        "Premium, clinical, intimate.",
        "Warm enough to feel like love. Sharp enough to feel like skincare. Never kiddish, never pet-shop cute.",
        "Clean bathroom ritual, towel, dog, product",
        zone="right",
        dark_photo=True,
    ))

    s = Slide("F6F1E8")
    s.full_image_placeholder("Soft abstract ritual image: towel, fur, product edge. Low contrast background.", dark=False)
    s.rect(0, 0, 13.333, 7.5, "F6F1E8", None, alpha=82000)
    s.logo()
    s.text("How the story moves", 0.75, 0.98, 3.6, 0.25, 10, "7A5BA8", True, all_caps=True, tracking=5000)
    s.text("Do not reveal everything at once.", 0.72, 1.42, 6.2, 0.8, 39, "161514", True)
    story = [
        ("01", "Create desire", "Something premium is coming."),
        ("02", "Expose the gap", "Why does pet care look so basic?"),
        ("03", "Reveal the ritual", "Product, parent, dog, texture, finish."),
        ("04", "Build memory", "Repeat the formats until Fur Love feels familiar."),
    ]
    for i, (n, h, b) in enumerate(story):
        y = 2.72 + i * 0.86
        s.text(n, 0.82, y, 0.55, 0.25, 11, "7A5BA8", True)
        s.line(1.45, y + 0.17, 2.25, y + 0.17, "B8A3D6", 12700)
        s.text(h, 2.45, y - 0.04, 2.6, 0.35, 19, "161514", True)
        s.text(b, 5.18, y, 4.7, 0.28, 14, "3C3935")
    s.rect(10.55, 1.1, 1.25, 4.85, "E8C8C2", None)
    s.rect(11.92, 1.1, 0.55, 4.85, "A8B398", None)
    s.footer("07")
    slides.append(s)

    slides.append(campaign_slide(
        8,
        "Phase 1",
        "Build sightings before explanation.",
        "Packaging crops, coat close-ups, texture videos, ritual fragments, countdown stories, and city sightings.",
        "Mysterious product crop with fur and label",
        zone="left",
        dark_photo=True,
    ))

    s = Slide("161514")
    s.full_image_placeholder("Outdoor takeover visual: premium billboard with dog portrait and Fur Love line.", dark=True)
    s.scrim("left", dark=True)
    s.logo(dark=False)
    s.text("Grand pre-launch activity", 0.78, 0.95, 4.0, 0.25, 10, "E8C8C2", True, all_caps=True, tracking=5000)
    s.text("The Fur Love\nTakeover", 0.72, 1.42, 5.8, 1.5, 48, "FAF8F4", True)
    s.text("A luxury outdoor teaser built to make people ask, 'what is this?' before the product is revealed.", 0.78, 3.42, 5.2, 0.75, 21, "D9D3CA")
    s.rect(7.15, 1.02, 4.8, 4.8, "FAF8F4", "D9D3CA")
    s.text("Fur Love", 7.58, 1.62, 3.55, 0.58, 40, "161514", True)
    s.text("For Love", 7.62, 4.2, 3.0, 0.5, 32, "7A5BA8", True, italic=True, font="Georgia")
    s.oval(10.1, 3.23, 1.18, 1.18, "EADEF3", "C9AFDE")
    s.text("Coming soon\nto loved dogs", 10.25, 3.63, 0.88, 0.32, 9, "3C3935", True, align="c")
    s.footer("09", dark=False)
    slides.append(s)

    slides.append(campaign_slide(
        10,
        "Launch",
        "Reveal the ritual, then the range.",
        "The hero film should move from touch to texture to coat finish, then make the products easy to understand.",
        "Hero film still: parent applying product",
        zone="bottom",
        dark_photo=True,
    ))

    s = Slide("F6F1E8")
    s.full_image_placeholder("Blurred ritual/product background. Keep center-left calm.", dark=False)
    s.rect(0, 0, 13.333, 7.5, "F6F1E8", None, alpha=86000)
    s.logo()
    s.text("Launch content system", 0.78, 0.98, 3.4, 0.25, 10, "7A5BA8", True, all_caps=True, tracking=5000)
    s.text("One launch. Three repeating assets.", 0.72, 1.42, 6.6, 0.85, 39, "161514", True)
    cards = [
        ("Hero Film", "The full ritual and brand reveal."),
        ("SKU Reels", "Use-led demos for each product."),
        ("Creator First-Use", "Premium, honest parent + dog reactions."),
    ]
    colors = ["EADEF3", "E8C8C2", "E5E9DD"]
    for i, (h, b) in enumerate(cards):
        x = 0.78 + i * 4.08
        s.rect(x, 3.0, 3.55, 2.05, colors[i], None)
        s.text(h, x + 0.25, 3.35, 2.65, 0.38, 22, "161514", True)
        s.text(b, x + 0.25, 4.25, 2.55, 0.4, 14, "3C3935")
    s.footer("11")
    slides.append(s)

    slides.append(campaign_slide(
        12,
        "Sustainance",
        "Turn the launch into recall.",
        "Keep the feed moving with ritual series, better-care education, real parent use, packaging shots, and cultural moments.",
        "Real parent/dog testimonial or routine shot",
        zone="right",
        dark_photo=True,
    ))

    s = Slide("FAF8F4")
    s.full_image_placeholder("Soft product shelf and dog-care objects. Low contrast.", dark=False)
    s.rect(0, 0, 13.333, 7.5, "FAF8F4", None, alpha=86000)
    s.logo()
    s.text("Operating rhythm", 0.78, 0.98, 3.1, 0.25, 10, "7A5BA8", True, all_caps=True, tracking=5000)
    s.text("The deck should sell a system, not a post list.", 0.72, 1.42, 6.8, 0.8, 39, "161514", True)
    rows = [("Pre-launch", "Desire + sightings"), ("Launch week", "Ritual + range"), ("Next 30 days", "Repeat + explain"), ("Always-on", "Proof + culture")]
    for i, (h, b) in enumerate(rows):
        y = 2.85 + i * 0.78
        s.rect(0.78, y, 2.25, 0.42, "EADEF3", None)
        s.text(h, 0.98, y + 0.1, 1.75, 0.18, 11, "4A2E78", True)
        s.text(b, 3.35, y + 0.06, 3.8, 0.22, 17, "161514", True)
        s.line(7.35, y + 0.22, 11.8, y + 0.22, "D9D3CA", 7620)
    s.footer("13")
    slides.append(s)

    slides.append(campaign_slide(
        14,
        "The takeaway",
        "Fur Love is the premium care brand for loved dogs.",
        "This is not pet grooming content dressed up. It is a beauty launch built around love, ritual, and proof.",
        "Final hero dog, polished coat, calm premium frame. Text calm zone on left.",
        zone="left",
        dark_photo=True,
    ))

    return slides


def write_package(slides: list[Slide]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="png" ContentType="image/png"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
    ]
    for i in range(1, len(slides) + 1):
        content_types.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    content_types.append("</Types>")

    slide_ids = "\n".join(f'<p:sldId id="{255+i}" r:id="rId{i}"/>' for i in range(1, len(slides) + 1))
    pres_rels = "\n".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, len(slides) + 1)
    )
    pres_rels += f'\n<Relationship Id="rId{len(slides)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    pres_rels += f'\n<Relationship Id="rId{len(slides)+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'

    presentation = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{len(slides)+1}"/></p:sldMasterIdLst>
  <p:sldIdLst>{slide_ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""

    slide_layout = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""
    slide_master = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""
    theme = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Fur Love"><a:themeElements><a:clrScheme name="Fur Love"><a:dk1><a:srgbClr val="161514"/></a:dk1><a:lt1><a:srgbClr val="F6F1E8"/></a:lt1><a:dk2><a:srgbClr val="3C3935"/></a:dk2><a:lt2><a:srgbClr val="FAF8F4"/></a:lt2><a:accent1><a:srgbClr val="7A5BA8"/></a:accent1><a:accent2><a:srgbClr val="E8C8C2"/></a:accent2><a:accent3><a:srgbClr val="A8B398"/></a:accent3><a:accent4><a:srgbClr val="D9A85A"/></a:accent4><a:accent5><a:srgbClr val="B8A3D6"/></a:accent5><a:accent6><a:srgbClr val="2F4A4A"/></a:accent6><a:hlink><a:srgbClr val="7A5BA8"/></a:hlink><a:folHlink><a:srgbClr val="4A2E78"/></a:folHlink></a:clrScheme><a:fontScheme name="Fur Love"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme><a:fmtScheme name="Fur Love"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>"""
    core = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Fur Love India Launch Strategy</dc:title><dc:creator>Codex</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>"""
    app = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Microsoft PowerPoint</Application><PresentationFormat>On-screen Show (16:9)</PresentationFormat><Slides>{len(slides)}</Slides></Properties>"""

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "\n".join(content_types))
        z.writestr("_rels/.rels", root_rels)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.writestr("ppt/presentation.xml", presentation)
        z.writestr("ppt/_rels/presentation.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{pres_rels}</Relationships>""")
        z.writestr("ppt/theme/theme1.xml", theme)
        z.writestr("ppt/slideMasters/slideMaster1.xml", slide_master)
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>""")
        z.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>""")
        z.writestr("ppt/media/image1.png", LOGO.read_bytes())
        for i, slide in enumerate(slides, start=1):
            z.writestr(f"ppt/slides/slide{i}.xml", slide.xml())
            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>"""
            if slide.needs_logo:
                rels += '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image1.png"/>'
            rels += "</Relationships>"
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels)


if __name__ == "__main__":
    if not LOGO.exists():
        raise FileNotFoundError(LOGO)
    slides = build_slides()
    write_package(slides)
    print(f"Wrote {OUT} with {len(slides)} slides")
