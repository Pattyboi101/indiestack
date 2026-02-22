-- Add email column for public (no-login) submissions
ALTER TABLE tools ADD COLUMN submitter_email TEXT;

-- Index for looking up tools by submitter email (for claim flow)
CREATE INDEX IF NOT EXISTS idx_tools_submitter_email ON tools (submitter_email)
    WHERE submitter_email IS NOT NULL;

-- Add IP tracking column
ALTER TABLE tools ADD COLUMN submitted_from_ip TEXT;
