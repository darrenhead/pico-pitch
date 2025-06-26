"""Lead analysis functions for extracting problems from user content."""

import json
from gemini_core import retry_on_rate_limit
from prompts.problem_extraction import get_problem_extraction_prompt, get_enhanced_problem_extraction_prompt


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