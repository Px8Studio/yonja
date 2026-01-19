-- Fix Chainlit tables for asyncpg compatibility
-- The createdAt columns need to accept string format

ALTER TABLE users ALTER COLUMN "createdAt" TYPE TEXT;
ALTER TABLE threads ALTER COLUMN "createdAt" TYPE TEXT;
ALTER TABLE steps ALTER COLUMN "createdAt" TYPE TEXT;
ALTER TABLE steps ALTER COLUMN "startTime" TYPE TEXT;
ALTER TABLE steps ALTER COLUMN "endTime" TYPE TEXT;
ALTER TABLE feedbacks ALTER COLUMN "createdAt" TYPE TEXT;
ALTER TABLE elements ALTER COLUMN "createdAt" TYPE TEXT;