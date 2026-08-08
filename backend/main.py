from __future__ import annotations

import asyncio
import csv
import io
import os
import re
import time
import zipfile
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from typing import Any, List, Optional
from PIL import Image

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from aiosmtplib import SMTP

from certificate import FieldSpec, render_certificate_png
from pdf_render import render_pdf_from_png

# ============================================================
# LOAD .ENV
# ============================================================

load_dotenv()

# ============================================================
# GLOBAL APP & PATHS
# ============================================================

BASE_DIR = Path(__file__).parent.resolve()
DEFAULT_TEMPLATE_PATH = str(BASE_DIR / "template.png")
DEFAULT_CSV_PATH = str(BASE_DIR / "sample_data.csv")
TEMP_TEMPLATE_PATH = str(BASE_DIR / "temp_user_template.png")
TEMP_CSV_PATH = str(BASE_DIR / "temp_user_data.csv")
OUTPUT_DIR = str(BASE_DIR / "certificates_output")


def get_active_template_path() -> str:
    if os.path.exists(TEMP_TEMPLATE_PATH):
        return TEMP_TEMPLATE_PATH
    return DEFAULT_TEMPLATE_PATH


def get_active_csv_path() -> str:
    if os.path.exists(TEMP_CSV_PATH):
        return TEMP_CSV_PATH
    return DEFAULT_CSV_PATH

app = FastAPI(title="Certificate Generator & Email Dispatcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CONFIGURATION MODEL
# ============================================================

class EmailConfig(BaseModel):
    brevo_smtp_host: str = os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com").strip()
    brevo_smtp_port: int = int(os.getenv("BREVO_SMTP_PORT", "587").strip())
    brevo_smtp_user: str = os.getenv("BREVO_SMTP_USER", "").strip()
    brevo_smtp_password: str = os.getenv("BREVO_SMTP_PASSWORD", "").strip().replace(" ", "")
    brevo_from_email: str = os.getenv("BREVO_FROM_EMAIL", "").strip()
    brevo_from_name: str = os.getenv("BREVO_FROM_NAME", "ACG Organizing Committee").strip()
    recipient_column: str = "email"
    email_subject: str = "Certificate of Participation - ACG Poster Presentation 2026"
    email_body: str = (
        "Dear {name},\n\n"
        "Thank you for your participation in the ACG Poster Presentation event organized by the Department of Computer Science and Engineering at LBRCE.\n\n"
        "Please find attached your Certificate of Participation for the event.\n\n"
        "Participant Details:\n"
        "Name: {name}\n"
        "Roll Number: {roll_number}\n"
        "Certificate ID: {certificate_id}\n\n"
        "This certificate acknowledges your contribution to the event.\n\n"
        "If you have any questions or need any assistance, please feel free to contact us.\n\n"
        "Best regards,\n"
        "ACG Organizing Committee\n"
        "Department of Computer Science and Engineering\n"
        "LBRCE\n"
    )
    max_emails: int = 100
    certificate_workers: int = 10
    smtp_workers: int = 5
    email_interval_seconds: float = 3.0
    send_email: bool = True
    output_format: str = "both"  # "both", "pdf", "png", "jpg"


class FieldConfigInput(BaseModel):
    field: str
    x: int
    y: int
    size: int = 40
    align: str = "center"
    font_path: str = "arial.ttf"
    color: str = "#000000"
    bold: bool = False


class GenerateRequest(BaseModel):
    fields: List[FieldConfigInput]
    output_format: str = "both"  # "both", "pdf", "png", "jpg"
    email_config: Optional[EmailConfig] = None


# Global job state for SSE streaming
JOB_STATE = {
    "running": False,
    "status": "idle",
    "logs": [],
    "progress": {"current": 0, "total": 0, "stage": ""},
    "successful": [],
    "failed": [],
}

def log_event(message: str):
    timestamp = time.strftime("[%H:%M:%S]")
    entry = f"{timestamp} {message}"
    JOB_STATE["logs"].append(entry)
    print(entry)


# ============================================================
# UTILITY & CSV FUNCTIONS
# ============================================================

ALLOWED_SENDERS = [
    "suryalbrcem9@gmail.com",
    "suryamaddipudi10@gmail.com",
    "communityservice202526@gmail.com",
]


def resolve_smtp_credentials(sender_email: str, fallback_user: str = "", fallback_password: str = "") -> tuple[str, str]:
    sender = (sender_email or "").strip().lower()
    e1 = os.getenv("BREVO_FROM_EMAIL_1", "suryalbrcem9@gmail.com").strip().lower()
    e2 = os.getenv("BREVO_FROM_EMAIL_2", "suryamaddipudi10@gmail.com").strip().lower()
    e3 = os.getenv("BREVO_FROM_EMAIL_3", "communityservice202526@gmail.com").strip().lower()

    if sender == e1:
        u = os.getenv("BREVO_SMTP_USER_1", e1).strip()
        p = os.getenv("BREVO_SMTP_PASSWORD_1", "").strip().replace(" ", "")
        return u, p or fallback_password or os.getenv("BREVO_SMTP_PASSWORD", "").strip().replace(" ", "")
    elif sender == e2:
        u = os.getenv("BREVO_SMTP_USER_2", e2).strip()
        p = os.getenv("BREVO_SMTP_PASSWORD_2", "").strip().replace(" ", "")
        return u, p or fallback_password or os.getenv("BREVO_SMTP_PASSWORD", "").strip().replace(" ", "")
    elif sender == e3:
        u = os.getenv("BREVO_SMTP_USER_3", e3).strip()
        p = os.getenv("BREVO_SMTP_PASSWORD_3", "").strip().replace(" ", "")
        return u, p or fallback_password or os.getenv("BREVO_SMTP_PASSWORD", "").strip().replace(" ", "")

    u = fallback_user or os.getenv("BREVO_SMTP_USER", sender).strip()
    p = fallback_password or os.getenv("BREVO_SMTP_PASSWORD", "").strip().replace(" ", "")
    return u, p


def read_csv_data(csv_path: str) -> list[dict[str, Any]]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise RuntimeError("CSV file does not contain headers.")
        rows = [row for row in reader if row]

    # Enforce strict 300 rows restriction
    return rows[:300]


class SafeDict(dict):
    def __missing__(self, key):
        return ""


def format_template(template: str, row: dict[str, Any]) -> str:
    values = {key: ("" if value is None else str(value)) for key, value in row.items()}
    return template.format_map(SafeDict(values))


def valid_email(email: str) -> bool:
    email = email.strip()
    if not email or " " in email or email.count("@") != 1:
        return False
    local, domain = email.split("@", 1)
    return bool(local and domain and "." in domain)


def safe_filename(value: str) -> str:
    value = str(value).strip()
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", value)
    return value[:120] or "certificate"


def create_email_message(
    row: dict[str, Any],
    file_paths: str | list[str] | None = None,
    config: EmailConfig | None = None,
    pdf_path: str | None = None,
) -> EmailMessage:
    paths = file_paths or pdf_path
    if not paths:
        raise ValueError("No attachment paths provided to create_email_message.")

    if isinstance(paths, str):
        paths = [paths]

    config = config or EmailConfig()
    recipient_col = config.recipient_column or "email"
    to_email = (row.get(recipient_col) or row.get("email") or "").strip()
    subject = format_template(config.email_subject, row)
    body = format_template(config.email_body, row)

    message = EmailMessage()
    message["From"] = formataddr((config.brevo_from_name, config.brevo_from_email))
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    for path_item in paths:
        attachment = Path(path_item)
        if not attachment.exists():
            continue

        ext = attachment.suffix.lower().lstrip(".")
        subtype = "pdf" if ext == "pdf" else "jpeg" if ext in ["jpg", "jpeg"] else "png"
        maintype = "application" if ext == "pdf" else "image"

        with attachment.open("rb") as file:
            data = file.read()

        message.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=attachment.name,
        )
    return message


# ============================================================
# ASYNC RATE LIMITER & SMTP WORKER
# ============================================================

class AsyncRateLimiter:
    def __init__(self, interval: float):
        self.interval = interval
        self.lock = asyncio.Lock()
        self.next_allowed_time = 0.0

    async def wait(self):
        async with self.lock:
            now = time.monotonic()
            if self.next_allowed_time > now:
                wait_time = self.next_allowed_time - now
                await asyncio.sleep(wait_time)
            send_time = time.monotonic()
            self.next_allowed_time = send_time + self.interval


class AsyncBrevoSMTP:
    def __init__(self, worker_id: int, config: EmailConfig):
        self.worker_id = worker_id
        self.config = config
        username, password = resolve_smtp_credentials(
            config.brevo_from_email,
            config.brevo_smtp_user,
            config.brevo_smtp_password,
        )
        self.smtp = SMTP(
            hostname=config.brevo_smtp_host,
            port=config.brevo_smtp_port,
            username=username,
            password=password,
            start_tls=True,
            timeout=30,
        )
        self.connected = False
        self.send_lock = asyncio.Lock()

    async def connect(self):
        await self.close()
        log_event(f"[SMTP-{self.worker_id}] Connecting to Brevo...")
        await self.smtp.connect()
        self.connected = True
        log_event(f"[SMTP-{self.worker_id}] ✓ Connected")

    async def send(self, message: EmailMessage):
        async with self.send_lock:
            if not self.connected:
                await self.connect()
            try:
                await self.smtp.send_message(message)
            except Exception:
                self.connected = False
                try:
                    await self.smtp.close()
                except Exception:
                    pass
                await self.connect()
                await self.smtp.send_message(message)

    async def close(self):
        if self.connected:
            try:
                self.smtp.close()
            except Exception:
                pass
            self.connected = False


def is_permanent_error(error: Exception) -> bool:
    text = str(error).lower()
    permanent_patterns = [
        "550", "551", "552", "553", "554", "5.1.1", "5.1.2", "5.7.1",
        "recipient refused", "invalid recipient", "invalid sender",
        "authentication failed", "authentication error", "unauthorized ip",
        "not verified", "blocked", "blacklisted", "spam",
    ]
    return any(pattern in text for pattern in permanent_patterns)


async def send_one_email(
    smtp: AsyncBrevoSMTP,
    limiter: AsyncRateLimiter,
    row: dict[str, Any],
    attachments: str | list[str],
    number: int,
    total: int,
    config: EmailConfig,
) -> tuple[bool, str, str]:
    name = (row.get("name") or "Unknown").strip()
    recipient_col = config.recipient_column or "email"
    email = (row.get(recipient_col) or row.get("email") or "").strip()

    if not valid_email(email):
        return (False, name, f"Invalid email address: {email}")

    try:
        message = create_email_message(row=row, file_paths=attachments, config=config)
    except Exception as error:
        return (False, name, str(error))

    max_retries = 3
    retry_delay = 5

    for attempt in range(1, max_retries + 1):
        try:
            await limiter.wait()
            log_event(f"[{number}/{total}] Sending to {name} <{email}> (attempt {attempt})")
            await smtp.send(message)
            log_event(f"✓ [{number}/{total}] Sent to {email}")
            return (True, name, email)
        except Exception as error:
            error_text = str(error)
            log_event(f"✗ [{number}/{total}] Attempt {attempt} failed for {email}: {error_text}")
            if is_permanent_error(error):
                log_event(f"  Permanent error. Skipping {email}.")
                return (False, name, error_text)
            if attempt < max_retries:
                delay = retry_delay * attempt
                log_event(f"  Temporary error. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

    return (False, name, "Maximum retries exceeded")


# ============================================================
# AUTHENTICATION MODELS & STORE
# ============================================================

class SendOTPRequest(BaseModel):
    email: str


class VerifyOTPRequest(BaseModel):
    email: str
    otp: str


OTP_STORE: dict[str, dict[str, Any]] = {}


AUTHORIZED_ADMIN_EMAIL = os.getenv("AUTHORIZED_ADMIN_EMAIL", "suryalbrcem9@gmail.com").strip().lower()


# ============================================================
# API ENDPOINTS
# ============================================================

@app.post("/api/auth/send-otp")
async def send_otp(req: SendOTPRequest):
    email = req.email.strip().lower()
    if not valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email address format.")

    if email != AUTHORIZED_ADMIN_EMAIL:
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: Email '{email}' is not authorized to log in. Only {AUTHORIZED_ADMIN_EMAIL} is allowed.",
        )

    import random
    otp_code = f"{random.randint(100000, 999999):06d}"
    OTP_STORE[email] = {
        "otp": otp_code,
        "expires_at": time.time() + 600,
    }

    # Send OTP strictly via Brevo SMTP email
    sender_email = AUTHORIZED_ADMIN_EMAIL
    username, password = resolve_smtp_credentials(sender_email)

    if not username or not password or password.startswith("your_api_key"):
        raise HTTPException(
            status_code=500,
            detail="Brevo SMTP password is missing or not configured in .env file. Please add your Brevo SMTP key to BREVO_SMTP_PASSWORD_1 in .env.",
        )

    try:
        msg = EmailMessage()
        msg["From"] = formataddr(("ACG Organizing Committee", sender_email))
        msg["To"] = email
        msg["Subject"] = f"Your Login OTP Code: {otp_code}"

        text_body = (
            f"Dear User,\n\n"
            f"Your OTP verification code for login to the Certificate Generator application is:\n\n"
            f"  {otp_code}\n\n"
            f"This code is valid for 10 minutes.\n\n"
            f"Best regards,\n"
            f"ACG Organizing Committee\n"
        )

        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }}
    .card {{ max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e5e7eb; }}
    .header {{ font-size: 20px; font-weight: 700; color: #111827; margin-bottom: 8px; text-align: center; }}
    .otp-code {{ font-size: 36px; font-weight: 800; letter-spacing: 6px; color: #2563eb; background: #eff6ff; border: 1px dashed #2563eb; border-radius: 8px; padding: 16px; text-align: center; margin: 24px 0; }}
    .footer {{ font-size: 13px; color: #6b7280; text-align: center; margin-top: 24px; border-top: 1px solid #f3f4f6; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">Certificate Generator Security Code</div>
    <p style="color: #374151; font-size: 15px; text-align: center;">Your verification code to complete your login is:</p>
    <div class="otp-code">{otp_code}</div>
    <p style="color: #6b7280; font-size: 13px; text-align: center;">This OTP is valid for 10 minutes. If you did not request this login, please ignore this message.</p>
    <div class="footer">ACG Organizing Committee</div>
  </div>
</body>
</html>"""

        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        smtp = SMTP(
            hostname=os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com"),
            port=int(os.getenv("BREVO_SMTP_PORT", "587")),
            username=username,
            password=password,
            start_tls=True,
            timeout=15,
        )
        await smtp.connect()
        await smtp.send_message(msg)
        try:
            smtp.close()
        except Exception:
            pass
        print(f"[AUTH] ✓ OTP email successfully sent to {email} via Brevo SMTP.")
    except Exception as err:
        print(f"[AUTH ERROR] Failed to send OTP email via Brevo SMTP: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send OTP email via Brevo SMTP: {err}. Please check your Brevo credentials in .env.",
        )

    return {"message": f"OTP verification code sent to {email}. Please check your email inbox."}


@app.post("/api/auth/verify-otp")
def verify_otp(req: VerifyOTPRequest):
    email = req.email.strip().lower()
    otp = req.otp.strip()

    if email != AUTHORIZED_ADMIN_EMAIL:
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: Email '{email}' is not authorized.",
        )

    data = OTP_STORE.get(email)
    if not data:
        raise HTTPException(status_code=400, detail="No active OTP found. Please request a new OTP code.")

    if time.time() > data["expires_at"]:
        OTP_STORE.pop(email, None)
        raise HTTPException(status_code=400, detail="OTP code has expired. Please request a new OTP code.")

    if data["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code. Please check and try again.")

    import random
    OTP_STORE.pop(email, None)
    return {
        "success": True,
        "token": f"session_{int(time.time())}_{random.randint(1000, 9999)}",
        "email": email,
    }


@app.post("/api/reset-session")
def reset_session():
    if os.path.exists(TEMP_TEMPLATE_PATH):
        try:
            os.remove(TEMP_TEMPLATE_PATH)
        except Exception:
            pass

    if os.path.exists(TEMP_CSV_PATH):
        try:
            os.remove(TEMP_CSV_PATH)
        except Exception:
            pass

    if os.path.exists(OUTPUT_DIR):
        try:
            import shutil
            shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
        except Exception:
            pass

    return {"message": "Session reset successfully"}


@app.get("/api/status")
def get_status():
    recipients_count = 0
    headers = []
    csv_path = get_active_csv_path()
    if os.path.exists(csv_path):
        try:
            data = read_csv_data(csv_path)
            recipients_count = len(data)
            headers = list(data[0].keys()) if data else []
        except Exception:
            pass

    return {
        "status": "ok",
        "template_exists": os.path.exists(get_active_template_path()),
        "csv_exists": os.path.exists(csv_path),
        "recipients_count": recipients_count,
        "csv_headers": headers,
        "job_state": JOB_STATE,
        "config_defaults": {
            "authorized_admin_email": AUTHORIZED_ADMIN_EMAIL,
            "brevo_from_email": os.getenv("BREVO_FROM_EMAIL", "").strip(),
            "brevo_from_name": os.getenv("BREVO_FROM_NAME", "ACG Organizing Committee").strip(),
            "brevo_smtp_host": os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com").strip(),
            "brevo_smtp_port": int(os.getenv("BREVO_SMTP_PORT", "587").strip()),
            "brevo_smtp_user": os.getenv("BREVO_SMTP_USER", "").strip(),
        },
    }


@app.get("/api/template-image")
def get_template_image():
    active_path = get_active_template_path()
    if not os.path.exists(active_path):
        raise HTTPException(status_code=404, detail="Template image not found.")
    return FileResponse(active_path, media_type="image/png")


@app.post("/api/upload-template")
async def upload_template(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        raise HTTPException(status_code=400, detail="Only image files (.png, .jpg, .jpeg) are supported.")
    
    contents = await file.read()
    with open(TEMP_TEMPLATE_PATH, "wb") as f:
        f.write(contents)
    return {"message": "Template image updated successfully", "filename": file.filename}


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    contents = await file.read()
    with open(TEMP_CSV_PATH, "wb") as f:
        f.write(contents)

    rows = read_csv_data(TEMP_CSV_PATH)
    headers = list(rows[0].keys()) if rows else []
    return {
        "message": "CSV uploaded successfully",
        "rows_count": len(rows),
        "headers": headers,
        "sample": rows[:3],
    }


@app.get("/api/csv-data")
def get_csv_data():
    csv_path = get_active_csv_path()
    if not os.path.exists(csv_path):
        return {"rows": [], "headers": []}
    rows = read_csv_data(csv_path)
    headers = list(rows[0].keys()) if rows else []
    return {"rows": rows, "headers": headers}


@app.post("/api/preview")
async def preview_certificate(req: GenerateRequest, row_index: int = 0):
    active_template = get_active_template_path()
    active_csv = get_active_csv_path()
    if not os.path.exists(active_template):
        raise HTTPException(status_code=404, detail="Template image missing.")

    rows = read_csv_data(active_csv) if os.path.exists(active_csv) else [{
        "name": "SURYA MADDIPUDI",
        "roll_number": "23761A05M9",
        "email": "suryamaddipudi10@gmail.com",
    }]

    row = rows[row_index % len(rows)]
    row["certificate_id"] = f"ACG-PP-2026-{(row_index + 1):03d}"

    fields = [
        FieldSpec(
            field=f.field,
            x=f.x,
            y=f.y,
            size=f.size,
            align=f.align,
            font_path=f.font_path,
            color=f.color,
            bold=f.bold,
        )
        for f in req.fields
    ]

    temp_preview_path = str(BASE_DIR / "temp_preview.png")
    render_certificate_png(
        template_path=active_template,
        output_path=temp_preview_path,
        row=row,
        fields=fields,
    )
    return FileResponse(temp_preview_path, media_type="image/png")


# Async task runner for email dispatch
async def run_full_generation_task(req: GenerateRequest):
    JOB_STATE["running"] = True
    JOB_STATE["status"] = "processing"
    JOB_STATE["logs"] = []
    JOB_STATE["successful"] = []
    JOB_STATE["failed"] = []

    active_template = get_active_template_path()
    active_csv = get_active_csv_path()

    config = req.email_config or EmailConfig()
    recipients = read_csv_data(active_csv)[:config.max_emails]

    for index, r in enumerate(recipients, start=1):
        r["certificate_id"] = f"ACG-PP-2026-{index:03d}"

    import shutil
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fields = [FieldSpec(**f.model_dump()) for f in req.fields]

    log_event("=" * 60)
    log_event("STEP 1: GENERATING CERTIFICATES")
    log_event("=" * 60)

    start_time = time.time()
    JOB_STATE["progress"] = {"current": 0, "total": len(recipients), "stage": "Generating Certificates"}

    output_fmt = req.output_format or config.output_format or "both"
    certificate_files = []
    for idx, row in enumerate(recipients, start=1):
        name = row.get("name") or f"student_{idx}"
        base = safe_filename(f"{idx:03d}_{name}")
        png_path = os.path.join(OUTPUT_DIR, f"{base}.png")
        pdf_path = os.path.join(OUTPUT_DIR, f"{base}.pdf")
        jpg_path = os.path.join(OUTPUT_DIR, f"{base}.jpg")

        try:
            page_size = render_certificate_png(
                template_path=active_template,
                output_path=png_path,
                row=row,
                fields=fields,
            )

            attachment_list = []

            if output_fmt == "both":
                render_pdf_from_png(png_path, pdf_path, page_size)
                attachment_list = [png_path, pdf_path]
            elif output_fmt == "pdf":
                render_pdf_from_png(png_path, pdf_path, page_size)
                if os.path.exists(png_path):
                    os.remove(png_path)
                attachment_list = [pdf_path]
            elif output_fmt == "jpg":
                with Image.open(png_path) as img:
                    img.convert("RGB").save(jpg_path, "JPEG", quality=95)
                if os.path.exists(png_path):
                    os.remove(png_path)
                attachment_list = [jpg_path]
            elif output_fmt == "png":
                attachment_list = [png_path]

            certificate_files.append((row, attachment_list))
            log_event(f"✓ Certificate [{output_fmt.upper()}] {idx}/{len(recipients)} generated for {name}")
        except Exception as e:
            log_event(f"✗ Certificate failed {idx}/{len(recipients)} for {name}: {e}")

        JOB_STATE["progress"]["current"] = idx

    gen_time = time.time() - start_time
    log_event(f"Certificate generation finished in {gen_time:.2f}s. Ready: {len(certificate_files)}/{len(recipients)}")

    if not config.send_email:
        log_event("Email sending disabled by user config.")
        JOB_STATE["running"] = False
        JOB_STATE["status"] = "completed"
        return

    # STEP 2: EMAIL DISPATCH
    log_event("=" * 60)
    log_event("STEP 2: ASYNC EMAIL SENDING")
    log_event("=" * 60)

    limiter = AsyncRateLimiter(config.email_interval_seconds)
    smtp_workers = [AsyncBrevoSMTP(worker_id=i+1, config=config) for i in range(config.smtp_workers)]

    JOB_STATE["progress"] = {"current": 0, "total": len(certificate_files), "stage": "Sending Emails"}

    # Connect workers
    try:
        await asyncio.gather(*[w.connect() for w in smtp_workers])
        log_event("✓ All async SMTP workers connected.")
    except Exception as err:
        log_event(f"✗ SMTP Connection error: {err}")
        for w in smtp_workers:
            await w.close()
        JOB_STATE["running"] = False
        JOB_STATE["status"] = "failed"
        return

    queue = asyncio.Queue()
    for idx, (row, attachment_list) in enumerate(certificate_files, start=1):
        await queue.put((idx, row, attachment_list))

    results_lock = asyncio.Lock()

    async def worker_loop(worker_id: int, smtp: AsyncBrevoSMTP):
        while True:
            try:
                number, row, attachment_list = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            try:
                success, name, result = await send_one_email(
                    smtp=smtp,
                    limiter=limiter,
                    row=row,
                    attachments=attachment_list,
                    number=number,
                    total=len(certificate_files),
                    config=config,
                )
                async with results_lock:
                    if success:
                        JOB_STATE["successful"].append({"name": name, "email": result})
                    else:
                        JOB_STATE["failed"].append({"name": name, "email": row.get("email", ""), "error": result})
                    JOB_STATE["progress"]["current"] = len(JOB_STATE["successful"]) + len(JOB_STATE["failed"])
            except Exception as e:
                async with results_lock:
                    JOB_STATE["failed"].append({"name": row.get("name", "Unknown"), "email": row.get("email", ""), "error": str(e)})
            finally:
                queue.task_done()

    email_start = time.time()
    tasks = [asyncio.create_task(worker_loop(i+1, smtp_workers[i])) for i in range(len(smtp_workers))]

    try:
        await asyncio.gather(*tasks)
    finally:
        await asyncio.gather(*[smtp.close() for smtp in smtp_workers], return_exceptions=True)

    email_time = time.time() - email_start
    log_event("=" * 60)
    log_event(f"EMAIL SENDING COMPLETE in {email_time:.2f}s")
    log_event(f"Successful: {len(JOB_STATE['successful'])}, Failed: {len(JOB_STATE['failed'])}")

    # Save failed report CSV
    if JOB_STATE["failed"]:
        failed_csv = os.path.join(OUTPUT_DIR, "failed_emails.csv")
        with open(failed_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "email", "error"])
            writer.writeheader()
            writer.writerows(JOB_STATE["failed"])
        log_event(f"Failed email report saved at: {failed_csv}")

    JOB_STATE["running"] = False
    JOB_STATE["status"] = "completed"


@app.post("/api/start-job")
async def start_job(req: GenerateRequest, background_tasks: BackgroundTasks):
    if JOB_STATE["running"]:
        raise HTTPException(status_code=400, detail="A job is already in progress.")
    background_tasks.add_task(run_full_generation_task, req)
    return {"message": "Job started successfully"}


@app.get("/api/job-progress")
def get_job_progress():
    return JOB_STATE


@app.get("/api/download-zip")
def download_output_zip():
    if not os.path.exists(OUTPUT_DIR):
        raise HTTPException(status_code=404, detail="Output directory does not exist.")

    files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith((".png", ".pdf", ".jpg", ".jpeg"))]
    if not files:
        raise HTTPException(status_code=400, detail="No generated certificates found.")

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            file_path = os.path.join(OUTPUT_DIR, file)
            zf.write(file_path, arcname=file)

    memory_file.seek(0)
    return StreamingResponse(
        memory_file,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=certificates_output.zip"},
    )


@app.get("/api/download-failed-csv")
def download_failed_csv():
    failed_csv = os.path.join(OUTPUT_DIR, "failed_emails.csv")
    if not os.path.exists(failed_csv):
        raise HTTPException(status_code=404, detail="No failed emails report found.")
    return FileResponse(failed_csv, media_type="text/csv", filename="failed_emails.csv")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
