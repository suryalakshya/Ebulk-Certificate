# 🚀 Deployment Guide for Render.com (Frontend + Backend)

This guide provides step-by-step instructions for deploying the **Certificate Generator & Email Dispatcher** (FastAPI Backend + Vite React Frontend) on **[Render.com](https://render.com)**.

---

## ⚡ Option 1: Automatic Blueprint Deployment (Recommended & Single Web Service)

Render supports deploying the entire full-stack app as a single service using `render.yaml`. This option builds the React frontend into static assets and serves them directly through FastAPI on a free Render Web Service.

### Steps:
1. **Push your code to GitHub / GitLab**.
2. Go to your **[Render Dashboard](https://dashboard.render.com)**.
3. Click **New +** → Select **Blueprint**.
4. Connect your GitHub/GitLab repository.
5. Render will automatically detect `render.yaml` and configure the service:
   - **Name**: `certificate-generator`
   - **Environment**: `Python`
   - **Build Command**: `./render-build.sh`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Under **Environment Variables**, set your secret Brevo API passwords:
   - `BREVO_SMTP_PASSWORD_1` = `xkeysib-your_brevo_api_key_1`
   - `BREVO_SMTP_PASSWORD_2` = `xkeysib-your_brevo_api_key_2` (optional)
   - `BREVO_SMTP_PASSWORD_3` = `xkeysib-your_brevo_api_key_3` (optional)
7. Click **Apply**. Render will automatically build the frontend, install backend dependencies, and launch your app live!

---

## 🌐 Option 2: Manual Web Service Setup (Render Web Service)

If you prefer setting up manually on Render without Blueprints:

### Step 1: Create Web Service
1. Click **New +** → **Web Service** on Render.
2. Select your repository.
3. Fill in the following configuration:
   - **Name**: `certificate-generator`
   - **Environment**: `Python 3`
   - **Region**: Select your closest region (e.g., Singapore, Frankfurt, Oregon)
   - **Branch**: `main` (or your default branch)
   - **Build Command**: `./render-build.sh`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 2: Set Environment Variables
In the **Environment** tab of your service, add the following key-value pairs:

| Key | Example Value |
|---|---|
| `AUTHORIZED_ADMIN_EMAIL` | `suryalbrcem9@gmail.com` |
| `BREVO_FROM_EMAIL_1` | `suryalbrcem9@gmail.com` |
| `BREVO_SMTP_USER_1` | `suryalbrcem9@gmail.com` |
| `BREVO_SMTP_PASSWORD_1` | `xkeysib-YOUR_ACTUAL_BREVO_API_KEY_1` |
| `BREVO_FROM_EMAIL_2` | `suryamaddipudi10@gmail.com` |
| `BREVO_SMTP_USER_2` | `suryamaddipudi10@gmail.com` |
| `BREVO_SMTP_PASSWORD_2` | `xkeysib-YOUR_ACTUAL_BREVO_API_KEY_2` |
| `BREVO_FROM_EMAIL_3` | `communityservice202526@gmail.com` |
| `BREVO_SMTP_USER_3` | `communityservice202526@gmail.com` |
| `BREVO_SMTP_PASSWORD_3` | `xkeysib-YOUR_ACTUAL_BREVO_API_KEY_3` |
| `BREVO_FROM_NAME` | `ACG Organizing Committee` |
| `BREVO_SMTP_HOST` | `smtp-relay.brevo.com` |
| `BREVO_SMTP_PORT` | `587` |
| `MAX_EMAILS` | `300` |
| `SEND_EMAIL` | `True` |

4. Click **Create Web Service**.

---

## 🛠️ Verification
Once deployed, Render will provide a live URL (e.g. `https://certificate-generator-xxxx.onrender.com`).
1. Open the URL in your browser.
2. Enter your authorized admin email (`suryalbrcem9@gmail.com`) to receive your OTP.
3. Enter the 6-digit OTP code received in your email inbox to log in!
