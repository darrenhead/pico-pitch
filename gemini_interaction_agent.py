import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
import time
from functools import wraps
import google.api_core.exceptions
from datetime import datetime

load_dotenv()

def retry_on_rate_limit(max_retries=3, initial_delay=5):
    """A decorator to handle Gemini API rate limiting with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except google.api_core.exceptions.ResourceExhausted as e:
                    retries += 1
                    if retries >= max_retries:
                        print(f"API rate limit exceeded. Max retries reached for function '{func.__name__}'. Failing.")
                        raise e
                    
                    print(f"API rate limit exceeded on '{func.__name__}'. Retrying in {delay} seconds... ({retries}/{max_retries})")
                    time.sleep(delay)
                    delay *= 2 # Exponential backoff
            return None
        return wrapper
    return decorator

def get_gemini_client(model_name='gemini-2.5-pro-preview-06-05'):
    """Initializes and returns a specific Gemini client with timeout configuration."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY must be set in the environment variables.")
    genai.configure(api_key=api_key)
    
    # Configure generation settings for better timeout handling
    generation_config = genai.types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=8192,  # Reasonable limit for most responses
        top_p=0.9,
        top_k=40
    )
    
    return genai.GenerativeModel(model_name, generation_config=generation_config)

def get_enhanced_problem_extraction_prompt():
    """Returns an enhanced prompt that extracts problems with supporting evidence."""
    return """
<extraction_task>
    <input>
        <raw_text>{raw_text}</raw_text>
        <source_metadata>
            <reddit_id>{reddit_id}</reddit_id>
            <permalink>{permalink}</permalink>
            <subreddit>{subreddit}</subreddit>
            <is_comment>{is_comment}</is_comment>
        </source_metadata>
    </input>
    
    <instructions>
        <step id="1">
            <action>Identify the core problem or pain point being expressed</action>
            <fallback>If no clear problem, state "No clear problem"</fallback>
        </step>
        
        <step id="2">
            <action>Extract 1-3 exact quotes that best represent the pain point</action>
            <guidance>Include enough context to understand the quote. Preserve the user's exact words including typos or informal language</guidance>
        </step>
        
        <step id="3">
            <action>Assess the emotional intensity and urgency</action>
            <indicators>
                <high>Words like: desperate, urgent, ASAP, frustrated, fed up, nightmare</high>
                <medium>Words like: struggling, difficult, challenging, need help</medium>
                <low>Words like: wondering, curious, thinking about, considering</low>
            </indicators>
        </step>
        
        <step id="4">
            <action>Identify any financial indicators</action>
            <extract>
                <item>Specific dollar amounts mentioned</item>
                <item>Budget references</item>
                <item>Cost of current pain (losses, wasted money)</item>
                <item>Willingness to pay signals</item>
            </extract>
        </step>
        
        <step id="5">
            <action>Classify the problem domain and SaaS potential</action>
            <guidance>Be specific about the niche or industry</guidance>
        </step>
    </instructions>
    
    <output_specification>
        <format>json</format>
        <schema>
            <field name="problem_summary" type="string" max_length="200" required="true"/>
            <field name="problem_domain" type="string" required="true"/>
            <field name="supporting_quotes" type="array" required="true">
                <item_schema>
                    <field name="text" type="string" required="true"/>
                    <field name="context" type="string" required="false"/>
                </item_schema>
            </field>
            <field name="urgency_level" type="string" values="Low,Medium,High" required="true"/>
            <field name="financial_indicators" type="object" required="true">
                <field name="amounts_mentioned" type="array" item_type="string"/>
                <field name="willing_to_pay" type="string" values="Yes,No,Maybe,Unknown"/>
                <field name="cost_of_problem" type="string" required="false"/>
            </field>
            <field name="saas_potential_flag" type="string" values="Yes,No,Uncertain" required="true"/>
            <field name="source_url" type="string" required="true"/>
        </schema>
    </output_specification>
</extraction_task>
"""

def get_problem_extraction_prompt():
    """Returns the prompt for the Gemini Problem Extractor."""
    return """
<analysis_task>
    <input>
        <raw_text>{raw_text}</raw_text>
    </input>
    
    <instructions>
        <step id="1">
            <action>Identify the core problem or pain point being expressed</action>
            <fallback>If no clear problem, state "No clear problem"</fallback>
        </step>
        
        <step id="2">
            <action>Summarize this problem</action>
            <constraint>1-2 concise sentences maximum</constraint>
        </step>
        
        <step id="3">
            <action>Classify the apparent domain or niche of this problem</action>
            <examples>
                <example>Project Management</example>
                <example>Social Media Marketing</example>
                <example>Restaurant Operations</example>
                <example>Software Development Tooling</example>
                <example>Personal Productivity</example>
                <example>Translation Services</example>
                <example>Digital Signage</example>
            </examples>
            <fallback_if_unclear>General Business Problem OR General Consumer Problem</fallback_if_unclear>
        </step>
        
        <step id="4">
            <action>Assess if this problem seems solvable by a software (SaaS) solution</action>
            <output_values>Yes | No | Uncertain</output_values>
        </step>
        
        <step id="5">
            <action>Estimate the intensity of the user's frustration</action>
            <output_values>Low | Medium | High</output_values>
        </step>
    </instructions>
    
    <output_specification>
        <format>json</format>
        <schema>
            <field name="problem_summary" type="string" max_length="200" required="true"/>
            <field name="problem_domain" type="string" required="true"/>
            <field name="saas_potential_flag" type="string" values="Yes,No,Uncertain" required="true"/>
            <field name="frustration_level" type="string" values="Low,Medium,High" required="true"/>
        </schema>
    </output_specification>
</analysis_task>
    """

def get_opportunity_identification_prompt():
    """Returns the prompt for the Gemini Business Opportunity Identifier."""
    return """
<opportunity_analysis>
    <input>
        <problem_summary>{problem_summary}</problem_summary>
        <problem_domain>{problem_domain}</problem_domain>
    </input>
    
    <instructions>
        <step id="1">
            <action>Describe a potential micro-SaaS or niche SaaS business opportunity that could address this specific problem</action>
            <constraint>Focus on practical, achievable solutions</constraint>
        </step>
        
        <step id="2">
            <action>Identify the primary target user/customer for this SaaS</action>
            <constraint>Be specific about demographics, role, or industry</constraint>
        </step>
        
        <step id="3">
            <action>Define the core value proposition for this SaaS</action>
            <constraint>What unique value does it provide to solve the problem?</constraint>
        </step>
        
        <step id="4">
            <action>Assess domain relevance</action>
            <categories>
                <category>Translation</category>
                <category>Digital Signage</category>
                <category>Menus</category>
                <category>Restaurant tech</category>
                <category>General SaaS Opportunity</category>
            </categories>
            <instruction>Specify which category this opportunity relates to, or state "General SaaS Opportunity" if none apply</instruction>
        </step>
        
        <step id="5">
            <action>Suggest a short, catchy title for this opportunity</action>
            <constraint>Maximum 5 words, memorable and descriptive</constraint>
        </step>
    </instructions>
    
    <output_specification>
        <format>json</format>
        <schema>
            <field name="opportunity_description" type="string" required="true"/>
            <field name="target_user" type="string" required="true"/>
            <field name="value_proposition" type="string" required="true"/>
            <field name="domain_relevance" type="string" required="true"/>
            <field name="opportunity_title" type="string" max_length="50" required="true"/>
        </schema>
    </output_specification>
</opportunity_analysis>
    """

def get_solution_concept_prompt():
    """Returns the prompt for the Gemini Solution Concept Generator."""
    return """
<solution_brainstorming>
    <input>
        <opportunity_description>{opportunity_description}</opportunity_description>
        <target_user>{target_user}</target_user>
        <value_proposition>{value_proposition}</value_proposition>
    </input>
    
    <instructions>
        <task>Brainstorm 1-3 distinct high-level solution concepts for a SaaS product</task>
        <constraints>
            <constraint>Each concept must be unique and differentiated</constraint>
            <constraint>Focus on practical implementation approaches</constraint>
            <constraint>Consider modern SaaS best practices</constraint>
        </constraints>
        
        <for_each_concept>
            <requirement id="1">Give it a conceptual name that reflects its approach</requirement>
            <requirement id="2">List 3-5 core features that define this concept</requirement>
            <requirement id="3">Ensure features are specific and actionable</requirement>
        </for_each_concept>
    </instructions>
    
    <output_specification>
        <format>json_array</format>
        <array_item_schema>
            <field name="concept_name" type="string" required="true"/>
            <field name="core_features" type="array" min_items="3" max_items="5" required="true">
                <item_type>string</item_type>
            </field>
        </array_item_schema>
    </output_specification>
</solution_brainstorming>
    """

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

def get_thematic_analysis_prompt():
    """Returns the prompt for summarizing a collection of related problems."""
    return """
<thematic_analysis_task>
    <input>
        <problem_domain>{problem_domain}</problem_domain>
        <problem_summaries>{problem_summaries}</problem_summaries>
    </input>
    
    <instructions>
        <context>The problem_summaries contain user-expressed problems from the same domain, with each problem on a new line</context>
        <objective>Synthesize these individual problems into a single, overarching pain point or theme</objective>
        
        <step id="1">
            <action>Identify and describe the common, recurring theme or core problem that connects most of these points</action>
            <guidance>Look for patterns, repeated concepts, and underlying frustrations</guidance>
        </step>
        
        <step id="2">
            <action>Provide a consolidated summary of this core problem</action>
            <constraint>Be concise yet comprehensive, capturing the essence of the shared pain point</constraint>
        </step>
        
        <step id="3">
            <action>Suggest a short, catchy title for this consolidated problem theme</action>
            <constraint>Maximum 5-7 words, memorable and descriptive</constraint>
        </step>
    </instructions>
    
    <output_specification>
        <format>json</format>
        <schema>
            <field name="common_theme_description" type="string" required="true"/>
            <field name="consolidated_problem_summary" type="string" required="true"/>
            <field name="theme_title" type="string" max_length="50" required="true"/>
        </schema>
    </output_specification>
</thematic_analysis_task>
    """

def get_opportunity_validation_prompt():
    """Returns a prompt to validate a SaaS opportunity."""
    return """
<opportunity_validation_task>
    <context>
        <role>You are a cynical, but fair, venture capitalist and product strategist</role>
        <objective>Critically evaluate a SaaS opportunity generated from observed user pain points</objective>
    </context>
    
    <input>
        <opportunity_title>{opportunity_title}</opportunity_title>
        <target_user>{target_user}</target_user>
        <value_proposition>{value_proposition}</value_proposition>
        <consolidated_problem>{consolidated_problem}</consolidated_problem>
    </input>
    
    <evaluation_criteria>
        <criterion id="1" name="Monetization Potential">
            <description>How likely is the target user to pay for this solution? Is the pain point strong enough?</description>
            <scale min="1" max="10">
                <level score="1-3">Users unlikely to pay, weak pain point</level>
                <level score="4-6">Some willingness to pay, moderate pain</level>
                <level score="7-10">Strong willingness to pay, significant pain</level>
            </scale>
        </criterion>
        
        <criterion id="2" name="Market Size">
            <description>How large is the potential market? Is it a tiny niche or a broad audience?</description>
            <scale min="1" max="10">
                <level score="1-3">Very small niche, limited growth potential</level>
                <level score="4-6">Moderate market size, reasonable growth</level>
                <level score="7-10">Large market, significant growth potential</level>
            </scale>
        </criterion>
        
        <criterion id="3" name="Feasibility">
            <description>How difficult would it be to build a Minimum Viable Product (MVP) for this?</description>
            <scale min="1" max="10">
                <level score="1-3">Very difficult, complex technical challenges</level>
                <level score="4-6">Moderate difficulty, standard challenges</level>
                <level score="7-10">Relatively easy, straightforward implementation</level>
            </scale>
        </criterion>
        
        <criterion id="4" name="Go/No-Go Recommendation">
            <decision_logic>
                <go_criteria>Scores generally above 6, with at least one score of 8+</go_criteria>
                <no_go_criteria>Any score below 4, or average below 5</no_go_criteria>
            </decision_logic>
            <output_values>Go | No-Go</output_values>
        </criterion>
        
        <criterion id="5" name="Justification">
            <requirement>Provide a brief, crisp justification for your recommendation</requirement>
            <constraint>2-3 sentences maximum, focus on key decision factors</constraint>
        </criterion>
    </evaluation_criteria>
    
    <output_specification>
        <format>json</format>
        <schema>
            <field name="monetization_score" type="integer" min="1" max="10" required="true"/>
            <field name="market_size_score" type="integer" min="1" max="10" required="true"/>
            <field name="feasibility_score" type="integer" min="1" max="10" required="true"/>
            <field name="recommendation" type="string" values="Go,No-Go" required="true"/>
            <field name="justification" type="string" max_length="300" required="true"/>
        </schema>
    </output_specification>
</opportunity_validation_task>
    """

def get_theme_consolidation_prompt():
    """Returns a prompt to consolidate similar thematic domains."""
    return """
<theme_consolidation_task>
    <context>
        <problem>Many 'Problem Domains' identified from user posts are semantically similar or duplicates, just worded differently</problem>
        <objective>Consolidate these domains into canonical themes</objective>
    </context>
    
    <input>
        <domain_list>{domain_list}</domain_list>
    </input>
    
    <instructions>
        <step id="1">
            <action>Group the domains that refer to the same core concept</action>
            <guidance>Look for semantic similarity, related industries, or overlapping problem spaces</guidance>
        </step>
        
        <step id="2">
            <action>Create a concise, canonical theme name for each group</action>
            <constraint>Theme names should be clear, professional, and representative</constraint>
            <example>Automated Content & Community Moderation</example>
        </step>
        
        <step id="3">
            <action>Handle unique domains</action>
            <rule>If a domain is unique and doesn't fit with others, it can be its own group</rule>
        </step>
    </instructions>
    
    <example>
        <input_domains>
            <domain>Community Management / Content Moderation</domain>
            <domain>Online Community Management</domain>
            <domain>Social Media Marketing</domain>
            <domain>Digital Marketing / Content Strategy</domain>
            <domain>Online Community Moderation</domain>
        </input_domains>
        
        <expected_output>
            <theme name="Automated Content & Community Moderation">
                <original_domain>Community Management / Content Moderation</original_domain>
                <original_domain>Online Community Management</original_domain>
                <original_domain>Online Community Moderation</original_domain>
            </theme>
            <theme name="Digital Marketing & Strategy">
                <original_domain>Social Media Marketing</original_domain>
                <original_domain>Digital Marketing / Content Strategy</original_domain>
            </theme>
        </expected_output>
    </example>
    
    <output_specification>
        <format>json</format>
        <structure>Object where keys are canonical theme names and values are arrays of original domain names</structure>
        <example_json>
    {{
        "Automated Content & Community Moderation": [
            "Community Management / Content Moderation",
            "Online Community Management",
            "Online Community Moderation"
        ],
        "Digital Marketing & Strategy": [
            "Social Media Marketing",
            "Digital Marketing / Content Strategy"
        ]
    }}
        </example_json>
    </output_specification>
</theme_consolidation_task>
    """

def get_current_date():
    """Returns the current date in a formatted string."""
    return datetime.now().strftime("%B %d, %Y")

@retry_on_rate_limit()
def analyze_lead_with_gemini(model, lead_text: str):
    """
    Analyzes a single lead's text with Gemini to extract problem details.

    Args:
        model: The Gemini model client.
        lead_text: The raw text from the Reddit lead.

    Returns:
        A dictionary with the extracted problem details, or None if analysis fails.
    """
    if not lead_text or not lead_text.strip():
        return None
        
    prompt = get_problem_extraction_prompt().format(raw_text=lead_text)
    
    try:
        response = model.generate_content(prompt)
        # Clean the response to extract the JSON part using robust method
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result_json = json.loads(response_text)
        return result_json
    except json.JSONDecodeError as e:
        print(f"JSON parsing error analyzing lead with Gemini: {e}")
        print(f"Raw response: {response.text}")
        return None
    except Exception as e:
        print(f"Error analyzing lead with Gemini: {e}")
        print(f"Problematic response: {response.text if 'response' in locals() else 'N/A'}")
        return None

@retry_on_rate_limit()
def summarize_common_pain_point(model, domain: str, summaries: list):
    """
    Analyzes a list of problem summaries to find a common theme using Gemini.

    Args:
        model: The Gemini model client.
        domain: The common domain of the problems.
        summaries: A list of problem summary strings.

    Returns:
        A dictionary with the thematic analysis, or None if analysis fails.
    """
    if not summaries:
        return None

    # Join summaries with a newline for the prompt
    problem_summaries_str = "\\n".join(f"- {s}" for s in summaries)

    prompt = get_thematic_analysis_prompt().format(
        problem_domain=domain,
        problem_summaries=problem_summaries_str
    )

    try:
        response = model.generate_content(prompt)
        # Clean the response to extract the JSON part using robust method
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result_json = json.loads(response_text)
        return result_json
    except json.JSONDecodeError as e:
        print(f"JSON parsing error during thematic analysis with Gemini: {e}")
        print(f"Raw response: {response.text}")
        return None
    except Exception as e:
        print(f"Error during thematic analysis with Gemini: {e}")
        print(f"Problematic response: {response.text if 'response' in locals() else 'N/A'}")
        return None

@retry_on_rate_limit()
def consolidate_themes_with_gemini(model, domain_list: list, batch_size=50, max_domains=200):
    """
    Uses Gemini to consolidate a list of similar domain names into canonical themes.
    Processes in batches to avoid timeouts and limits total domains for efficiency.

    Args:
        model: The Gemini model client.
        domain_list (list): A list of raw domain name strings.
        batch_size (int): Number of domains to process per batch (default: 50).
        max_domains (int): Maximum total domains to process (default: 200).

    Returns:
        A dictionary mapping canonical themes to original domains, or None on failure.
    """
    if not domain_list:
        return None

    # Limit and log domain processing only if necessary
    if len(domain_list) > max_domains:
        print(f"⚡ Large dataset detected: limiting theme consolidation to {max_domains} most common domains (from {len(domain_list)} total)")
        print(f"   💡 To process all domains, increase MAX_DOMAINS_TO_PROCESS in orchestrator.py")
        # Sort by frequency if possible, or just take first N
        domain_list = domain_list[:max_domains]
    else:
        print(f"🔍 Processing all {len(domain_list)} domains found in your data")
    
    # Process in batches to avoid timeouts
    consolidated_result = {}
    total_batches = (len(domain_list) + batch_size - 1) // batch_size
    
    print(f"📦 Processing {len(domain_list)} domains in {total_batches} batches of {batch_size}")
    
    for i in range(0, len(domain_list), batch_size):
        batch = domain_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} domains)...")
        
        prompt = get_theme_consolidation_prompt().format(
            domain_list=json.dumps(batch, indent=2)
        )

        try:
            response = model.generate_content(prompt)
            # Clean the response to extract the JSON part using robust method
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            batch_result = json.loads(response_text)
            
            # Merge batch results
            if isinstance(batch_result, dict):
                consolidated_result.update(batch_result)
                print(f"      ✅ Batch {batch_num} added {len(batch_result)} themes")
            else:
                print(f"⚠️  Warning: Batch {batch_num} returned non-dict result")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error in batch {batch_num}: {e}")
            print(f"Raw response: {response.text}")
            continue
        except Exception as e:
            print(f"❌ Error in batch {batch_num}: {e}")
            continue
    
    if not consolidated_result:
        print("❌ All batches failed. No theme consolidation possible.")
        return None
        
    print(f"📊 First pass: consolidated {len(domain_list)} domains into {len(consolidated_result)} themes")
    
    # SECOND PASS: Consolidate the consolidated themes to catch cross-batch similarities
    if len(consolidated_result) > 1:
        print("🔄 Second pass: consolidating themes across batches...")
        consolidated_theme_names = list(consolidated_result.keys())
        
        # If we have many themes, batch the second pass too
        if len(consolidated_theme_names) <= 50:
            final_consolidation = consolidate_themes_second_pass(model, consolidated_theme_names, consolidated_result)
            if final_consolidation:
                print(f"✅ Final result: {len(domain_list)} domains → {len(final_consolidation)} consolidated themes")
                return final_consolidation
        else:
            print(f"⚠️  Too many themes ({len(consolidated_theme_names)}) for second pass. Using first pass results.")
    
    print(f"✅ Final result: {len(domain_list)} domains → {len(consolidated_result)} themes")
    return consolidated_result

def consolidate_themes_second_pass(model, theme_names, theme_mapping):
    """
    Second pass consolidation to merge similar themes that were separated across batches.
    
    Args:
        model: The Gemini model client
        theme_names: List of consolidated theme names from first pass
        theme_mapping: Original mapping from first pass {theme: [domains]}
        
    Returns:
        Final consolidated mapping or None if failed
    """
    try:
        prompt = get_theme_consolidation_prompt().format(
            domain_list=json.dumps(theme_names, indent=2)
        )
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean response
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        second_pass_result = json.loads(response_text)
        
        # Merge the domain lists based on the second pass consolidation
        final_mapping = {}
        for final_theme, original_themes in second_pass_result.items():
            merged_domains = []
            for original_theme in original_themes:
                if original_theme in theme_mapping:
                    merged_domains.extend(theme_mapping[original_theme])
            final_mapping[final_theme] = merged_domains
            
            # Debug output to show theme merging
            if len(original_themes) > 1:
                print(f"   🔀 Merged themes: {original_themes} → '{final_theme}' ({len(merged_domains)} total domains)")
            
        return final_mapping
        
    except Exception as e:
        print(f"⚠️  Second pass consolidation failed: {e}")
        return None

@retry_on_rate_limit()
def validate_opportunity_with_gemini(model, opportunity: dict):
    """
    Uses Gemini to validate the viability of a SaaS opportunity.

    Args:
        model: The Gemini model client.
        opportunity (dict): The opportunity details.

    Returns:
        A dictionary with the validation analysis, or None if analysis fails.
    """
    if not opportunity:
        return None

    prompt = get_opportunity_validation_prompt().format(
        opportunity_title=opportunity.get('title'),
        target_user=opportunity.get('target_user_ai'),
        value_proposition=opportunity.get('value_proposition_ai'),
        consolidated_problem=opportunity.get('problem_summary_consolidated')
    )

    try:
        response = model.generate_content(prompt)
        # Clean the response to extract the JSON part using robust method
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result_json = json.loads(response_text)
        return result_json
    except json.JSONDecodeError as e:
        print(f"JSON parsing error during opportunity validation with Gemini: {e}")
        print(f"Raw response: {response.text}")
        return None
    except Exception as e:
        print(f"Error during opportunity validation with Gemini: {e}")
        print(f"Problematic response: {response.text if 'response' in locals() else 'N/A'}")
        return None

@retry_on_rate_limit()
def identify_opportunity_with_gemini(model, problem_summary: str, problem_domain: str):
    """
    Analyzes a problem summary with Gemini to identify a business opportunity.

    Args:
        model: The Gemini model client.
        problem_summary: The summary of the problem.
        problem_domain: The domain of the problem.

    Returns:
        A dictionary with the opportunity details, or None if analysis fails.
    """
    if not problem_summary or not problem_domain:
        return None
        
    prompt = get_opportunity_identification_prompt().format(
        problem_summary=problem_summary,
        problem_domain=problem_domain
    )
    
    try:
        response = model.generate_content(prompt)
        # Clean the response to extract the JSON part using robust method
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result_json = json.loads(response_text)
        return result_json
    except json.JSONDecodeError as e:
        print(f"JSON parsing error identifying opportunity with Gemini: {e}")
        print(f"Raw response: {response.text}")
        return None
    except Exception as e:
        print(f"Error identifying opportunity with Gemini: {e}")
        print(f"Problematic response: {response.text if 'response' in locals() else 'N/A'}")
        return None

@retry_on_rate_limit()
def generate_solution_concepts_with_gemini(model, opportunity_description: str, target_user: str, value_proposition: str):
    """
    Generates solution concepts for a given SaaS opportunity.

    Args:
        model: The Gemini model client.
        opportunity_description: The description of the opportunity.
        target_user: The target user for the opportunity.
        value_proposition: The value proposition of the opportunity.

    Returns:
        A list of solution concept dictionaries, or None if analysis fails.
    """
    if not all([opportunity_description, target_user, value_proposition]):
        return None
        
    prompt = get_solution_concept_prompt().format(
        opportunity_description=opportunity_description,
        target_user=target_user,
        value_proposition=value_proposition
    )
    
    try:
        response = model.generate_content(prompt)
        # Clean the response to extract the JSON part using robust method
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result_json = json.loads(response_text)
        return result_json
    except json.JSONDecodeError as e:
        print(f"JSON parsing error generating solution concepts with Gemini: {e}")
        print(f"Raw response: {response.text}")
        return None
    except Exception as e:
        print(f"Error generating solution concepts with Gemini: {e}")
        print(f"Problematic response: {response.text if 'response' in locals() else 'N/A'}")
        return None

def generate_brd_with_gemini(model, pain_point_summary, opportunity_details, selected_concept, use_evidence=True):
    """
    Generates a BRD using either evidence-based or original prompt based on availability.

    Args:
        model: The Gemini model client
        pain_point_summary: The original problem summary
        opportunity_details: The opportunity details dictionary
        selected_concept: The selected solution concept
        use_evidence: Whether to use evidence-based generation if available

    Returns:
        The generated BRD in Markdown format
    """
    if not all([pain_point_summary, opportunity_details, selected_concept]):
        return None

    # Check if we have evidence and should use it
    has_evidence = (
        use_evidence and 
        opportunity_details.get('total_posts_analyzed', 0) > 0 and
        (
            opportunity_details.get('supporting_quotes') or 
            opportunity_details.get('pain_point_frequency', 0) > 0
        )
    )
    
    if has_evidence:
        print("📊 Generating evidence-based BRD with real user quotes...")
        prompt = get_enhanced_brd_drafter_prompt().format(
            current_date=get_current_date(),
            pain_point_summary=pain_point_summary,
            opportunity_title=opportunity_details.get('title'),
            opportunity_description=opportunity_details.get('opportunity_description_ai'),
            target_user=opportunity_details.get('target_user_ai'),
            value_proposition=opportunity_details.get('value_proposition_ai'),
            concept_name=selected_concept.get('concept_name'),
            core_features=selected_concept.get('core_features_json', {}).get('features', []),
            total_posts_analyzed=opportunity_details.get('total_posts_analyzed', 0),
            pain_point_frequency=opportunity_details.get('pain_point_frequency', 0),
            supporting_quotes=json.dumps(opportunity_details.get('supporting_quotes', [])),
            financial_indicators=json.dumps(opportunity_details.get('financial_indicators', {})),
            urgency_distribution=json.dumps(opportunity_details.get('urgency_distribution', {})),
            competitor_mentions=json.dumps(opportunity_details.get('competitor_mentions', [])),
            source_posts=json.dumps(opportunity_details.get('source_posts', []))
        )
    else:
        print("📝 Generating standard BRD...")
        prompt = get_brd_drafter_prompt().format(
            pain_point_summary=pain_point_summary,
            opportunity_title=opportunity_details.get('title'),
            opportunity_description=opportunity_details.get('opportunity_description_ai'),
            target_user=opportunity_details.get('target_user_ai'),
            value_proposition=opportunity_details.get('value_proposition_ai'),
            concept_name=selected_concept.get('concept_name'),
            core_features=selected_concept.get('core_features_json', {}).get('features', [])
        )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating BRD with Gemini: {e}")
        return None

@retry_on_rate_limit()
def draft_prd_with_gemini(model, brd_content, selected_concept, opportunity_details, use_evidence=True):
    """
    Drafts a Product Requirements Document (PRD) using Gemini with optional evidence integration.

    Args:
        model: The Gemini model client.
        brd_content (str): The content of the BRD.
        selected_concept (dict): The dictionary for the chosen solution concept.
        opportunity_details (dict): The dictionary containing opportunity details for context.
        use_evidence: Whether to use evidence-based generation if available.

    Returns:
        The generated PRD in Markdown format, or None on failure.
    """
    if not all([brd_content, selected_concept, opportunity_details]):
        return None

    # Check if we have evidence and should use it
    has_evidence = (
        use_evidence and 
        opportunity_details.get('total_posts_analyzed', 0) > 0 and
        (
            opportunity_details.get('supporting_quotes') or 
            opportunity_details.get('pain_point_frequency', 0) > 0
        )
    )

    if has_evidence:
        print("📊 Generating evidence-based PRD with real user validation...")
        prompt = get_enhanced_prd_drafter_prompt().format(
            current_date=get_current_date(),
            brd_markdown_content=brd_content,
            opportunity_title=opportunity_details.get('title'),
            concept_name=selected_concept.get('concept_name'),
            core_features=selected_concept.get('core_features_json', {}).get('features', []),
            total_posts_analyzed=opportunity_details.get('total_posts_analyzed', 0),
            pain_point_frequency=opportunity_details.get('pain_point_frequency', 0),
            supporting_quotes=json.dumps(opportunity_details.get('supporting_quotes', [])),
            financial_indicators=json.dumps(opportunity_details.get('financial_indicators', {})),
            urgency_distribution=json.dumps(opportunity_details.get('urgency_distribution', {})),
            competitor_mentions=json.dumps(opportunity_details.get('competitor_mentions', []))
        )
    else:
        print("📝 Generating standard PRD...")
        prompt = get_prd_drafter_prompt().format(
            brd_markdown_content=brd_content,
            opportunity_title=opportunity_details.get('title'),
            concept_name=selected_concept.get('concept_name'),
            core_features=selected_concept.get('core_features_json', {}).get('features', [])
        )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error drafting PRD with Gemini: {e}")
        return None

@retry_on_rate_limit()
def generate_agile_plan_with_gemini(model, prd_content):
    """
    Generates a detailed Agile plan from a PRD using Gemini.

    Args:
        model: The Gemini model client.
        prd_content (str): The content of the PRD.

    Returns:
        The generated Agile plan in Markdown format, or None on failure.
    """
    if not prd_content:
        return None

    prompt = get_agile_breakdown_prompt().format(
        prd_markdown_content=prd_content
    )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating Agile plan with Gemini: {e}")
        return None

def aggregate_evidence_for_opportunity(leads_data):
    """
    Aggregates evidence from multiple leads to provide market validation data.
    
    Args:
        leads_data: List of analyzed leads with their extracted problems and evidence
        
    Returns:
        Dictionary containing aggregated evidence metrics
    """
    evidence = {
        'total_posts_analyzed': len(leads_data),
        'supporting_quotes': [],
        'financial_indicators': {
            'amounts_mentioned': [],
            'willing_to_pay_counts': {'Yes': 0, 'No': 0, 'Maybe': 0, 'Unknown': 0},
            'total_cost_of_problems': []
        },
        'urgency_distribution': {'High': 0, 'Medium': 0, 'Low': 0},
        'competitor_mentions': {},
        'pain_point_frequency': 0,
        'source_links': [],
        'source_posts': []  # Enhanced source information
    }
    
    for lead in leads_data:
        analysis = lead.get('analysis', {})
        
        # Skip if no clear problem
        if analysis.get('problem_summary', '').lower() == 'no clear problem':
            continue
            
        evidence['pain_point_frequency'] += 1
        
        # Collect detailed source post information
        if lead.get('permalink'):
            source_post = {
                'reddit_url': f"https://reddit.com{lead.get('permalink', '')}",
                'permalink': lead.get('permalink', ''),
                'title': lead.get('title', 'Untitled'),
                'subreddit': lead.get('subreddit', 'unknown'),
                'author': lead.get('author', '[deleted]'),
                'is_comment': lead.get('is_comment', False),
                'problem_summary': analysis.get('problem_summary', ''),
                'urgency_level': analysis.get('urgency_level', 'Low'),
                'financial_impact': analysis.get('financial_indicators', {}).get('cost_of_problem', ''),
                'supporting_quotes': analysis.get('supporting_quotes', [])
            }
            evidence['source_posts'].append(source_post)
        
        # Collect quotes
        quotes = analysis.get('supporting_quotes', [])
        for quote in quotes:
            if isinstance(quote, dict):
                evidence['supporting_quotes'].append({
                    'text': quote.get('text', ''),
                    'context': quote.get('context', ''),
                    'source': lead.get('permalink', ''),
                    'reddit_url': f"https://reddit.com{lead.get('permalink', '')}" if lead.get('permalink') else '',
                    'author': lead.get('author', '[deleted]'),
                    'subreddit': lead.get('subreddit', 'unknown')
                })
        
        # Aggregate financial indicators
        financial = analysis.get('financial_indicators', {})
        if financial:
            amounts = financial.get('amounts_mentioned', [])
            evidence['financial_indicators']['amounts_mentioned'].extend(amounts)
            
            willing = financial.get('willing_to_pay', 'Unknown')
            if willing not in evidence['financial_indicators']['willing_to_pay_counts']:
                evidence['financial_indicators']['willing_to_pay_counts'][willing] = 0
            evidence['financial_indicators']['willing_to_pay_counts'][willing] += 1
            
            cost_of_problem = financial.get('cost_of_problem', '')
            if cost_of_problem:
                evidence['financial_indicators']['total_cost_of_problems'].append(cost_of_problem)
        
        # Count urgency levels (handle any unexpected values gracefully)
        urgency = analysis.get('urgency_level', 'Low')
        if urgency not in evidence['urgency_distribution']:
            evidence['urgency_distribution'][urgency] = 0
        evidence['urgency_distribution'][urgency] += 1
        
        # Track source links (maintaining backwards compatibility)
        if lead.get('permalink'):
            evidence['source_links'].append(lead.get('permalink'))
        
        # Extract competitor mentions (simple keyword search for now)
        text = lead.get('content', '').lower()
        competitors = ['upwork', 'toptal', 'fiverr', 'freelancer', 'guru', '99designs']
        for comp in competitors:
            if comp in text:
                evidence['competitor_mentions'][comp] = evidence['competitor_mentions'].get(comp, 0) + 1
    
    # Calculate percentages
    if evidence['total_posts_analyzed'] > 0:
        evidence['pain_point_percentage'] = round(
            (evidence['pain_point_frequency'] / evidence['total_posts_analyzed']) * 100, 1
        )
    else:
        evidence['pain_point_percentage'] = 0
    
    return evidence

@retry_on_rate_limit()
def analyze_lead_with_enhanced_extraction(model, lead_data):
    """
    Analyzes a Reddit lead using the enhanced extraction prompt that captures evidence.
    
    Args:
        model: The Gemini model instance
        lead_data: Dictionary containing lead information including content, permalink, etc.
        
    Returns:
        Dictionary containing the analysis with evidence
    """
    prompt = get_enhanced_problem_extraction_prompt().format(
        raw_text=lead_data.get('content', ''),
        reddit_id=lead_data.get('reddit_id', ''),
        permalink=lead_data.get('permalink', ''),
        subreddit=lead_data.get('subreddit', ''),
        is_comment=str(lead_data.get('is_comment', False))
    )
    
    response = model.generate_content(prompt)
    
    try:
        # Clean the response text
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        # Add source URL from lead data
        analysis = json.loads(response_text)
        if lead_data.get('permalink'):
            analysis['source_url'] = f"https://reddit.com{lead_data.get('permalink')}"
        
        return analysis
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in enhanced extraction: {e}")
        print(f"Raw response: {response.text}")
        return {
            'problem_summary': 'Error parsing response',
            'problem_domain': 'Unknown',
            'supporting_quotes': [],
            'urgency_level': 'Low',
            'financial_indicators': {
                'amounts_mentioned': [],
                'willing_to_pay': 'Unknown'
            },
            'saas_potential_flag': 'Uncertain',
            'source_url': lead_data.get('permalink', '')
        }

@retry_on_rate_limit()
def draft_brd_with_gemini(model, pain_point_summary, opportunity_details, selected_concept):
    """
    Legacy function - calls generate_brd_with_gemini for backwards compatibility.
    Uses the original (non-evidence) mode by default.
    """
    return generate_brd_with_gemini(model, pain_point_summary, opportunity_details, selected_concept, use_evidence=False)

if __name__ == '__main__':
    try:
        gemini_model = get_gemini_client()
        print("Gemini client created successfully.")
        
        # Example Usage:
        example_text = "I'm so tired of manually tracking my expenses in a spreadsheet. It's tedious and I always make mistakes. I wish there was a simple app that could connect to my bank and categorize everything automatically."
        
        analysis = analyze_lead_with_gemini(gemini_model, example_text)
        
        if analysis:
            print("\nAnalysis Result:")
            print(json.dumps(analysis, indent=2))

            # Example for opportunity identification
            opportunity = identify_opportunity_with_gemini(
                gemini_model,
                analysis['problem_summary'],
                analysis['problem_domain']
            )
            if opportunity:
                print("\nOpportunity Identified:")
                print(json.dumps(opportunity, indent=2))

                # Example for solution concept generation
                concepts = generate_solution_concepts_with_gemini(
                    gemini_model,
                    opportunity['opportunity_description'],
                    opportunity['target_user'],
                    opportunity['value_proposition']
                )
                if concepts:
                    print("\nSolution Concepts Generated:")
                    print(json.dumps(concepts, indent=2))

                    # Example for BRD drafting
                    brd = generate_brd_with_gemini(
                        gemini_model,
                        analysis['problem_summary'],
                        {
                            'opportunity_description_ai': opportunity['opportunity_description'],
                            'target_user_ai': opportunity['target_user'],
                            'value_proposition_ai': opportunity['value_proposition'],
                        },
                        concepts[0] # Using the first concept for the example
                    )
                    if brd:
                        print("\nBRD Drafted:")
                        print(brd)

                        # Example for PRD drafting
                        prd = draft_prd_with_gemini(gemini_model, brd, concepts[0], opportunity)
                        if prd:
                            print("\nPRD Drafted:")
                            print(prd)

                            # Example for Agile Plan generation
                            agile_plan = generate_agile_plan_with_gemini(gemini_model, prd)
                            if agile_plan:
                                print("\nAgile Plan Generated:")
                                print(agile_plan)
                            else:
                                print("\nAgile plan generation failed.")
                        else:
                            print("\nPRD drafting failed.")
                    else:
                        print("\nBRD drafting failed.")
                else:
                    print("\nSolution concept generation failed.")
            else:
                print("\nOpportunity identification failed.")
        else:
            print("\nAnalysis failed.")

    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}") 