create table if not exists jobs (
  job_id text primary key,
  status text not null,
  created_at double precision not null,
  updated_at double precision not null,
  request jsonb not null,
  result jsonb,
  error jsonb,
  attempts integer not null default 0
);

create index if not exists idx_jobs_status_created_at on jobs (status, created_at desc);
create index if not exists idx_jobs_updated_at on jobs (updated_at);

create table if not exists predictions (
  prediction_id text primary key,
  username text not null,
  created_at double precision not null,
  request jsonb not null,
  result jsonb not null,
  metrics jsonb not null,
  meta jsonb not null
);

create index if not exists idx_predictions_username_created_at on predictions (username, created_at desc);
