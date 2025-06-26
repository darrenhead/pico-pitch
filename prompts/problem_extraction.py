"""Problem extraction prompts for Gemini interaction."""

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