"""Opportunity-related prompts for Gemini interaction."""

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