"""Solution generation prompts for Gemini interaction."""

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