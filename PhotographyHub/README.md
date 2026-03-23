# 📸 PhotographyHub: Elite On-Demand Photography Portal

PhotographyHub is a high-end, real-time photography booking platform designed for elite service delivery. Built with Django and powered by an **Autonomous Expansion Engine**, it connects premium photographers in Ahmedabad with customers across 10 specialized niches.

## 🌈 Key Features & Innovations

### 🚀 Autonomous Expansion Engine
- **Expanding Ripple Search**: Real-time Celery-driven task that automatically expands the search radius from 5km to 60km until a photographer is found.
- **Elite Window**: 5-minute priority access for "Elite Partner" photographers before a job goes public.
- **Radar Tracking**: Photographers can "Save" jobs to expand their tracking window or receive instant alerts via **Django Channels (WebSockets)**.

### 🎯 Expertise & Priority System (Phase 4)
- **Expert-First Dispatch**: Premium photographers with matching niche expertise (e.g., "Wedding Expert") receive a **10-minute head start** on relevant bookings.
- **Service-Strict Matching**: Multi-service bookings (Photo + Video + Drone) are precisely matched to photographers offering all required skills.
- **Unified Profile Management**: Photographers can manage their 17+ niche specializations and 4 core services via a premium grid-based interface.

### 📱 Mobile-First PWA Experience
- **Zero-Install Access**: PWA manifest and service worker integration for an app-style experience on Android and iOS.
- **Strict Device Control**: Desktop/Tablet restriction overlay to enforce a high-focus, mobile-only workflow for photographers.
- **Real-Time Push Alerts**: Instant job notifications powered by Django Channels and browser-native push APIs.

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
- **Styling**: Tailwind CSS / Vanilla CSS Hybrid
- **Authentication**: Google OAuth 2.0 (Gmail Login)

---

## 🚀 Quick Start Guide

### Local Development (Windows)
1. **Prepare Environment**:
   ```bash
   python -m venv .venv
   .\.venv/Scripts/activate
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
- `apps/bookings/`: Core expansion engine, ripple matching logic, and pricing.
- `apps/accounts/`: User profiles, Photographer HomeBase, and expertise management.
- `templates/`: Premium HTML5 architecture with mobile-first CSS overlays.
- `run_all.bat`: Master lifecycle script for developers.

---

## 🔐 Configuration & Integrations
Setup your environment variables in `.env` for:
- **Google OAuth**: Client ID & Secret for social login.
- **Supabase**: PostgreSQL connection string.
- **Celery**: Redis broker and result backend URLs.

---

## 💎 Developers
Built with a focus on **Peak UX** and **Atomic Concurrency**.
