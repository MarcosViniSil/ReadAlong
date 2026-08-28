-- ============================================================
-- ReadAlong — PostgreSQL schema
-- Generated from the Python models in src/models/
-- Requires PostgreSQL 13+ (gen_random_uuid)
-- ============================================================

-- ---------------------------
-- ENUM types
-- ---------------------------

CREATE TYPE book_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'completed_with_errors',
    'failed'
);

CREATE TYPE worker_status AS ENUM (
    'healthy',
    'unhealthy'
);

CREATE TYPE job_type AS ENUM (
    'analyze_grammar',
    'generate_audio',
    'generate_hls'
);

CREATE TYPE event_type AS ENUM (
    'BOOK_CREATED',
    'BOOK_PROCESSING_STARTED',
    'BOOK_COMPLETED',
    'BOOK_COMPLETED_WITH_ERRORS',
    'PAGE_CREATED',
    'PAGE_PROCESSING_STARTED',
    'PAGE_COMPLETED',
    'PAGE_FAILED',
    'CHUNK_CREATED',
    'CHUNK_COMPLETED',
    'CHUNK_FAILED',
    'JOB_CREATED',
    'JOB_QUEUED',
    'JOB_ASSIGNED',
    'JOB_STARTED',
    'JOB_COMPLETED',
    'JOB_FAILED',
    'JOB_RETRY',
    'WORKER_REGISTERED',
    'WORKER_ONLINE',
    'WORKER_OFFLINE',
    'WORKER_UNHEALTHY',
    'WORKER_RECOVERED',
    'AUDIO_GENERATED',
    'AUDIO_UPLOADED',
    'HLS_GENERATED'
);

-- ---------------------------
-- Tables
-- ---------------------------

-- Model: Book.py
CREATE TABLE books (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT NOT NULL,
    author          TEXT NOT NULL,
    language        VARCHAR(10) NOT NULL DEFAULT 'en'
                    CHECK (language IN (
                        'af','sq','ar','hy','eu','be','bn','bs','bg','ca',
                        'zh-CN','zh-TW','hr','cs','da','nl','en','eo','et',
                        'fi','fr','gl','ka','de','el','gu','ht','he','hi',
                        'hu','is','id','ga','it','ja','kn','kk','ko','lv',
                        'lt','mk','ms','ml','mt','mr','no','fa','pl','pt',
                        'pa','ro','ru','sr','sk','sl','es','sw','sv','ta',
                        'te','th','tr','uk','ur','vi','cy','xh','zu'
                    )),
    status          book_status NOT NULL,
    total_pages     INTEGER NOT NULL DEFAULT 0,
    book_url        TEXT NOT NULL,
    completed_pages INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model: ProcessingRun.py
CREATE TABLE processing_runs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id      UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    status       book_status NOT NULL,
    page_size    INTEGER NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Model: Page.py
CREATE TABLE pages (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processing_run_id UUID NOT NULL REFERENCES processing_runs(id) ON DELETE CASCADE,
    sequence          INTEGER NOT NULL,
    page_url          TEXT NOT NULL,
    sentence_count    INTEGER NOT NULL DEFAULT 0,
    status            book_status NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (processing_run_id, sequence)
);

-- Model: chunk.py
CREATE TABLE chunks (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id    UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    sequence   INTEGER NOT NULL,
    text       TEXT NOT NULL,
    status     book_status NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (page_id, sequence)
);

-- Model: AudioAsset.py
CREATE TABLE audio_assets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id    UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    storage_key TEXT NOT NULL,
    format      TEXT NOT NULL,
    duration    DOUBLE PRECISION NOT NULL,
    size        DOUBLE PRECISION NOT NULL,
    status      book_status NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model: MediaManifest.py
CREATE TABLE media_manifests (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id     UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    page_id     UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    type        TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    status      book_status NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model: worker.py
CREATE TABLE workers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    status          worker_status NOT NULL,
    cpu_model       TEXT,
    cpu_cores       TEXT,
    cpu_threads     TEXT,
    ram_total       TEXT,
    ram_type        TEXT,
    ram_speed       TEXT,
    os              TEXT,
    os_version      TEXT,
    last_heart_beat TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model: WorkerMetric.py
CREATE TABLE worker_metrics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    cpu_usage       TEXT,
    memory_usage    TEXT,
    disk_usage      TEXT,
    cpu_temperature TEXT
);

-- Model: Job.py
CREATE TABLE jobs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processing_run_id UUID NOT NULL REFERENCES processing_runs(id) ON DELETE CASCADE,
    page_id           UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    chunk_id          UUID REFERENCES chunks(id) ON DELETE SET NULL,
    type              job_type NOT NULL,
    status            book_status NOT NULL,
    worker_id         UUID REFERENCES workers(id) ON DELETE SET NULL,
    attempt           INTEGER NOT NULL DEFAULT 0,
    queued_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at        TIMESTAMPTZ,
    finished_at       TIMESTAMPTZ,
    error_code        INTEGER,
    error_message     TEXT
);

-- Model: Event.py
CREATE TABLE events (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type        event_type NOT NULL,
    occurred_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    entity_type       TEXT NOT NULL,
    entity_id         TEXT NOT NULL,
    actor_type        TEXT,
    processing_run_id UUID REFERENCES processing_runs(id) ON DELETE SET NULL,
    correlation_id    TEXT,
    causation_id      TEXT,
    payload           TEXT
);

-- ---------------------------
-- Indexes
-- ---------------------------

CREATE INDEX idx_processing_runs_book_id  ON processing_runs (book_id);
CREATE INDEX idx_processing_runs_status   ON processing_runs (status);

CREATE INDEX idx_pages_processing_run_id  ON pages (processing_run_id);
CREATE INDEX idx_pages_status             ON pages (status);

CREATE INDEX idx_chunks_page_id           ON chunks (page_id);
CREATE INDEX idx_chunks_status            ON chunks (status);

CREATE INDEX idx_audio_assets_chunk_id    ON audio_assets (chunk_id);

CREATE INDEX idx_media_manifests_book_id  ON media_manifests (book_id);
CREATE INDEX idx_media_manifests_page_id  ON media_manifests (page_id);

CREATE INDEX idx_workers_status           ON workers (status);

CREATE INDEX idx_worker_metrics_worker_id ON worker_metrics (worker_id, timestamp);

CREATE INDEX idx_jobs_processing_run_id   ON jobs (processing_run_id);
CREATE INDEX idx_jobs_page_id             ON jobs (page_id);
CREATE INDEX idx_jobs_chunk_id            ON jobs (chunk_id);
CREATE INDEX idx_jobs_worker_id           ON jobs (worker_id);
CREATE INDEX idx_jobs_type_status         ON jobs (type, status);

CREATE INDEX idx_events_occurred_at       ON events (occurred_at);
CREATE INDEX idx_events_processing_run_id ON events (processing_run_id);
CREATE INDEX idx_events_event_type        ON events (event_type);

-- ---------------------------
-- updated_at auto-maintenance
-- ---------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_books_updated_at
    BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_pages_updated_at
    BEFORE UPDATE ON pages
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_chunks_updated_at
    BEFORE UPDATE ON chunks
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_workers_updated_at
    BEFORE UPDATE ON workers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
