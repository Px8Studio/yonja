-- ============================================
-- Chainlit Data Layer Schema
-- ============================================
-- This script creates/recreates all tables required by
-- Chainlit's SQLAlchemyDataLayer for conversation persistence.
--
-- Tables:
--   users      - OAuth user identity (email from Google OAuth)
--   threads    - Conversation sessions  
--   steps      - Individual messages in conversations
--   elements   - File attachments and media
--   feedbacks  - User feedback (thumbs up/down)
--
-- Usage:
--   psql -h localhost -p 5433 -U yonca -d yonca -f scripts/chainlit/init_tables.sql
--
-- Note: This is SAFE to run multiple times (uses IF NOT EXISTS / IF EXISTS)
-- ============================================

-- Drop existing tables (cascade to remove dependencies)
-- Comment out these lines if you want to preserve existing data
DROP TABLE IF EXISTS feedbacks CASCADE;
DROP TABLE IF EXISTS elements CASCADE;
DROP TABLE IF EXISTS steps CASCADE;
DROP TABLE IF EXISTS threads CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================
-- USERS TABLE
-- Stores OAuth user identity for Chainlit
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    "id" VARCHAR(36) PRIMARY KEY,
    "identifier" VARCHAR(255) NOT NULL UNIQUE,
    "createdAt" VARCHAR(30) NOT NULL,
    "metadata" TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_users_identifier ON users("identifier");

COMMENT ON TABLE users IS 'Chainlit OAuth users (separate from user_profiles)';
COMMENT ON COLUMN users.id IS 'UUID primary key';
COMMENT ON COLUMN users.identifier IS 'User email from OAuth provider';
COMMENT ON COLUMN users."createdAt" IS 'ISO timestamp of creation';
COMMENT ON COLUMN users.metadata IS 'JSON metadata including chat_settings';

-- ============================================
-- THREADS TABLE
-- Stores conversation threads/sessions
-- ============================================
CREATE TABLE IF NOT EXISTS threads (
    "id" VARCHAR(36) PRIMARY KEY,
    "createdAt" VARCHAR(30),
    "name" VARCHAR(255),
    "userId" VARCHAR(36),
    "userIdentifier" VARCHAR(255),  -- Required by Chainlit 2.x
    "tags" TEXT,
    "metadata" TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_threads_userId ON threads("userId");
CREATE INDEX IF NOT EXISTS ix_threads_userIdentifier ON threads("userIdentifier");

COMMENT ON TABLE threads IS 'Chainlit conversation threads';
COMMENT ON COLUMN threads.id IS 'UUID primary key';
COMMENT ON COLUMN threads."userId" IS 'FK to users.id';
COMMENT ON COLUMN threads."userIdentifier" IS 'Denormalized user email for queries';
COMMENT ON COLUMN threads.tags IS 'JSON array of tags';

-- ============================================
-- STEPS TABLE
-- Stores individual messages/steps in conversations
-- ============================================
CREATE TABLE IF NOT EXISTS steps (
    "id" VARCHAR(36) PRIMARY KEY,
    "name" VARCHAR(255),
    "type" VARCHAR(50),
    "threadId" VARCHAR(36),
    "parentId" VARCHAR(36),
    "streaming" BOOLEAN,
    "waitForAnswer" BOOLEAN,
    "isError" BOOLEAN,
    "metadata" TEXT,
    "tags" TEXT,
    "input" TEXT,
    "output" TEXT,
    "createdAt" VARCHAR(30),
    "start" VARCHAR(30),
    "end" VARCHAR(30),
    "generation" TEXT,
    "showInput" VARCHAR(10),
    "language" VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS ix_steps_threadId ON steps("threadId");

COMMENT ON TABLE steps IS 'Individual messages/steps in Chainlit threads';
COMMENT ON COLUMN steps."threadId" IS 'FK to threads.id';
COMMENT ON COLUMN steps.generation IS 'JSON generation metadata (tokens, model, etc)';

-- ============================================
-- ELEMENTS TABLE
-- Stores file attachments and media
-- ============================================
CREATE TABLE IF NOT EXISTS elements (
    "id" VARCHAR(36) PRIMARY KEY,
    "threadId" VARCHAR(36),
    "type" VARCHAR(50),
    "chainlitKey" VARCHAR(255),
    "url" TEXT,
    "objectKey" VARCHAR(500),
    "name" VARCHAR(255),
    "display" VARCHAR(50),
    "size" VARCHAR(50),
    "language" VARCHAR(50),
    "page" INTEGER,
    "autoPlay" BOOLEAN,
    "playerConfig" TEXT,
    "forId" VARCHAR(36),
    "mime" VARCHAR(100),
    "props" TEXT
);

CREATE INDEX IF NOT EXISTS ix_elements_threadId ON elements("threadId");
CREATE INDEX IF NOT EXISTS ix_elements_forId ON elements("forId");

COMMENT ON TABLE elements IS 'File attachments and media in Chainlit';
COMMENT ON COLUMN elements."threadId" IS 'FK to threads.id';
COMMENT ON COLUMN elements."forId" IS 'Associated step ID';

-- ============================================
-- FEEDBACKS TABLE
-- Stores user feedback on steps (thumbs up/down)
-- ============================================
CREATE TABLE IF NOT EXISTS feedbacks (
    "id" VARCHAR(36) PRIMARY KEY,
    "forId" VARCHAR(36),
    "threadId" VARCHAR(36),
    "value" INTEGER,
    "comment" TEXT
);

CREATE INDEX IF NOT EXISTS ix_feedbacks_forId ON feedbacks("forId");
CREATE INDEX IF NOT EXISTS ix_feedbacks_threadId ON feedbacks("threadId");

COMMENT ON TABLE feedbacks IS 'User feedback on Chainlit steps';
COMMENT ON COLUMN feedbacks."forId" IS 'Step ID this feedback is for';
COMMENT ON COLUMN feedbacks.value IS 'Feedback value (1=positive, -1=negative)';

-- ============================================
-- VERIFICATION
-- ============================================
SELECT 
    'Chainlit tables initialized successfully!' AS status,
    (SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_name IN ('users', 'threads', 'steps', 'elements', 'feedbacks')
     AND table_schema = 'public') AS tables_created;
