"""
Gemini Interaction Agent - Main module for backward compatibility.

This module re-exports all public functions from the modularized components
to maintain compatibility with existing code that imports from gemini_interaction_agent.
"""

# Core utilities
from gemini_core import (
    retry_on_rate_limit,
    get_gemini_client,
    get_current_date
)

# Problem extraction prompts
from prompts.problem_extraction import (
    get_enhanced_problem_extraction_prompt,
    get_problem_extraction_prompt
)

# Opportunity prompts
from prompts.opportunity_prompts import (
    get_opportunity_identification_prompt,
    get_opportunity_validation_prompt,
    get_thematic_analysis_prompt,
    get_theme_consolidation_prompt
)

# Solution prompts
from prompts.solution_prompts import (
    get_solution_concept_prompt
)

# Document prompts
from prompts.document_prompts import (
    get_brd_drafter_prompt,
    get_enhanced_brd_drafter_prompt,
    get_prd_drafter_prompt,
    get_enhanced_prd_drafter_prompt,
    get_agile_breakdown_prompt
)

# Lead analysis
from analyzers.lead_analyzer import (
    analyze_lead_with_gemini,
    analyze_lead_with_enhanced_extraction
)

# Theme analysis
from analyzers.theme_analyzer import (
    summarize_common_pain_point,
    consolidate_themes_with_gemini,
    consolidate_themes_second_pass,
    consolidate_themes_second_pass_batched
)

# Opportunity analysis
from analyzers.opportunity_analyzer import (
    identify_opportunity_with_gemini,
    validate_opportunity_with_gemini
)

# Solution generation
from generators.solution_generator import (
    generate_solution_concepts_with_gemini
)

# Document generation
from generators.document_generator import (
    generate_brd_with_gemini,
    draft_brd_with_gemini,
    draft_prd_with_gemini,
    generate_agile_plan_with_gemini
)

# Evidence aggregation
from utils.evidence_aggregator import (
    aggregate_evidence_for_opportunity
)

# Re-export all functions for backward compatibility
__all__ = [
    # Core
    'retry_on_rate_limit',
    'get_gemini_client',
    'get_current_date',
    
    # Prompts
    'get_enhanced_problem_extraction_prompt',
    'get_problem_extraction_prompt',
    'get_opportunity_identification_prompt',
    'get_opportunity_validation_prompt',
    'get_thematic_analysis_prompt',
    'get_theme_consolidation_prompt',
    'get_solution_concept_prompt',
    'get_brd_drafter_prompt',
    'get_enhanced_brd_drafter_prompt',
    'get_prd_drafter_prompt',
    'get_enhanced_prd_drafter_prompt',
    'get_agile_breakdown_prompt',
    
    # Analysis functions
    'analyze_lead_with_gemini',
    'analyze_lead_with_enhanced_extraction',
    'summarize_common_pain_point',
    'consolidate_themes_with_gemini',
    'consolidate_themes_second_pass',
    'consolidate_themes_second_pass_batched',
    'identify_opportunity_with_gemini',
    'validate_opportunity_with_gemini',
    
    # Generation functions
    'generate_solution_concepts_with_gemini',
    'generate_brd_with_gemini',
    'draft_brd_with_gemini',
    'draft_prd_with_gemini',
    'generate_agile_plan_with_gemini',
    
    # Utilities
    'aggregate_evidence_for_opportunity'
]

# Main block for testing
if __name__ == '__main__':
    import json
    
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