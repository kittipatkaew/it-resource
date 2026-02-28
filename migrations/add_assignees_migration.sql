-- SQL Migration: Add assignees field to tasks table for multiple assignees
-- Run this SQL script directly on your PostgreSQL database if flask-migrate is not available

-- Add assignees column as JSONB to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignees JSONB DEFAULT '[]'::jsonb;

-- Migrate existing single assignee data to assignees array
UPDATE tasks 
SET assignees = jsonb_build_array(assignee_name)
WHERE assignee_name IS NOT NULL AND (assignees IS NULL OR assignees = '[]'::jsonb);

-- For tasks without assignee, ensure empty array
UPDATE tasks 
SET assignees = '[]'::jsonb
WHERE assignee_name IS NULL AND assignees IS NULL;

-- Verify the migration
SELECT id, text, assignee_name, assignees FROM tasks LIMIT 10;
