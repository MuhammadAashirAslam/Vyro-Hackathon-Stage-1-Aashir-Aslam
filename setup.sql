-- ============================================
-- Grabpic: Database Setup Script
-- Run this ONCE in the Supabase SQL Editor
-- ============================================

-- Enable pgvector extension
create extension if not exists vector;

-- Faces table: one row per unique identity
create table if not exists faces (
  grab_id uuid primary key default gen_random_uuid(),
  embedding vector(128) not null,
  created_at timestamptz default now()
);

-- Images table: one row per photo file
create table if not exists images (
  image_id uuid primary key default gen_random_uuid(),
  file_path text unique not null,
  file_name text not null,
  ingested_at timestamptz default now()
);

-- Join table: one image can contain many faces, one face can appear in many images
create table if not exists image_faces (
  id uuid primary key default gen_random_uuid(),
  image_id uuid references images(image_id) on delete cascade,
  grab_id uuid references faces(grab_id) on delete cascade,
  face_bbox jsonb,
  unique(image_id, grab_id)
);

-- Index for fast vector similarity search
-- NOTE: IVFFlat requires rows to exist before index creation.
-- If table is empty, use this alternative first:
create index if not exists faces_embedding_idx on faces using hnsw (embedding vector_cosine_ops);
