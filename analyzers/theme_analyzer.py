"""Theme analysis and consolidation functions."""

import json
from gemini_core import retry_on_rate_limit
from prompts.opportunity_prompts import get_thematic_analysis_prompt, get_theme_consolidation_prompt


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
    problem_summaries_str = "\n".join(f"- {s}" for s in summaries)

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
        
        # Process second pass in batches if needed, but allow much larger datasets
        if len(consolidated_theme_names) <= 200:
            final_consolidation = consolidate_themes_second_pass(model, consolidated_theme_names, consolidated_result)
            if final_consolidation:
                print(f"✅ Final result: {len(domain_list)} domains → {len(final_consolidation)} consolidated themes")
                return final_consolidation
        else:
            # For very large datasets, process in batches for second pass too
            print(f"🔄 Large theme set ({len(consolidated_theme_names)} themes) - processing second pass in batches...")
            final_consolidation = consolidate_themes_second_pass_batched(model, consolidated_theme_names, consolidated_result)
            if final_consolidation:
                print(f"✅ Final result: {len(domain_list)} domains → {len(final_consolidation)} consolidated themes")
                return final_consolidation
    
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


def consolidate_themes_second_pass_batched(model, theme_names, theme_mapping, batch_size=50):
    """
    Second pass consolidation for large theme sets, processing in batches.
    
    Args:
        model: The Gemini model client
        theme_names: List of consolidated theme names from first pass
        theme_mapping: Original mapping from first pass {theme: [domains]}
        batch_size: Number of themes to process per batch
        
    Returns:
        Final consolidated mapping or None if failed
    """
    if len(theme_names) <= batch_size:
        # Small enough for single batch
        return consolidate_themes_second_pass(model, theme_names, theme_mapping)
    
    print(f"   📦 Processing {len(theme_names)} themes in batches of {batch_size}")
    
    # Process themes in batches
    batched_result = {}
    total_batches = (len(theme_names) + batch_size - 1) // batch_size
    
    for i in range(0, len(theme_names), batch_size):
        batch = theme_names[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"   Processing second pass batch {batch_num}/{total_batches} ({len(batch)} themes)...")
        
        # Create a subset mapping for this batch
        batch_mapping = {theme: theme_mapping[theme] for theme in batch if theme in theme_mapping}
        
        # Consolidate this batch
        batch_consolidation = consolidate_themes_second_pass(model, batch, batch_mapping)
        
        if batch_consolidation:
            batched_result.update(batch_consolidation)
            print(f"      ✅ Second pass batch {batch_num} consolidated to {len(batch_consolidation)} themes")
        else:
            # If batch fails, keep original themes
            for theme in batch:
                if theme in theme_mapping:
                    batched_result[theme] = theme_mapping[theme]
            print(f"      ⚠️  Second pass batch {batch_num} failed, keeping original themes")
    
    # THIRD PASS: Final consolidation across batches if we still have many themes
    if len(batched_result) > 100:
        print(f"🔄 Third pass: final consolidation of {len(batched_result)} themes...")
        final_theme_names = list(batched_result.keys())
        final_consolidation = consolidate_themes_second_pass(model, final_theme_names, batched_result)
        if final_consolidation:
            print(f"   ✅ Third pass successful: {len(batched_result)} → {len(final_consolidation)} themes")
            return final_consolidation
    
    return batched_result