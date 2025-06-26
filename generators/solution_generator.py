"""Solution concept generation functions."""

import json
from gemini_core import retry_on_rate_limit
from prompts.solution_prompts import get_solution_concept_prompt


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