-- Chainlit SQLAlchemy Data Layer Schema
-- Run this against your PostgreSQL database

CREATE TABLE IF NOT EXISTS users (
    "id" UUID PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "createdAt" TIMESTAMPTZ DEFAULT NOW(),
    "metadata" JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS threads (
    "id" UUID PRIMARY KEY,
    "name" TEXT,
    "userId" UUID REFERENCES users("id") ON DELETE CASCADE,
    "createdAt" TIMESTAMPTZ DEFAULT NOW(),
    "metadata" JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS steps (
    "id" UUID PRIMARY KEY,
    "threadId" UUID REFERENCES threads("id") ON DELETE CASCADE,
    "parentId" UUID REFERENCES steps("id") ON DELETE SET NULL,
    "name" TEXT,
    "type" TEXT,
    "input" TEXT,
    "output" TEXT,
    "createdAt" TIMESTAMPTZ DEFAULT NOW(),
    "startTime" TIMESTAMPTZ,
    "endTime" TIMESTAMPTZ,
    "metadata" JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS feedbacks (
    "id" UUID PRIMARY KEY,
    "stepId" UUID REFERENCES steps("id") ON DELETE CASCADE,
    "value" INTEGER,
    "comment" TEXT,
    "createdAt" TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS elements (
    "id" UUID PRIMARY KEY,
    "threadId" UUID REFERENCES threads("id") ON DELETE CASCADE,
    "stepId" UUID REFERENCES steps("id") ON DELETE CASCADE,
    "type" TEXT,
    "name" TEXT,
    "url" TEXT,
    "content" TEXT,
    "mime" TEXT,
    "createdAt" TIMESTAMPTZ DEFAULT NOW(),
    "metadata" JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_users_identifier ON users("identifier");
CREATE INDEX IF NOT EXISTS idx_threads_userId ON threads("userId");
CREATE INDEX IF NOT EXISTS idx_steps_threadId ON steps("threadId");