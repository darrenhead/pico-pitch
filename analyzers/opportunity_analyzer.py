"""Opportunity identification and validation functions."""

import json
from gemini_core import retry_on_rate_limit
from prompts.opportunity_prompts import get_opportunity_identification_prompt, get_opportunity_validation_prompt


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