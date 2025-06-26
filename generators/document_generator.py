"""Document generation functions for BRD, PRD, and Agile plans."""

import json
from gemini_core import retry_on_rate_limit, get_current_date
from prompts.document_prompts import (
    get_brd_drafter_prompt,
    get_enhanced_brd_drafter_prompt,
    get_prd_drafter_prompt,
    get_enhanced_prd_drafter_prompt,
    get_agile_breakdown_prompt
)


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
def draft_brd_with_gemini(model, pain_point_summary, opportunity_details, selected_concept):
    """
    Legacy function - calls generate_brd_with_gemini for backwards compatibility.
    Uses the original (non-evidence) mode by default.
    """
    return generate_brd_with_gemini(model, pain_point_summary, opportunity_details, selected_concept, use_evidence=False)


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