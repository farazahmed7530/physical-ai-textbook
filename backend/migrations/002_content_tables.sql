-- Migration 002: Content Tables
-- Creates personalized_content and translated_content tables
-- Requirements: 6.5, 7.4, 8.4

-- Personalized content cache table
CREATE TABLE IF NOT EXISTS personalized_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chapter_id VARCHAR(100) NOT NULL,
    personalized_content TEXT NOT NULL,
    experience_level VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_personalized_user_chapter UNIQUE(user_id, chapter_id)
);

-- Create index on chapter_id for faster lookups
CREATE INDEX IF NOT EXISTS ix_personalized_content_chapter_id ON personalized_content(chapter_id);

-- Translated content cache table
CREATE TABLE IF NOT EXISTS translated_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chapter_id VARCHAR(100) NOT NULL,
    translated_content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'ur' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_translated_chapter_language UNIQUE(chapter_id, language)
);

-- Create index on chapter_id for faster lookups
CREATE INDEX IF NOT EXISTS ix_translated_content_chapter_id ON translated_content(chapter_id);

-- Trigger for personalized_content table
DROP TRIGGER IF EXISTS update_personalized_content_updated_at ON personalized_content;
CREATE TRIGGER update_personalized_content_updated_at
    BEFORE UPDATE ON personalized_content
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for translated_content table
DROP TRIGGER IF EXISTS update_translated_content_updated_at ON translated_content;
CREATE TRIGGER update_translated_content_updated_at
    BEFORE UPDATE ON translated_content
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
