# Diagrama do Banco de Dados — ReadAlong

Diagrama entidade-relacionamento gerado a partir de [`schema.sql`](./schema.sql).

## Diagrama ER

```mermaid
erDiagram
    BOOKS ||--o{ PROCESSING_RUNS : "possui"
    BOOKS ||--o{ MEDIA_MANIFESTS : "possui"
    PROCESSING_RUNS ||--o{ PAGES : "contém"
    PROCESSING_RUNS ||--o{ JOBS : "dispara"
    PROCESSING_RUNS ||--o{ EVENTS : "gera"
    PAGES ||--o{ CHUNKS : "divide-se em"
    PAGES ||--o{ MEDIA_MANIFESTS : "possui"
    PAGES ||--o{ JOBS : "gera"
    CHUNKS ||--o| AUDIO_ASSETS : "gera"
    CHUNKS ||--o{ JOBS : "gera"
    WORKERS ||--o{ WORKER_METRICS : "registra"
    WORKERS ||--o{ JOBS : "executa"

    BOOKS {
        uuid id PK
        text title
        book_url text
        text author
        varchar language
        book_status status
        int total_pages
        int completed_pages
        timestamp created_at
        timestamp updated_at
    }

    PROCESSING_RUNS {
        uuid id PK
        uuid book_id FK
        book_status status
        int page_size
        timestamp created_at
        timestamp started_at
        timestamp completed_at
    }

    PAGES {
        uuid id PK
        uuid processing_run_id FK
        int sequence
        text page_url
        int sentence_count
        book_status status
        timestamp created_at
        timestamp updated_at
    }

    CHUNKS {
        uuid id PK
        uuid page_id FK
        int sequence
        text text
        book_status status
        timestamp created_at
        timestamp updated_at
    }

    AUDIO_ASSETS {
        uuid id PK
        uuid chunk_id FK
        text storage_key
        text format
        float duration
        float size
        book_status status
        timestamp created_at
    }

    MEDIA_MANIFESTS {
        uuid id PK
        uuid book_id FK
        uuid page_id FK
        text media_type
        text storage_key
        book_status status
        timestamp created_at
    }

    WORKERS {
        uuid id PK
        text name
        worker_status status
        text cpu_model
        text cpu_cores
        text cpu_threads
        text ram_total
        text ram_type
        text ram_speed
        text os
        text os_version
        timestamp last_heart_beat
        timestamp created_at
        timestamp updated_at
    }

    WORKER_METRICS {
        uuid id PK
        uuid worker_id FK
        timestamp timestamp
        text cpu_usage
        text memory_usage
        text disk_usage
        text cpu_temperature
    }

    JOBS {
        uuid id PK
        uuid processing_run_id FK
        uuid page_id FK
        uuid chunk_id FK
        job_type type
        book_status status
        uuid worker_id FK
        int attempt
        timestamp queued_at
        timestamp started_at
        timestamp finished_at
        int error_code
        text error_message
    }

    EVENTS {
        uuid id PK
        event_type event_type
        timestamp occurred_at
        text entity_type
        text entity_id
        text actor_type
        uuid processing_run_id FK
        text correlation_id
        text causation_id
        text payload
    }
```

## Cardinalidades

| De | Para | Cardinalidade | Significado |
|---|---|---|---|
| `books` | `processing_runs` | 1 : N | um livro tem várias execuções de processamento |
| `books` | `media_manifests` | 1 : N | um livro tem vários manifestos de mídia |
| `processing_runs` | `pages` | 1 : N | uma execução gera várias páginas |
| `processing_runs` | `jobs` | 1 : N | uma execução dispara vários jobs |
| `processing_runs` | `events` | 1 : N | uma execução gera vários eventos |
| `pages` | `chunks` | 1 : N | uma página se divide em vários chunks |
| `pages` | `media_manifests` | 1 : N | uma página tem vários manifestos |
| `pages` | `jobs` | 1 : N | uma página gera vários jobs |
| `chunks` | `audio_assets` | 1 : 1 | um chunk gera um único asset de áudio |
| `chunks` | `jobs` | 1 : N | um chunk gera vários jobs |
| `workers` | `worker_metrics` | 1 : N | um worker registra várias métricas |
| `workers` | `jobs` | 1 : N | um worker executa vários jobs |

## Enums

- **`book_status`**: `pending`, `processing`, `completed`, `completed_with_errors`, `failed`
- **`worker_status`**: `healthy`, `unhealthy`
- **`job_type`**: `analyze_grammar`, `generate_audio`, `generate_hls`
- **`event_type`**: `BOOK_CREATED`, `BOOK_PROCESSING_STARTED`, `BOOK_COMPLETED`, `BOOK_COMPLETED_WITH_ERRORS`, `PAGE_CREATED`, `PAGE_PROCESSING_STARTED`, `PAGE_COMPLETED`, `PAGE_FAILED`, `CHUNK_CREATED`, `CHUNK_COMPLETED`, `CHUNK_FAILED`, `JOB_CREATED`, `JOB_QUEUED`, `JOB_ASSIGNED`, `JOB_STARTED`, `JOB_COMPLETED`, `JOB_FAILED`, `JOB_RETRY`, `WORKER_REGISTERED`, `WORKER_ONLINE`, `WORKER_OFFLINE`, `WORKER_UNHEALTHY`, `WORKER_RECOVERED`, `AUDIO_GENERATED`, `AUDIO_UPLOADED`, `HLS_GENERATED`
