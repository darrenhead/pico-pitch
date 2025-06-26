-- PicoPitch Database Schema
-- Run this script in your Supabase SQL editor to set up all required tables

-- Create raw_leads table
CREATE TABLE IF NOT EXISTS raw_leads (
    id BIGSERIAL PRIMARY KEY,
    reddit_id TEXT NOT NULL UNIQUE,
    permalink TEXT,
    subreddit TEXT,
    title TEXT,
    body_text TEXT,
    is_comment BOOLEAN NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'new_raw_lead',
    gemini_problem_summary TEXT,
    gemini_problem_domain TEXT,
    gemini_saas_potential_flag TEXT,
    gemini_frustration_level TEXT,
    enhanced_analysis JSONB,
    has_evidence BOOLEAN DEFAULT FALSE,
    author TEXT,
    score INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    created_utc INTEGER,
    url TEXT,
    session_id TEXT
);

-- Create opportunities table
CREATE TABLE IF NOT EXISTS opportunities (
    id BIGSERIAL PRIMARY KEY,
    based_on_lead_ids BIGINT[],
    title TEXT,
    problem_summary_consolidated TEXT,
    opportunity_description_ai TEXT,
    target_user_ai TEXT,
    value_proposition_ai TEXT,
    domain_relevance_ai TEXT,
    status TEXT DEFAULT 'opportunity_defined',
    selected_solution_concept_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    monetization_score INTEGER,
    market_size_score INTEGER,
    feasibility_score INTEGER,
    recommendation TEXT,
    justification TEXT,
    evidence_json JSONB DEFAULT '{}',
    total_posts_analyzed INTEGER DEFAULT 0,
    pain_point_frequency INTEGER DEFAULT 0,
    session_id TEXT
);

-- Create solution_concepts table
CREATE TABLE IF NOT EXISTS solution_concepts (
    id BIGSERIAL PRIMARY KEY,
    opportunity_id BIGINT REFERENCES opportunities(id),
    concept_name TEXT,
    core_features_json JSONB,
    ai_generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    opportunity_id BIGINT REFERENCES opportunities(id),
    document_type TEXT NOT NULL,
    content_markdown TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    local_file_path TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_raw_leads_status ON raw_leads(status);
CREATE INDEX IF NOT EXISTS idx_raw_leads_reddit_id ON raw_leads(reddit_id);
CREATE INDEX IF NOT EXISTS idx_raw_leads_session_id ON raw_leads(session_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_session_id ON opportunities(session_id);
CREATE INDEX IF NOT EXISTS idx_solution_concepts_opportunity_id ON solution_concepts(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_documents_opportunity_id ON documents(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);