"""Document generation prompts for Gemini interaction."""

def get_brd_drafter_prompt():
    """Returns the prompt for the Gemini BRD Drafter."""
    return """
<brd_generation_task>
    <context>
        <role>You are an exceptionally skilled Senior Technical Product Manager tasked with creating a comprehensive Business Requirements Document (BRD)</role>
        <purpose>This BRD will serve as the foundational business case and guide for developing a new SaaS product</purpose>
        <knowledge_base>Your insights should reflect an understanding of modern SaaS business models and market contexts, as if informed by broad industry knowledge (akin to what a "Context7 MCP" might provide on business strategy)</knowledge_base>
    </context>
    
    <input_data>
        <opportunity_title>{opportunity_title}</opportunity_title>
        <pain_point_summary>{pain_point_summary}</pain_point_summary>
        <opportunity_description>{opportunity_description}</opportunity_description>
        <target_user>{target_user}</target_user>
        <value_proposition>{value_proposition}</value_proposition>
        <concept_name>{concept_name}</concept_name>
        <core_features>{core_features}</core_features>
    </input_data>
    
    <sections_to_include>
        <section id="1" name="Stakeholder & User Deep Dive">
            <requirements>
                <requirement>Identify Key Stakeholders (e.g., Development Lead, Marketing, Sales, CEO)</requirement>
                <requirement>Outline their primary interest/concern</requirement>
                <requirement>Elaborate on 1-2 detailed User Personas based on target_user</requirement>
            </requirements>
            <persona_details>
                <detail>Demographics/Role</detail>
                <detail>Goals</detail>
                <detail>Pain Points related to pain_point_summary</detail>
                <detail>Motivations</detail>
                <detail>Technical proficiency</detail>
            </persona_details>
        </section>
        
        <section id="2" name="Value Proposition & Competitive Differentiation">
            <framework>Value Proposition Canvas Framework</framework>
            <customer_profile>
                <element>Customer Jobs</element>
                <element>Pains (expand on pain_point_summary)</element>
                <element>Gains</element>
            </customer_profile>
            <value_map>
                <element>Products & Services (how core_features address jobs)</element>
                <element>Pain Relievers</element>
                <element>Gain Creators</element>
            </value_map>
            <requirement>Clearly articulate 2-3 Unique Selling Points (USPs)</requirement>
        </section>
        
        <section id="3" name="Business Model & Market Context">
            <framework>Business Model Canvas Insights, informed by "Context7 MCP"-like knowledge</framework>
            <elements>
                <element>Key Customer Segments</element>
                <element>Revenue Streams (Hypothesized: e.g., subscription tiers via Stripe; consider modern SaaS pricing models from "Context7 MCP")</element>
                <element>Cost Structure (High-Level: Development, Marketing, Infrastructure - Supabase, Vercel, Clerk, Resend, Gemini API)</element>
                <element>Brief Competitive Landscape Overview</element>
            </elements>
        </section>
        
        <section id="4" name="Business Requirements Definition & Prioritization">
            <framework>MoSCoW Framework</framework>
            <task>Translate core_features into clear, high-level Business Requirements</task>
            <priorities>
                <priority>Must have</priority>
                <priority>Should have</priority>
                <priority>Could have</priority>
                <priority>Won't have for this version</priority>
            </priorities>
        </section>
        
        <section id="5" name="Risk & Assumption Analysis">
            <swot_analysis>
                <element>Strengths</element>
                <element>Weaknesses</element>
                <element>Opportunities</element>
                <element>Threats</element>
            </swot_analysis>
            <critical_items>
                <requirement>List 2-3 critical risks (e.g., "User adoption", "Technical challenge")</requirement>
                <requirement>List key assumptions (e.g., "Willingness to pay X", "Feasibility of Y integration")</requirement>
            </critical_items>
        </section>
        
        <section id="6" name="Success Metrics & Key Performance Indicators">
            <requirement>Propose 3-5 quantifiable success metrics</requirement>
            <metric_examples>
                <example>MAU (Monthly Active Users)</example>
                <example>Trial Conversion Rate</example>
                <example>LTV (Lifetime Value)</example>
                <example>Churn Rate</example>
                <example>NPS (Net Promoter Score)</example>
            </metric_examples>
            <requirement>Explain relevance of each metric</requirement>
        </section>
    </sections_to_include>
    
    <output_specification>
        <format>markdown</format>
        <style>well-structured, professional, clear, persuasive</style>
        <constraint>Output ONLY the Markdown. Do not wrap it in a JSON object or backticks</constraint>
    </output_specification>
</brd_generation_task>
"""

def get_enhanced_brd_drafter_prompt():
    """Returns an enhanced BRD prompt that incorporates real user evidence."""
    return """
<brd_generation_task>
    <context>
        <role>You are an exceptionally skilled Senior Technical Product Manager creating an evidence-based Business Requirements Document (BRD)</role>
        <purpose>This BRD will serve as the foundational business case, grounded in real user feedback and market evidence</purpose>
        <date>{current_date}</date>
    </context>
    
    <input_data>
        <opportunity_title>{opportunity_title}</opportunity_title>
        <pain_point_summary>{pain_point_summary}</pain_point_summary>
        <opportunity_description>{opportunity_description}</opportunity_description>
        <target_user>{target_user}</target_user>
        <value_proposition>{value_proposition}</value_proposition>
        <concept_name>{concept_name}</concept_name>
        <core_features>{core_features}</core_features>
        
        <market_evidence>
            <total_posts_analyzed>{total_posts_analyzed}</total_posts_analyzed>
            <pain_point_frequency>{pain_point_frequency}</pain_point_frequency>
            <supporting_quotes>{supporting_quotes}</supporting_quotes>
            <financial_indicators>{financial_indicators}</financial_indicators>
            <urgency_distribution>{urgency_distribution}</urgency_distribution>
            <competitor_mentions>{competitor_mentions}</competitor_mentions>
            <source_posts>{source_posts}</source_posts>
        </market_evidence>
    </input_data>
    
    <instructions>
        <step id="1" name="Executive Summary with Evidence">
            <action>Write executive summary that opens with compelling user evidence</action>
            <guidance>Start with a powerful quote or statistic from the Reddit analysis. If no direct quotes are available, use the pain point frequency and user analysis data to demonstrate market demand</guidance>
        </step>
        
        <step id="2" name="User Personas with Real Quotes">
            <action>Create 1-2 personas based on actual user patterns</action>
            <requirements>
                <requirement>Include real quotes under "Voice of the Customer" if available, otherwise reference the pain point patterns and urgency levels</requirement>
                <requirement>Link pain points to general community discussions even if specific quotes aren't available</requirement>
                <requirement>Use actual financial impacts mentioned by users or reference the urgency distribution</requirement>
            </requirements>
        </step>
        
        <step id="3" name="Value Proposition with Market Validation">
            <action>Define value proposition with evidence of demand</action>
            <include>
                <item>Number of users expressing this need (total_posts_analyzed and pain_point_frequency)</item>
                <item>Current costs/losses users are experiencing (from financial_indicators)</item>
                <item>Competitor gaps identified by real users or reflected in community discussions</item>
            </include>
        </step>
        
        <step id="4" name="Requirements with User Justification">
            <action>List requirements with traceable user evidence</action>
            <format>
                <requirement>
                    <id>BR-XX</id>
                    <description>The requirement description</description>
                    <user_evidence>Quote or data point justifying this requirement. If no direct quotes available, reference community patterns and urgency levels</user_evidence>
                    <source>Reddit discussion patterns or specific post references when available</source>
                </requirement>
            </format>
        </step>
        
        <step id="5" name="Success Metrics Based on User Needs">
            <action>Define KPIs that directly address identified pain points</action>
            <link_to_evidence>Show how each metric relates to user-expressed problems</link_to_evidence>
        </step>
        
        <step id="6" name="Source Evidence Table">
            <action>Create a comprehensive table showing all Reddit posts that provided evidence for this opportunity</action>
            <requirements>
                <requirement>Include clickable Reddit links so readers can visit the original posts</requirement>
                <requirement>Show post titles, subreddits, authors, and problem summaries</requirement>
                <requirement>Note the urgency level and any financial impact mentioned</requirement>
                <requirement>Indicate whether it's a post or comment</requirement>
                <requirement>Add a note that readers can contact these users directly to validate the idea or gather feedback</requirement>
            </requirements>
            <table_format>
                <columns>
                    <column>Post Type</column>
                    <column>Title/Context</column>
                    <column>Author</column>
                    <column>Subreddit</column>
                    <column>Problem Summary</column>
                    <column>Urgency</column>
                    <column>Financial Impact</column>
                    <column>Reddit Link</column>
                </columns>
            </table_format>
            <note>Add explanatory text that this table provides direct access to the source conversations, enabling readers to verify the market demand and potentially reach out to these users for further validation or early customer conversations</note>
        </step>
    </instructions>
    
    <output_format>
        <structure>Professional Business Requirements Document in Markdown</structure>
        <evidence_integration>Seamlessly weave quotes and data throughout</evidence_integration>
        <citation_style>Include Reddit post IDs and links as inline references</citation_style>
        <source_table>Create a dedicated markdown table for source evidence with clickable links</source_table>
    </output_format>
</brd_generation_task>
    """

def get_prd_drafter_prompt():
    """Returns the prompt for the Gemini PRD Drafter."""
    return """
<prd_generation_task>
    <context>
        <role>You are an expert Senior Technical Product Manager responsible for translating business needs into actionable product specifications</role>
        <purpose>Create a comprehensive Product Requirements Document (PRD) based on the provided Business Requirements Document (BRD) and solution concept</purpose>
        <mcp_reference>Act as if you are referencing the latest best practices from the "Context7 MCP" (Model Context Protocol) for authoritative documentation and patterns</mcp_reference>
    </context>
    
    <input_data>
        <brd_content>{brd_markdown_content}</brd_content>
        <concept_name>{concept_name}</concept_name>
        <core_features>{core_features}</core_features>
        <opportunity_title>{opportunity_title}</opportunity_title>
    </input_data>
    
    <technology_stack>
        <framework>Next.js (App Router paradigm exclusively)</framework>
        <authentication>Clerk</authentication>
        <ui_components>Shadcn/ui & Tailwind CSS</ui_components>
        <database>Supabase PostgreSQL (for application-specific data)</database>
        <email>Resend (for transactional emails)</email>
        <deployment>Vercel</deployment>
        <form_handling>react-hook-form with zod</form_handling>
        <state_management>Zustand (only for complex global states)</state_management>
    </technology_stack>
    
    <sections_to_include>
        <section id="1" name="Feature Definition, Elaboration & Prioritization">
            <framework>Kano Model Application</framework>
            <task>From BRD's requirements and core_features, expand into detailed product features</task>
            <classifications>
                <classification>Basic (Must-have features)</classification>
                <classification>Performance (Linear satisfaction features)</classification>
                <classification>Excitement (Delighter features)</classification>
            </classifications>
        </section>
        
        <section id="2" name="Detailed Functional & Non-Functional Requirements">
            <functional_requirements>
                <description>Precise "what the system will do"</description>
                <constraint>Must be testable and measurable</constraint>
            </functional_requirements>
            <non_functional_requirements>
                <nfr category="Performance">
                    <item>Next.js LCP targets</item>
                    <item>Server Action response times</item>
                </nfr>
                <nfr category="Scalability">
                    <item>Supabase query optimization</item>
                    <item>Vercel serverless function limits</item>
                </nfr>
                <nfr category="Security">
                    <item>Clerk authentication patterns</item>
                    <item>Supabase RLS policies</item>
                    <item>OWASP principles as per Context7 MCP for Next.js</item>
                </nfr>
                <nfr category="Usability/Accessibility">
                    <item>Shadcn/ui best practices</item>
                    <item>WCAG 2.1 AA from Context7 MCP</item>
                </nfr>
                <nfr category="Reliability/Availability">
                    <item>Vercel/Supabase/Clerk uptimes</item>
                </nfr>
                <nfr category="Maintainability">
                    <item>Code organization standards</item>
                </nfr>
            </non_functional_requirements>
        </section>
        
        <section id="3" name="User Workflows & Journeys">
            <approach>User Story Mapping</approach>
            <structure>Activities -> Tasks -> User Stories (high-level)</structure>
            <requirement>Identify key user activities and create User Story Map backbone for 2-3 major workflows</requirement>
        </section>
        
        <section id="4" name="Conceptual Technical Architecture & Considerations">
            <architecture_diagram>
                <layer>Frontend Client (Next.js on Vercel)</layer>
                <layer>Next.js Server Actions (Vercel Functions)</layer>
                <layer>Services: Clerk (auth) / Supabase (DB) / Resend (email)</layer>
            </architecture_diagram>
            <data_model>
                <tables>
                    <table name="app_users">
                        <purpose>Link clerk_user_id to app-specific profile data</purpose>
                    </table>
                    <table name="projects" />
                    <table name="documents" />
                </tables>
                <requirements>
                    <requirement>Define key columns, relationships, UUIDs</requirement>
                    <requirement>Identify potential indexes</requirement>
                </requirements>
            </data_model>
            <authentication_flow>
                <description>User sign-up/login/session management using Clerk Next.js SDK, middleware, and components</description>
            </authentication_flow>
            <email_strategy>
                <types>Welcome, password reset, notifications</types>
                <trigger>Server Actions via Resend SDK</trigger>
                <templating>React Email for template management</templating>
            </email_strategy>
        </section>
        
        <section id="5" name="Acceptance Criteria">
            <format>Gherkin Syntax (Given-When-Then)</format>
            <requirement>Write clear Gherkin acceptance criteria for 3-5 core functional requirements/user stories</requirement>
        </section>
        
        <section id="6" name="Release Planning">
            <approach>Phased Approach</approach>
            <phases>
                <phase>MVP - Minimum Viable Product</phase>
                <phase>R1.1 - First Enhancement Release</phase>
            </phases>
            <requirement>Map key features per phase from Kano analysis</requirement>
        </section>
        
        <section id="7" name="RAID Log">
            <categories>
                <category>Risks</category>
                <category>Assumptions</category>
                <category>Issues</category>
                <category>Dependencies</category>
            </categories>
            <examples>
                <example>Integration complexity of Clerk with Supabase for user data sync</example>
                <example>Resend deliverability monitoring</example>
            </examples>
        </section>
    </sections_to_include>
    
    <output_specification>
        <format>markdown</format>
        <style>exceptionally clear, well-organized</style>
        <alignment>All technical descriptions must align with Context7 MCP for the specified stack</alignment>
        <constraint>Output ONLY the Markdown. Do not wrap it in a JSON object or backticks</constraint>
    </output_specification>
</prd_generation_task>
    """

def get_enhanced_prd_drafter_prompt():
    """Returns an enhanced PRD prompt that incorporates real user evidence."""
    return """
<prd_generation_task>
    <context>
        <role>You are an expert Senior Technical Product Manager creating an evidence-based Product Requirements Document (PRD)</role>
        <purpose>Translate business needs into actionable product specifications grounded in real user feedback</purpose>
        <date>{current_date}</date>
        <mcp_reference>Reference latest best practices from "Context7 MCP" for documentation patterns</mcp_reference>
    </context>
    
    <input_data>
        <brd_content>{brd_markdown_content}</brd_content>
        <concept_name>{concept_name}</concept_name>
        <core_features>{core_features}</core_features>
        <opportunity_title>{opportunity_title}</opportunity_title>
        
        <market_evidence>
            <total_posts_analyzed>{total_posts_analyzed}</total_posts_analyzed>
            <pain_point_frequency>{pain_point_frequency}</pain_point_frequency>
            <supporting_quotes>{supporting_quotes}</supporting_quotes>
            <financial_indicators>{financial_indicators}</financial_indicators>
            <urgency_distribution>{urgency_distribution}</urgency_distribution>
            <competitor_mentions>{competitor_mentions}</competitor_mentions>
        </market_evidence>
    </input_data>
    
    <technology_stack>
        <framework>Next.js (App Router paradigm exclusively)</framework>
        <authentication>Clerk</authentication>
        <ui_components>Shadcn/ui & Tailwind CSS</ui_components>
        <database>Supabase PostgreSQL</database>
        <email>Resend</email>
        <deployment>Vercel</deployment>
        <form_handling>react-hook-form with zod</form_handling>
    </technology_stack>
    
    <instructions>
        <step id="1" name="Evidence-Based Feature Prioritization">
            <action>Use Kano Model with user evidence to classify features</action>
            <include_evidence>Quote user pain points that justify each feature priority</include_evidence>
        </step>
        
        <step id="2" name="User Workflows with Real Examples">
            <action>Create user workflows based on actual user behavior patterns</action>
            <requirements>
                <requirement>Reference specific user quotes in acceptance criteria if available, otherwise use community patterns and urgency indicators</requirement>
                <requirement>Include pain points users mentioned in workflow steps, or reference the pain point frequency and urgency distribution</requirement>
                <requirement>Cite Reddit permalinks for traceability when available, otherwise reference community patterns</requirement>
            </requirements>
        </step>
        
        <step id="3" name="Requirements with User Validation">
            <action>Define functional requirements tied to user evidence</action>
            <format>
                <requirement>
                    <id>FR-XX</id>
                    <description>Technical requirement</description>
                    <user_justification>Real user quote or data point. If no direct quotes available, reference pain point frequency, urgency distribution, or financial indicators</user_justification>
                    <source>Reddit link or community pattern reference</source>
                </requirement>
            </format>
        </step>
        
        <step id="4" name="Evidence-Based Acceptance Criteria">
            <action>Write Gherkin scenarios that reflect real user needs</action>
            <guidance>Use actual user language and scenarios from Reddit posts when available, otherwise use common patterns from the community analysis</guidance>
        </step>
        
        <step id="5" name="Success Metrics with Baseline Evidence">
            <action>Define KPIs with current state evidence</action>
            <include>
                <item>Financial impact data from user posts</item>
                <item>Time/efficiency gains users are seeking</item>
                <item>Competitor shortcomings users have identified</item>
            </include>
        </step>
    </instructions>
    
    <output_format>
        <structure>Comprehensive PRD in Markdown with evidence integration</structure>
        <evidence_style>Seamlessly incorporate quotes and data throughout</evidence_style>
        <citations>Include Reddit permalinks as references</citations>
    </output_format>
</prd_generation_task>
    """

def get_agile_breakdown_prompt():
    """Returns the prompt for the Gemini Agile Breakdown Master."""
    return """
<agile_development_plan>
    <context>
        <role>You are an AI Native, "God Tier" Solutions Architect and Principal Engineer</role>
        <directive>Generate an ultra-precise, production-ready, and meticulously detailed development plan</directive>
        <target_consumer>Elite AI Coding Agent embedded within the Cursor IDE</target_consumer>
        <mcp_usage>The AI Agent leverages the Model Context Protocol (MCP) to access latest documentation and best practices</mcp_usage>
        <knowledge_source>Reference "Context7 MCP" as the simulated, authoritative, up-to-the-millisecond knowledge source</knowledge_source>
    </context>
    
    <input_data>
        <prd_content>{prd_markdown_content}</prd_content>
    </input_data>
    
    <technology_stack>
        <framework>
            <name>Next.js</name>
            <paradigm>App Router exclusively</paradigm>
            <mcp_alignment>All Next.js related subtasks must align with patterns derivable from Context7 MCP for Next.js App Router</mcp_alignment>
        </framework>
        <authentication>
            <name>Clerk</name>
            <mcp_alignment>Subtasks MUST specify API calls and component usage based on Context7 MCP for Clerk's Next.js App Router integration</mcp_alignment>
        </authentication>
        <ui_styling>
            <components>Shadcn/ui</components>
            <styling>Tailwind CSS</styling>
            <mcp_alignment>Subtasks must reference specific component names, props, and CLI commands as per Context7 MCP</mcp_alignment>
        </ui_styling>
        <state_management>
            <name>Zustand</name>
            <usage>Only for truly complex global or cross-component client states</usage>
            <preference>Strongly prefer server-derived state, URL state, and local component state</preference>
        </state_management>
        <backend>
            <approach>Next.js Server Actions</approach>
            <database>Supabase PostgreSQL</database>
            <rule>All data mutations (Create, Update, Delete) MUST go through Server Actions</rule>
        </backend>
        <email>
            <service>Resend</service>
            <templating>React Email</templating>
            <mcp_alignment>Reference Context7 MCP for Resend API usage, domain verification, and email template management</mcp_alignment>
        </email>
        <deployment>
            <platform>Vercel</platform>
        </deployment>
        <form_handling>
            <library>react-hook-form</library>
            <validation>zod</validation>
        </form_handling>
    </technology_stack>
    
    <critical_principles>
        <principle id="1" name="SIMULATE AUTHORITATIVE CONTEXT7 MCP KNOWLEDGE ACCESS">
            <description>For EVERY subtask involving core technologies, operate as if you have just queried Context7 MCP</description>
            <requirement>Output MUST reflect up-to-the-millisecond currency and specificity</requirement>
        </principle>
        
        <principle id="2" name="STRICT HIERARCHY & ABSOLUTE GRANULARITY">
            <hierarchy>
                <level1>## Epic</level1>
                <level2>### User Story</level2>
                <level3>#### Task</level3>
                <level4>- [ ] Subtask</level4>
            </hierarchy>
            <constraint>Every subtask MUST be a concrete, atomic, actionable, 1-story-point item</constraint>
        </principle>
        
        <principle id="3" name="TECHNOLOGY-SPECIFIC & EXPLICIT SUBTASKS">
            <example category="Auth/Clerk">
                <subtask>[Auth/Clerk] Initialize Clerk provider in `src/app/layout.tsx` (consult Context7 MCP for Clerk's latest Next.js App Router `<ClerkProvider>` setup and `src/middleware.ts` configuration, including `publicRoutes`)</subtask>
            </example>
            <example category="Backend/Resend">
                <subtask>[Backend/Resend] Create Server Action `sendWelcomeEmail(email: string, userName: string)` in `src/app/actions/email.ts` using Resend SDK (verify Resend API key setup, domain configuration, and `Resend.emails.send()` usage, including React Email template import, via Context7 MCP for Resend)</subtask>
            </example>
            <example category="UI/Shadcn">
                <subtask>[UI/Shadcn] Add `<Button>` and `<Input>` components to project using `npx shadcn-cli@latest add button input` (verify exact command and any dependencies via Context7 MCP for Shadcn)</subtask>
            </example>
        </principle>
        
        <principle id="4" name="NEXT.JS APP ROUTER MASTERY">
            <requirements>
                <requirement>Label Server/Client Components</requirement>
                <requirement>Correctly utilize Layouts, Loading UI (`loading.tsx`), Error UI (`error.tsx`)</requirement>
                <requirement>Route Handlers for webhooks in `src/app/api/.../route.ts`</requirement>
                <requirement>Server Actions in `src/app/actions/...ts`</requirement>
                <requirement>Parallel/Intercepting Routes where applicable</requirement>
            </requirements>
        </principle>
        
        <principle id="5" name="SECURE SERVER-SIDE LOGIC">
            <rules>
                <rule>All CUD database operations MUST be in Next.js Server Actions</rule>
                <rule>Input validation (Zod) is mandatory</rule>
                <rule>Ensure Clerk session data is correctly accessed in Server Actions for authorization</rule>
            </rules>
        </principle>
        
        <principle id="6" name="FLAWLESS UX STATE HANDLING">
            <states>
                <state type="Loading">Shadcn `<Skeleton>`</state>
                <state type="Error">Shadcn `<Toast>`</state>
                <state type="Empty">Custom empty state components</state>
            </states>
        </principle>
        
        <principle id="7" name="METICULOUS INITIAL PROJECT SETUP">
            <setup_tasks>
                <task category="Ops">Create `.nvmrc` with current Node.js LTS (verify via Context7 MCP for Node.js)</task>
                <task category="Ops">Init Next.js: `npx create-next-app@latest pico-seed-app --typescript --tailwind --eslint --app --src-dir` (verify flags via Context7 MCP)</task>
                <task category="Ops">Init Shadcn/ui: `npx shadcn-cli@latest init` (verify command and configuration via Context7 MCP)</task>
                <task category="Ops">Install core dependencies with latest stable versions</task>
                <task category="Ops">Create `.env.example` with all required environment variables</task>
                <task category="Auth/Clerk">Configure Clerk Next.js SDK with middleware and layout wrapper</task>
                <task category="Backend/Util">Create Supabase SSR clients if using Supabase DB</task>
            </setup_tasks>
            <dependencies>
                <dependency>zod</dependency>
                <dependency>react-hook-form</dependency>
                <dependency>@hookform/resolvers</dependency>
                <dependency>zustand</dependency>
                <dependency>lucide-react</dependency>
                <dependency>date-fns</dependency>
                <dependency>@supabase/ssr</dependency>
                <dependency>@supabase/supabase-js</dependency>
                <dependency>@clerk/nextjs</dependency>
                <dependency>resend</dependency>
                <dependency>react-email</dependency>
                <dependency>@react-email/components</dependency>
                <dependency>@react-email/render</dependency>
            </dependencies>
            <env_variables>
                <variable>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</variable>
                <variable>CLERK_SECRET_KEY</variable>
                <variable>NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in</variable>
                <variable>NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up</variable>
                <variable>NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard</variable>
                <variable>NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard</variable>
                <variable>NEXT_PUBLIC_SUPABASE_URL</variable>
                <variable>NEXT_PUBLIC_SUPABASE_ANON_KEY</variable>
                <variable>SUPABASE_SERVICE_ROLE_KEY</variable>
                <variable>RESEND_API_KEY</variable>
            </env_variables>
        </principle>
        
        <principle id="8" name="EMAIL INTEGRATION WITH RESEND">
            <tasks>
                <task>Create React Email templates in `src/emails/`</task>
                <task>Create Server Actions to trigger email sends</task>
                <task>Implement error handling for email failures</task>
                <task>Set up domain verification on Resend.com</task>
            </tasks>
        </principle>
        
        <principle id="9" name="DATABASE SCHEMA & RLS">
            <condition>If Supabase DB is used</condition>
            <tasks>
                <task>Create migration files in `supabase/migrations`</task>
                <task>Define table schemas with proper types and constraints</task>
                <task>Implement Row Level Security (RLS) policies</task>
            </tasks>
        </principle>
    </critical_principles>
    
    <output_specification>
        <format>markdown</format>
        <structure>Hierarchical task breakdown following Epic -> User Story -> Task -> Subtask</structure>
        <mcp_integration>Heavy emphasis on AI Agent leveraging MCP for latest documentation</mcp_integration>
        <constraint>Output ONLY the Markdown</constraint>
    </output_specification>
</agile_development_plan>
    """