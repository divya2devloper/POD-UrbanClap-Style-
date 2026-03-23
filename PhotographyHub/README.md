# 📸 PhotographyHub: Elite On-Demand Photography Portal

PhotographyHub is a high-end, real-time photography booking platform designed for elite service delivery. Built with Django and powered by an **Autonomous Expansion Engine**, it connects premium photographers in Ahmedabad with customers across 10 specialized niches.

## 🌈 Key Features & Innovations

### 🚀 Autonomous Expansion Engine
- **Expanding Ripple Search**: Real-time Celery-driven task that automatically expands the search radius from 5km to 60km until a photographer is found.
- **Elite Window**: 5-minute priority access for "Elite Partner" photographers before a job goes public.
- **Radar Tracking**: Photographers can "Save" jobs to expand their tracking window or receive instant alerts via **Django Channels (WebSockets)**.

### 💰 Smart Financial Logic
- **Unified Premium Tier**: 'Wedding', 'Pre-Wedding', and 'Maternity' are unified under a single **Premium** pricing profile for consistent, elite service delivery.
- **Granular Durations**: Booking options for 1, 2, 3, 4, 6, and 8-hour shoots with real-time price previews (Base + 18% GST).
- **Automated Payouts**: Standardized 7-day payout scheduling after job acceptance.

### 🖼️ Peak Visual Aesthetic
- **Visual Saturation**: Background "Mash" pushed to peak vibrancy (0.38 opacity) with high-saturation filters.
- **Niche-Specific Symbols**: Unique iconography for every category (e.g., Hearts for Weddings, Briefcases for Corporate).
- **Global Placeholder Coverage**: High-vibrancy, full-color Unsplash fallbacks ensuring no "empty frames" across the site.

---

## 🛠️ Technology Stack
- **Framework**: Django 5.x
- **Database**: PostgreSQL (Supabase / Local)
- **Async Workers**: Celery & Redis
- **Real-time**: Django Channels (WebSockets)
- **Styling**: Tailwind CSS
- **Authentication**: Google OAuth 2.0 (Gmail Login)

---

## 🚀 Quick Start Guide

### Local Development (Windows)
1. **Prepare Environment**:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Unified Startup & Management**:
   Run the master script to start the Web Server, Celery Worker, and Celery Beat simultaneously:
   ```batch
   ./run_all.bat
   ```
   *Note: This script handles **Unified Process Cleanup**—closing the web server window automatically terminates all background worker windows.*

### Docker Deployment
1. Ensure Docker Desktop is running.
2. Run the same `./run_all.bat`. It will automatically detect Docker and launch the entire stack via `docker compose`.

---

## 📂 Project Structure
- `apps/bookings/`: Core expansion engine, pricing logic, and radar tracking.
- `apps/accounts/`: User profiles, Photographer HomeBase, and Financial stats.
- `templates/`: Premium HTML5/Tailwind layout with unified `base.html` architecture.
- `run_all.bat`: Master lifecycle script for developers.

---

## 🔐 OAuth Setup
Follow the `auth_setup_guide.md` in the documentation to configure your Google Cloud Console for Gmail Login integration.

---

## 💎 Developers
Built with a focus on **Peak UX** and **Atomic Concurrency**.
