# Vyro-Hackathon-Stage-1-Aashir-Aslam

# 📸 Grabpic — Intelligent Identity & Retrieval Engine

> **High-performance facial recognition backend for large-scale event photography.**  
> Uses AI-powered face detection to automatically group images and provides a **Selfie-as-a-Key** retrieval system.

**Problem**: A marathon with 500 runners and 50,000 photos. Finding *your* photos? Impossible.  
**Solution**: Grabpic uses **DeepFace + FaceNet** to auto-tag every face with a unique `grab_id`, then lets users snap a selfie to instantly retrieve every photo they appear in.

---

## ⚙️ Tech Stack & Models

| Layer | Technology | Details |
|-------|-----------|---------|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Python 3.10+, async-ready, auto Swagger docs |
| **Database** | [Supabase](https://supabase.com) (PostgreSQL) | Hosted Postgres with pgvector extension |
| **Vector Search** | [pgvector](https://github.com/pgvector/pgvector) | HNSW index, cosine distance (`<=>` operator) |
| **Face Detection** | [DeepFace](https://github.com/serengil/deepface) | Wrapper for multiple face recognition models |
| **Face Recognition Model** | **FaceNet** | 128-dimensional face embeddings, high accuracy |
| **Face Detector Backend** | **OpenCV** (Haar Cascade) | Fast multi-face detection per image |
| **ML Runtime** | **TensorFlow / tf-keras** | Backend for FaceNet model inference |
| **Frontend** | Vanilla HTML/CSS/JS | Dark theme, glassmorphism, no build step |
| **API Docs** | Swagger UI + ReDoc | Auto-generated at `/docs` and `/redoc` |

### Models Used

| Model | Purpose | Output | Source |
|-------|---------|--------|--------|
| `Facenet` | Face embedding extraction | 128-dim float vector per face | [DeepFace](https://github.com/serengil/deepface) → `DeepFace.represent(model_name="Facenet")` |
| `opencv` | Face detection / localization | Bounding box `{x, y, w, h}` per face | [DeepFace](https://github.com/serengil/deepface) → `detector_backend="opencv"` |

> **First run**: The FaceNet model weights (~250MB) are auto-downloaded on first ingestion call. Be patient.

---

## 🏗️ Architecture

```
                              ┌──────────────────────┐
                              │   FastAPI Backend     │
                              │   (Python 3.10+)     │
                              └──────────┬───────────┘
                                         │
          ┌──────────────────────────────┼──────────────────────────────┐
          │                              │                              │
 POST /api/v1/ingest          POST /api/v1/auth/selfie      GET /api/v1/users/{id}/images
          │                              │                              │
 ┌────────▼─────────┐          ┌─────────▼──────────┐       ┌──────────▼──────────┐
 │ DeepFace FaceNet  │          │  Vector Similarity  │       │  PostgreSQL JOIN     │
 │ 128-dim embedding │          │  Search (pgvector)  │       │  image_faces ⟷      │
 │ Multi-face detect │          │  cosine distance    │       │  images              │
 └────────┬─────────┘          └─────────┬──────────┘       └─────────────────────┘
          │                              │
          └──────────────┬───────────────┘
                         │
              ┌──────────▼──────────┐
              │  Supabase Postgres   │
              │  + pgvector (HNSW)   │
              └─────────────────────┘
```

### Database Schema (3 tables)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `faces` | One row per **unique identity** | `grab_id` (UUID PK), `embedding` (vector 128-dim) |
| `images` | One row per **photo file** | `image_id` (UUID PK), `file_path` (unique), `file_name` |
| `image_faces` | **Many-to-many** join table | `image_id` → `images`, `grab_id` → `faces`, `face_bbox` (JSONB) |

> **Key**: One image can contain multiple people. One person can appear in many images. The `image_faces` table handles this M:N relationship.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- A [Supabase](https://supabase.com) project (free tier works)

### 1. Clone & Install

```bash
git clone https://github.com/MuhammadAashirAslam/Vyro-Hackathon-Stage-1-Aashir-Aslam.git
cd Vyro-Hackathon-Stage-1-Aashir-Aslam
pip install -r requirements.txt
```

#### `requirements.txt`
```
fastapi
uvicorn[standard]
psycopg2-binary
deepface
tf-keras
numpy
python-multipart
python-dotenv
pytest
httpx
pgvector
```

### 2. Configure Environment

```bash
cp .env.example .env
```

#### `.env.example`
```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
STORAGE_PATH=./storage
SIMILARITY_THRESHOLD=0.4
```

Edit `.env` and replace with your **actual Supabase credentials**:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres
STORAGE_PATH=./storage
SIMILARITY_THRESHOLD=0.4
```

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | Supabase PostgreSQL connection string (**required**) |
| `STORAGE_PATH` | `./storage` | Directory containing event photos |
| `SIMILARITY_THRESHOLD` | `0.4` | Max cosine distance for face match (lower = stricter) |

**Where to find your connection string:**  
[Supabase Dashboard](https://supabase.com/dashboard) → Your Project → **Project Settings** → **Database** → **Connection string** → **URI**

### 3. Set Up the Database

Go to [Supabase SQL Editor](https://supabase.com/dashboard) → **SQL Editor** → **New Query** → Paste the contents of [`setup.sql`](setup.sql) → **Run**.

```sql
-- Enables pgvector, creates faces/images/image_faces tables + HNSW index
-- Full script in setup.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS faces (
  grab_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  embedding vector(128) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS images (
  image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_path TEXT UNIQUE NOT NULL,
  file_name TEXT NOT NULL,
  ingested_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS image_faces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  image_id UUID REFERENCES images(image_id) ON DELETE CASCADE,
  grab_id UUID REFERENCES faces(grab_id) ON DELETE CASCADE,
  face_bbox JSONB,
  UNIQUE(image_id, grab_id)
);

CREATE INDEX IF NOT EXISTS faces_embedding_idx
  ON faces USING hnsw (embedding vector_cosine_ops);
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

| URL | What |
|-----|------|
| http://localhost:8000 | **Web UI** — Upload selfie, find photos, upload images |
| http://localhost:8000/docs | **Swagger UI** — Interactive API docs |
| http://localhost:8000/redoc | **ReDoc** — Alternative API docs |
| http://localhost:8000/api/v1/health | **Health Check** |

---

## 🌐 Web Frontend

Grabpic ships with a built-in **dark-themed Web UI** at the root URL (`/`). No separate frontend server needed.

| Tab | What it does |
|-----|-------------|
| 🔍 **Find My Photos** | Upload a selfie → AI matches your face → displays all your photos in a gallery |
| 📤 **Upload Photos** | Drag & drop event photos into storage (supports batch upload) |
| ⚙️ **Process** | Triggers face detection & indexing on all uploaded photos |

---

## 📡 API Endpoints & cURL Examples

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```
```json
{ "status": "ok" }
```

---

### Upload Photos to Storage
```bash
# Single file
curl -X POST http://localhost:8000/api/v1/upload \
  -F "files=@./storage/photo1.jpg"

# Multiple files
curl -X POST http://localhost:8000/api/v1/upload \
  -F "files=@./photo1.jpg" \
  -F "files=@./photo2.jpg" \
  -F "files=@./photo3.png"
```
```json
{
  "uploaded": 3,
  "files": [
    { "file": "photo1.jpg", "saved_as": "a1b2c3d4_photo1.jpg" },
    { "file": "photo2.jpg", "saved_as": "e5f6a7b8_photo2.jpg" },
    { "file": "photo3.png", "saved_as": "c9d0e1f2_photo3.png" }
  ],
  "errors": []
}
```

---

### Ingest & Process All Photos
```bash
curl -X POST http://localhost:8000/api/v1/ingest
```
```json
{
  "images_processed": 15,
  "faces_detected": 23,
  "new_faces_found": 8,
  "total_faces_known": 8
}
```
> **Idempotent** — safe to call multiple times. Already-processed images are skipped.

---

### Selfie Authentication (Selfie-as-a-Key)
```bash
curl -X POST http://localhost:8000/api/v1/auth/selfie \
  -F "file=@./my_selfie.jpg"
```
**Success (200):**
```json
{
  "grab_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "confidence": 0.8523
}
```
**No match (404):**
```json
{
  "detail": "No matching identity found. Your face is not in any ingested photos."
}
```

---

### Get All Photos for a Person
```bash
curl http://localhost:8000/api/v1/users/a1b2c3d4-e5f6-7890-abcd-ef1234567890/images
```
```json
{
  "grab_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "total": 3,
  "images": [
    {
      "image_id": "11111111-2222-3333-4444-555555555555",
      "file_path": "finish_line_001.jpg",
      "file_name": "finish_line_001.jpg",
      "ingested_at": "2026-04-18T10:30:00Z"
    }
  ]
}
```

---

### Serve a Stored Image
```bash
curl http://localhost:8000/api/v1/storage/photo1.jpg --output photo1.jpg
```

---

## 🧠 How It Works

### Ingestion Pipeline (`POST /api/v1/ingest`)
```
Storage Directory → Crawl for .jpg/.jpeg/.png
       ↓
  For each image:
       ↓
  DeepFace.represent(model_name="Facenet", detector_backend="opencv")
       ↓
  Extracts ALL faces → 128-dim embedding per face
       ↓
  For each face embedding:
       ↓
  Query pgvector: SELECT nearest face WHERE cosine_distance ≤ 0.4
       ↓
  ┌─ Match found → reuse existing grab_id
  └─ No match    → INSERT new face → new grab_id (UUID)
       ↓
  INSERT into image_faces (image_id, grab_id, face_bbox)
```

### Selfie Authentication (`POST /api/v1/auth/selfie`)
```
Upload selfie → Extract face embedding (enforce_detection=True)
       ↓
  Query pgvector: nearest neighbor cosine distance search
       ↓
  distance ≤ 0.4 → Return grab_id + confidence (1 - distance)
  distance > 0.4 → 404 "No match found"
```

### Multiple Faces per Image
A group photo with 5 people → 5 face embeddings → each independently matched or creates a new identity → 5 rows in `image_faces` linking the same `image_id` to 5 different `grab_id`s.

---

## 🧪 Unit Tests

```bash
pytest tests/ -v
```

Tests use **mocked** DB and face detection — no Supabase connection needed.

| Test File | What It Tests |
|-----------|--------------|
| `test_ingest.py` | Ingestion pipeline, face counting, empty storage |
| `test_auth.py` | Selfie match, no-match 404, invalid file type, no-face-detected |
| `test_users.py` | Image retrieval, 404 for unknown IDs, empty results |

---

## 📁 Project Structure

```
Vyro-Hackathon-Stage-1-Aashir-Aslam/
├── app/
│   ├── main.py                # FastAPI app entry point + frontend serving
│   ├── config.py              # .env loader (DATABASE_URL, STORAGE_PATH, SIMILARITY_THRESHOLD)
│   ├── database.py            # psycopg2 connection helper (RealDictCursor)
│   ├── models/
│   │   └── schemas.py         # Pydantic response models
│   ├── routers/
│   │   ├── ingest.py          # POST /api/v1/ingest
│   │   ├── auth.py            # POST /api/v1/auth/selfie
│   │   ├── users.py           # GET  /api/v1/users/{grab_id}/images
│   │   └── upload.py          # POST /api/v1/upload + GET /api/v1/storage/{path}
│   └── services/
│       ├── face_service.py    # DeepFace FaceNet embedding extraction + cosine distance
│       └── ingest_service.py  # Storage crawl + DB persistence + face matching
├── frontend/
│   └── index.html             # Built-in dark-themed Web UI (served at /)
├── storage/                   # Drop event photos here (or use /api/v1/upload)
├── tests/
│   ├── test_ingest.py         # Ingestion tests (mocked)
│   ├── test_auth.py           # Auth tests (mocked)
│   └── test_users.py          # User image retrieval tests (mocked)
├── setup.sql                  # Database schema — run once in Supabase SQL Editor
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── .gitignore
└── README.md
```

---

## 🚧 Error Handling

| Status | Meaning |
|--------|---------|
| `400` | Invalid file type, no face detected, missing filename |
| `404` | No matching identity, unknown grab_id, no faces ingested yet |
| `500` | Internal error (DB, model failure) |

---

## 📝 Key Design Decisions

1. **FaceNet (128-dim)** — Compact embeddings, fast inference, good accuracy for event photos
2. **HNSW index over IVFFlat** — Works on empty tables (critical for first-time setup)
3. **Idempotent ingestion** — `ON CONFLICT DO NOTHING` makes re-running `/ingest` safe
4. **Synchronous DB** — `psycopg2` sync calls (simpler to debug, sufficient throughput)
5. **Embedded frontend** — Single HTML file served by FastAPI (no separate server/build step)
6. **Confidence = 1 − cosine_distance** — Distance 0 = identical → confidence 1.0

---

*Built by Muhammad Aashir Aslam for [Vyrothon 2026](https://vyro.ai) Hackathon*
