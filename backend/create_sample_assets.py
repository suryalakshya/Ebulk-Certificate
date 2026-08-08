import csv
import os
from PIL import Image, ImageDraw, ImageFont

def create_sample_template(output_path: str):
    # Create high-resolution certificate template (2000 x 1414 pixels)
    width, height = 2000, 1414
    img = Image.new("RGB", (width, height), color="#FAF8F5")
    draw = ImageDraw.Draw(img)

    # Outer border - Gold & Navy accents
    draw.rectangle([40, 40, width - 40, height - 40], outline="#D4AF37", width=8)
    draw.rectangle([56, 56, width - 56, height - 56], outline="#1A2B4C", width=3)
    draw.rectangle([64, 64, width - 64, height - 64], outline="#D4AF37", width=2)

    # Decorative corner ribbons
    draw.polygon([(40, 40), (240, 40), (40, 240)], fill="#1A2B4C")
    draw.polygon([(40, 40), (180, 40), (40, 180)], fill="#D4AF37")
    
    draw.polygon([(width-40, height-40), (width-240, height-40), (width-40, height-240)], fill="#1A2B4C")
    draw.polygon([(width-40, height-40), (width-180, height-40), (width-40, height-180)], fill="#D4AF37")

    # Header text
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 46)
        font_sub = ImageFont.truetype("arial.ttf", 26)
        font_cert = ImageFont.truetype("georgiab.ttf", 64)
        font_body = ImageFont.truetype("georgia.ttf", 32)
        font_sig = ImageFont.truetype("arialbd.ttf", 24)
    except Exception:
        font_title = font_sub = font_cert = font_body = font_sig = ImageFont.load_default()

    # Organization Header
    draw.text((width // 2, 140), "LAKIREDDY BALI REDDY COLLEGE OF ENGINEERING", fill="#0F2042", font=font_title, anchor="mm")
    draw.text((width // 2, 200), "(An Autonomous Institution since 2010)", fill="#C0392B", font=font_sub, anchor="mm")
    draw.text((width // 2, 240), "Approved by AICTE, New Delhi and Permanently Affiliated to JNTUK, Kakinada", fill="#444444", font=font_sub, anchor="mm")

    # Event Title
    draw.text((width // 2, 330), "Poster Presentation Contest", fill="#D32F2F", font=font_cert, anchor="mm")
    draw.text((width // 2, 400), "Innovating Ideas, Engineering the Future", fill="#333333", font=font_sub, anchor="mm")

    # Certificate Title
    draw.text((width // 2, 490), "CERTIFICATE OF PARTICIPATION", fill="#0F2042", font=font_cert, anchor="mm")

    # Body static line
    draw.text((width // 2, 600), "This certificate is proudly presented to", fill="#444444", font=font_body, anchor="mm")
    # Underline for name
    draw.line([400, 690, 1600, 690], fill="#888888", width=2)

    # Roll No static text
    draw.text((360, 750), "HT No.", fill="#444444", font=font_body, anchor="rm")
    draw.line([380, 760, 750, 760], fill="#888888", width=2)

    draw.text((780, 750), "for participating in the Poster Presentation Contest", fill="#444444", font=font_body, anchor="lm")
    draw.text((width // 2, 820), "organized by Association of Computer Geeks (ACG), Dept of CSE", fill="#0F2042", font=font_body, anchor="mm")
    draw.text((width // 2, 880), "held on July 25, 2026 at LBRCE Mylavaram.", fill="#444444", font=font_body, anchor="mm")

    # Certificate ID static label bottom right
    draw.text((1500, 1330), "Certificate ID:", fill="#666666", font=font_sig, anchor="rm")

    # Signature lines
    draw.line([300, 1200, 600, 1200], fill="#333333", width=2)
    draw.text((450, 1230), "Coordinator\n(Mr. A.S.R.C. Murthy)", fill="#C0392B", font=font_sig, anchor="mm", align="center")

    draw.line([850, 1200, 1150, 1200], fill="#333333", width=2)
    draw.text((1000, 1230), "Convener & HOD CSE\n(Dr. S. Nagarjuna Reddy)", fill="#0F2042", font=font_sig, anchor="mm", align="center")

    draw.line([1400, 1200, 1700, 1200], fill="#333333", width=2)
    draw.text((1550, 1230), "Principal\n(Dr. K. Appa Rao)", fill="#C0392B", font=font_sig, anchor="mm", align="center")

    img.save(output_path, "PNG")
    print(f"Created template at {output_path}")

def create_sample_csv(output_path: str):
    rows = [
        {
            "name": "SURYA MADDIPUDI",
            "roll_number": "23761A05M9",
            "email": "suryamaddipudi10@gmail.com",
            "department": "CSE",
        },
        {
            "name": "ANANYA VERMA",
            "roll_number": "23761A0501",
            "email": "ananya.verma@example.com",
            "department": "CSE",
        },
        {
            "name": "RISHABH SHARMA",
            "roll_number": "23761A0512",
            "email": "rishabh.sharma@example.com",
            "department": "CSE",
        },
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "roll_number", "email", "department"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created sample CSV at {output_path}")

if __name__ == "__main__":
    os.makedirs("d:/Flutter/certifcates/backend", exist_ok=True)
    create_sample_template("d:/Flutter/certifcates/backend/template.png")
    create_sample_csv("d:/Flutter/certifcates/backend/sample_data.csv")
