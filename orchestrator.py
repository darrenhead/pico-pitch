import time
from collections import defaultdict
import concurrent.futures
from functools import partial
from database_manager import get_supabase_client
from gemini_interaction_agent import (
    get_gemini_client, 
    analyze_lead_with_gemini, 
    analyze_lead_with_enhanced_extraction,
    aggregate_evidence_for_opportunity,
    summarize_common_pain_point,
    consolidate_themes_with_gemini,
    validate_opportunity_with_gemini,
    identify_opportunity_with_gemini, 
    generate_solution_concepts_with_gemini, 
    draft_brd_with_gemini,
    generate_brd_with_gemini,
    draft_prd_with_gemini, 
    generate_agile_plan_with_gemini
)
from file_exporter import save_document_to_file

# --- Configuration ---
MIN_LEADS_FOR_THEME = 3 # The minimum number of related leads to form a theme
FLASH_MODEL_NAME = "gemini-2.5-flash-preview-05-20" # Fast model for high-volume, simple tasks
PRO_MODEL_NAME = "gemini-2.5-pro-preview-06-05" # Powerful model for critical thinking tasks
USE_ENHANCED_EXTRACTION = True  # Toggle to use evidence-based extraction

def get_new_leads(supabase):
    """Fetches a large batch of leads from Supabase that have not been processed yet."""
    print("Fetching new leads from Supabase...")
    try:
        response = supabase.table('raw_leads').select('*').eq('status', 'new_raw_lead').limit(50).execute()
        print(f"Found {len(response.data)} new leads to process.")
        return response.data
    except Exception as e:
        print(f"Error fetching new leads: {e}")
        return []

def get_processed_leads_for_theming(supabase):
    """Fetches all processed leads that are ready for thematic analysis."""
    print("Fetching processed leads for thematic analysis...")
    try:
        # Fetch leads that have a problem extracted but are not yet part of an opportunity
        response = supabase.table('raw_leads').select('*').eq('status', 'problem_extracted').execute()
        print(f"Found {len(response.data)} processed leads to analyze for themes.")
        return response.data
    except Exception as e:
        print(f"Error fetching processed leads for theming: {e}")
        return []

def get_defined_opportunities(supabase):
    """Fetches opportunities that have been defined but have no solution concepts yet."""
    print("Fetching defined opportunities for solution brainstorming...")
    try:
        response = supabase.table('opportunities').select('*').eq('status', 'opportunity_defined').limit(5).execute()
        print(f"Found {len(response.data)} opportunities to brainstorm solutions for.")
        return response.data
    except Exception as e:
        print(f"Error fetching defined opportunities: {e}")
        return []

def get_opportunities_for_validation(supabase):
    """Fetches a large batch of opportunities that have been defined but not yet validated."""
    print("Fetching defined opportunities for validation...")
    try:
        response = supabase.table('opportunities').select('*').eq('status', 'opportunity_defined').limit(50).execute()
        print(f"Found {len(response.data)} opportunities to validate.")
        return response.data
    except Exception as e:
        print(f"Error fetching opportunities for validation: {e}")
        return []

def get_validated_opportunities(supabase):
    """Fetches a large batch of opportunities that have been validated and are ready for solution brainstorming."""
    print("Fetching validated opportunities for solution brainstorming...")
    try:
        response = supabase.table('opportunities').select('*').eq('status', 'opportunity_validated').limit(50).execute()
        print(f"Found {len(response.data)} opportunities to brainstorm solutions for.")
        return response.data
    except Exception as e:
        print(f"Error fetching validated opportunities: {e}")
        return []

def get_opportunities_for_planning(supabase):
    """Fetches a large batch of opportunities that have solutions brainstormed."""
    print("Fetching opportunities ready for document generation...")
    try:
        # Fetch opportunities and their related solution concepts
        response = supabase.table('opportunities').select('*, solution_concepts(*)').eq('status', 'solutions_brainstormed').limit(50).execute()
        print(f"Found {len(response.data)} opportunities for planning.")
        return response.data
    except Exception as e:
        print(f"Error fetching opportunities for planning: {e}")
        return []

def process_and_update_lead(supabase, gemini_model, lead):
    """Analyzes a lead with Gemini and updates it in Supabase."""
    print(f"Processing lead ID: {lead['id']} (Reddit ID: {lead['reddit_id']})")
    
    # Choose extraction method based on configuration
    if USE_ENHANCED_EXTRACTION and lead.get('reddit_id') and lead.get('permalink'):
        # Use enhanced extraction with evidence capture
        lead_data = {
            'content': lead['body_text'],
            'reddit_id': lead['reddit_id'],
            'permalink': lead['permalink'],
            'subreddit': lead.get('subreddit', 'unknown'),
            'is_comment': lead.get('is_comment', False),
            'author': lead.get('author', '[deleted]'),
            'score': lead.get('score', 0),
            'num_comments': lead.get('num_comments', 0)
        }
        analysis_result = analyze_lead_with_enhanced_extraction(gemini_model, lead_data)
        
        # Store enhanced analysis separately if available
        if analysis_result:
            update_data = {
                "gemini_problem_summary": analysis_result.get("problem_summary"),
                "gemini_problem_domain": analysis_result.get("problem_domain"),
                "gemini_saas_potential_flag": analysis_result.get("saas_potential_flag"),
                "gemini_frustration_level": analysis_result.get("urgency_level", "Low"),  # Map urgency to frustration
                "enhanced_analysis": analysis_result,  # Store full enhanced analysis
                "has_evidence": bool(analysis_result.get("supporting_quotes")),
                "status": "problem_extracted"
            }
            print(f"  -> Enhanced analysis successful. New status: problem_extracted")
        else:
            update_data = {"status": "problem_extraction_failed"}
            print(f"  -> Enhanced analysis failed. New status: problem_extraction_failed")
    else:
        # Fallback to original analysis
        analysis_result = analyze_lead_with_gemini(gemini_model, lead['body_text'])
        
        if analysis_result:
            update_data = {
                "gemini_problem_summary": analysis_result.get("problem_summary"),
                "gemini_problem_domain": analysis_result.get("problem_domain"),
                "gemini_saas_potential_flag": analysis_result.get("saas_potential_flag"),
                "gemini_frustration_level": analysis_result.get("frustration_level"),
                "status": "problem_extracted"
            }
            print(f"  -> Standard analysis successful. New status: problem_extracted")
        else:
            update_data = {"status": "problem_extraction_failed"}
            print(f"  -> Standard analysis failed. New status: problem_extraction_failed")

    try:
        supabase.table('raw_leads').update(update_data).eq('id', lead['id']).execute()
    except Exception as e:
        print(f"  -> Error updating lead {lead['id']} in Supabase: {e}")


def find_and_create_themed_opportunities(supabase, gemini_model, theme_name, leads):
    """Analyzes a list of leads under a consolidated theme to create a single opportunity."""
    
    # This function is now simpler, it doesn't need to group, just process.
    summaries = [lead['gemini_problem_summary'] for lead in leads]
    
    # Get the consolidated theme summary from Gemini
    theme_analysis = summarize_common_pain_point(gemini_model, theme_name, summaries)

    if not theme_analysis:
        print(f"    -> Thematic analysis summary failed for theme '{theme_name}'.")
        return

    print(f"    -> Theme summary successful for: '{theme_analysis.get('theme_title')}'")

    # Now, create an opportunity from this consolidated theme
    opportunity_details = identify_opportunity_with_gemini(
        gemini_model,
        theme_analysis.get('consolidated_problem_summary'),
        theme_name # Use the canonical theme name
    )

    if not opportunity_details:
        print("    -> Opportunity identification based on theme failed.")
        # Update leads to avoid reprocessing
        lead_ids_to_update = [lead['id'] for lead in leads]
        supabase.table('raw_leads').update({"status": "thematic_analysis_failed"}).in_('id', lead_ids_to_update).execute()
        return

    # Aggregate evidence if using enhanced extraction
    evidence_data = {}
    if USE_ENHANCED_EXTRACTION:
        # Prepare leads data for evidence aggregation
        leads_with_analysis = []
        for lead in leads:
            if lead.get('enhanced_analysis'):
                leads_with_analysis.append({
                    'permalink': lead.get('permalink', ''),
                    'content': lead.get('body_text', ''),
                    'analysis': lead.get('enhanced_analysis')
                })
            elif lead.get('gemini_problem_summary'):
                # Fallback for leads without enhanced analysis
                leads_with_analysis.append({
                    'permalink': lead.get('permalink', ''),
                    'content': lead.get('body_text', ''),
                    'analysis': {
                        'problem_summary': lead.get('gemini_problem_summary'),
                        'problem_domain': lead.get('gemini_problem_domain'),
                        'urgency_level': lead.get('gemini_frustration_level', 'Low'),
                        'supporting_quotes': [],
                        'financial_indicators': {},
                        'saas_potential_flag': lead.get('gemini_saas_potential_flag', 'Uncertain')
                    }
                })
        
        if leads_with_analysis:
            evidence_data = aggregate_evidence_for_opportunity(leads_with_analysis)
            print(f"    -> Aggregated evidence from {evidence_data.get('total_posts_analyzed', 0)} posts")

    print("    -> Opportunity identified from theme. Creating record in Supabase.")
    try:
        lead_ids = [lead['id'] for lead in leads]
        # Create the opportunity with evidence data
        opportunity_data = {
            "based_on_lead_ids": lead_ids,
            "title": opportunity_details.get("opportunity_title"),
            "problem_summary_consolidated": theme_analysis.get('consolidated_problem_summary'),
            "opportunity_description_ai": opportunity_details.get("opportunity_description"),
            "target_user_ai": opportunity_details.get("target_user"),
            "value_proposition_ai": opportunity_details.get("value_proposition"),
            "domain_relevance_ai": opportunity_details.get("domain_relevance"),
            "status": "opportunity_defined"
        }
        
        # Add evidence data if available
        if evidence_data:
            opportunity_data.update({
                "evidence_json": evidence_data,
                "total_posts_analyzed": evidence_data.get('total_posts_analyzed', 0),
                "pain_point_frequency": evidence_data.get('pain_point_frequency', 0)
            })
            
        insert_response = supabase.table('opportunities').insert(opportunity_data).execute()
        
        if insert_response.data:
            print(f"    -> Successfully created opportunity for theme '{theme_name}'.")
            # Update all contributing leads
            supabase.table('raw_leads').update({"status": "opportunity_created"}).in_('id', lead_ids).execute()
        else:
             print("   -> FAILED to insert opportunity.")


    except Exception as e:
        print(f"    -> Error creating themed opportunity or updating leads: {e}")
        lead_ids_to_update = [lead['id'] for lead in leads]
        supabase.table('raw_leads').update({"status": "thematic_analysis_failed"}).in_('id', lead_ids_to_update).execute()


def validate_and_update_opportunity(supabase, gemini_model, opportunity):
    """Validates an opportunity and updates its status and scores in Supabase."""
    print(f"Validating opportunity ID: {opportunity['id']} ('{opportunity['title']}')")
    
    validation_result = validate_opportunity_with_gemini(gemini_model, opportunity)
    
    update_data = {}
    if validation_result:
        recommendation = validation_result.get("recommendation", "No-Go")
        new_status = "opportunity_validated" if recommendation == "Go" else "opportunity_rejected"
        
        update_data = {
            "monetization_score": validation_result.get("monetization_score"),
            "market_size_score": validation_result.get("market_size_score"),
            "feasibility_score": validation_result.get("feasibility_score"),
            "recommendation": recommendation,
            "justification": validation_result.get("justification"),
            "status": new_status
        }
        print(f"  -> Validation successful. Recommendation: {recommendation}. New status: {new_status}")
    else:
        update_data = {"status": "validation_failed"}
        print(f"  -> Validation failed. New status: validation_failed")

    try:
        supabase.table('opportunities').update(update_data).eq('id', opportunity['id']).execute()
    except Exception as e:
        print(f"  -> Error updating opportunity {opportunity['id']} in Supabase: {e}")


def brainstorm_and_store_solutions(supabase, gemini_model, opportunity):
    """Generates solution concepts for an opportunity and stores them."""
    print(f"Brainstorming solutions for opportunity ID: {opportunity['id']}")

    concepts = generate_solution_concepts_with_gemini(
        gemini_model,
        opportunity.get('opportunity_description_ai'),
        opportunity.get('target_user_ai'),
        opportunity.get('value_proposition_ai')
    )

    if not concepts:
        print("  -> Solution brainstorming failed.")
        supabase.table('opportunities').update({"status": "solution_brainstorm_failed"}).eq('id', opportunity['id']).execute()
        return

    print(f"  -> Brainstorming successful. Storing {len(concepts)} concepts.")
    try:
        # Prepare concepts for batch insertion
        concepts_to_insert = [
            {
                "opportunity_id": opportunity['id'],
                "concept_name": concept.get("concept_name"),
                "core_features_json": {"features": concept.get("core_features")} # Wrap features in a JSON object
            }
            for concept in concepts
        ]
        
        supabase.table('solution_concepts').insert(concepts_to_insert).execute()

        # Update the opportunity's status
        supabase.table('opportunities').update({"status": "solutions_brainstormed"}).eq('id', opportunity['id']).execute()
        print(f"  -> Successfully stored concepts and updated opportunity {opportunity['id']}.")

    except Exception as e:
        print(f"  -> Error storing solution concepts: {e}")
        supabase.table('opportunities').update({"status": "solution_brainstorm_failed"}).eq('id', opportunity['id']).execute()


def generate_planning_documents(supabase, gemini_model, opportunity):
    """Generates BRD, saves it, and stores it in Supabase."""
    print(f"Generating planning documents for opportunity ID: {opportunity['id']}")

    # M3.2 is not done, so we'll select the first concept as the preferred one
    concepts = opportunity.get('solution_concepts')
    if not concepts:
        print("  -> No solution concepts found for this opportunity. Skipping.")
        return

    selected_concept = concepts[0]
    print(f"  -> Auto-selecting first concept: '{selected_concept.get('concept_name')}'")

    # We need the original lead's pain point summary.
    # This assumes the first lead is representative.
    lead_id = opportunity.get('based_on_lead_ids', [])[0]
    lead_response = supabase.table('raw_leads').select('gemini_problem_summary').eq('id', lead_id).single().execute()
    pain_point_summary = lead_response.data.get('gemini_problem_summary')

    if not pain_point_summary:
        print("  -> Could not retrieve original pain point. Skipping BRD generation.")
        return

    # Prepare opportunity details with evidence if available
    opportunity_with_evidence = opportunity.copy()
    
    # If we have evidence data, merge it into opportunity details
    if opportunity.get('evidence_json'):
        evidence = opportunity['evidence_json']
        opportunity_with_evidence.update({
            'total_posts_analyzed': opportunity.get('total_posts_analyzed', 0),
            'pain_point_frequency': opportunity.get('pain_point_frequency', 0),
            'supporting_quotes': evidence.get('supporting_quotes', []),
            'financial_indicators': evidence.get('financial_indicators', {}),
            'urgency_distribution': evidence.get('urgency_distribution', {}),
            'competitor_mentions': evidence.get('competitor_mentions', {})
        })
        print(f"  -> Using evidence from {opportunity_with_evidence['total_posts_analyzed']} posts for BRD generation")

    # M3.3: Draft BRD with enhanced generation if evidence is available
    if USE_ENHANCED_EXTRACTION and opportunity_with_evidence.get('supporting_quotes'):
        brd_content = generate_brd_with_gemini(
            gemini_model, 
            pain_point_summary, 
            opportunity_with_evidence, 
            selected_concept, 
            use_evidence=True
        )
    else:
        brd_content = draft_brd_with_gemini(gemini_model, pain_point_summary, opportunity, selected_concept)
        
    if not brd_content:
        print("  -> BRD drafting failed.")
        # Optionally update status to reflect failure
        return

    print("  -> BRD drafted successfully. Saving to file and Supabase...")
    try:
        # Save BRD to local file
        brd_file_path = save_document_to_file(opportunity['id'], opportunity['title'], 'BRD', brd_content)

        # Store BRD in documents table
        supabase.table('documents').insert({
            "opportunity_id": opportunity['id'],
            "document_type": "BRD",
            "content_markdown": brd_content,
            "local_file_path": brd_file_path
        }).execute()
        print(f"  -> Successfully saved BRD for opportunity {opportunity['id']}.")

    except Exception as e:
        print(f"  -> Error saving BRD: {e}")
        # If BRD saving fails, we shouldn't proceed to PRD
        return
        
    # M3.4: Draft PRD with enhanced generation if evidence is available
    if USE_ENHANCED_EXTRACTION and opportunity_with_evidence.get('supporting_quotes'):
        prd_content = draft_prd_with_gemini(
            gemini_model, 
            brd_content, 
            selected_concept, 
            opportunity_with_evidence, 
            use_evidence=True
        )
    else:
        prd_content = draft_prd_with_gemini(
            gemini_model, 
            brd_content, 
            selected_concept, 
            opportunity, 
            use_evidence=False
        )
    if not prd_content:
        print("  -> PRD drafting failed.")
        return

    print("  -> PRD drafted successfully. Saving to file and Supabase...")
    try:
        # Save PRD to local file
        prd_file_path = save_document_to_file(opportunity['id'], opportunity['title'], 'PRD', prd_content)

        # Store PRD in documents table
        supabase.table('documents').insert({
            "opportunity_id": opportunity['id'],
            "document_type": "PRD",
            "content_markdown": prd_content,
            "local_file_path": prd_file_path
        }).execute()
        print(f"  -> Successfully saved PRD for opportunity {opportunity['id']}.")
    except Exception as e:
        print(f"  -> Error saving PRD: {e}")
        return

    # M3.5: Draft Agile Plan
    agile_plan_content = generate_agile_plan_with_gemini(gemini_model, prd_content)
    if not agile_plan_content:
        print("  -> Agile Plan generation failed.")
        return

    print("  -> Agile Plan generated successfully. Saving to file and Supabase...")
    try:
        # Save Agile Plan to local file
        agile_plan_file_path = save_document_to_file(opportunity['id'], opportunity['title'], 'AGILE_PLAN', agile_plan_content)

        # Store Agile Plan in documents table
        supabase.table('documents').insert({
            "opportunity_id": opportunity['id'],
            "document_type": "AGILE_PLAN",
            "content_markdown": agile_plan_content,
            "local_file_path": agile_plan_file_path
        }).execute()

        # Update opportunity with selected concept and final status
        supabase.table('opportunities').update({
            "selected_solution_concept_json": selected_concept,
            "status": "planning_documents_generated"
        }).eq('id', opportunity['id']).execute()

        print(f"  -> Successfully saved Agile Plan for opportunity {opportunity['id']}.")

    except Exception as e:
        print(f"  -> Error saving Agile Plan or updating opportunity: {e}")


def main():
    """Main orchestrator to run as a single, powerful batch job."""
    print("Starting PicoPitch Orchestrator...")
    start_time = time.time()
    stage_times = {}

    gemini_flash_model = get_gemini_client(FLASH_MODEL_NAME)
    gemini_pro_model = get_gemini_client(PRO_MODEL_NAME)
    print(f"Initialized models: '{FLASH_MODEL_NAME}' for speed, '{PRO_MODEL_NAME}' for quality.")
    supabase = get_supabase_client()
    
    # --- STAGE 1: Process all raw leads in parallel ---
    print("\n--- STAGE 1: PROCESSING ALL RAW LEADS (IN PARALLEL) ---")
    while True:
        new_leads = get_new_leads(supabase)
        if not new_leads:
            print("No more new leads to process.")
            break
        
        # Create a partial function with fixed arguments for supabase and the model
        process_func = partial(process_and_update_lead, supabase, gemini_flash_model)
        
        # Use a ThreadPoolExecutor to process leads in parallel for maximum speed
        with concurrent.futures.ThreadPoolExecutor() as executor:
            print(f"Processing batch of {len(new_leads)} leads in parallel...")
            # Use list() to ensure all futures complete before the 'with' block exits
            list(executor.map(process_func, new_leads))
    stage_times["1_Lead_Processing"] = time.time() - start_time

    # --- STAGE 2: PRE-ANALYSIS - Group leads by raw domain ---
    print("\n--- STAGE 2: GROUPING LEADS BY DOMAIN ---")
    processed_leads = get_processed_leads_for_theming(supabase)
    leads_by_domain = defaultdict(list)
    if processed_leads:
        for lead in processed_leads:
            if lead.get("gemini_problem_domain"):
                leads_by_domain[lead["gemini_problem_domain"]].append(lead)
        print(f"Found {len(leads_by_domain)} raw domains to analyze.")
    else:
        print("No processed leads were found for thematic analysis.")
    stage_times["2_Domain_Grouping"] = time.time() - stage_times.get("1_Lead_Processing", start_time)

    # --- STAGE 2.5: CONSOLIDATE THEMES ---
    print("\n--- STAGE 2.5: CONSOLIDATING SIMILAR THEMES ---")
    raw_domains = list(leads_by_domain.keys())
    print(f"Sending {len(raw_domains)} unique domains to Gemini for consolidation. This may take a few moments...")
    consolidated_theme_map = consolidate_themes_with_gemini(gemini_pro_model, raw_domains)
    
    if not consolidated_theme_map:
        print("Theme consolidation failed. Exiting.")
        return

    print(f"Consolidated {len(raw_domains)} raw domains into {len(consolidated_theme_map)} canonical themes.")
    
    # Merge the lead groups based on the consolidation map
    final_themes = defaultdict(list)
    for canonical_theme, original_domains in consolidated_theme_map.items():
        for domain in original_domains:
            final_themes[canonical_theme].extend(leads_by_domain[domain])
            
    # --- STAGE 3: Create opportunities from CONSOLIDATED themes in parallel ---
    print("\n--- STAGE 3: CREATING OPPORTUNITIES FROM CONSOLIDATED THEMES (IN PARALLEL) ---")
    
    # Filter themes that meet the minimum lead requirement
    themes_to_process = {theme: leads for theme, leads in final_themes.items() if len(leads) >= MIN_LEADS_FOR_THEME}
    print(f"Found {len(themes_to_process)} themes that meet the minimum lead requirement for opportunity creation.")

    if themes_to_process:
        # Create a partial function for parallel execution
        create_opp_func = partial(find_and_create_themed_opportunities, supabase, gemini_pro_model)
        
        # Use a ThreadPoolExecutor to process themes in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            print(f"Creating opportunities for {len(themes_to_process)} themes in parallel...")
            # Map the function to the themes' names (keys) and their corresponding leads (values)
            list(executor.map(create_opp_func, themes_to_process.keys(), themes_to_process.values()))
    stage_times["3_Opportunity_Creation"] = time.time() - stage_times.get("2.5_Theme_Consolidation", start_time)

    # --- STAGE 4: Validate all defined opportunities in parallel ---
    print("\n--- STAGE 4: OPPORTUNITY VALIDATION (IN PARALLEL) ---")
    while True:
        opportunities_to_validate = get_opportunities_for_validation(supabase)
        if not opportunities_to_validate:
            print("No more opportunities to validate.")
            break
        
        validate_func = partial(validate_and_update_opportunity, supabase, gemini_pro_model)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            print(f"Validating batch of {len(opportunities_to_validate)} opportunities in parallel...")
            list(executor.map(validate_func, opportunities_to_validate))
    stage_times["4_Validation"] = time.time() - stage_times.get("3_Opportunity_Creation", start_time)

    # --- STAGE 5: Brainstorm solutions for all validated opportunities in parallel ---
    print("\n--- STAGE 5: SOLUTION BRAINSTORMING (IN PARALLEL) ---")
    while True:
        validated_opportunities = get_validated_opportunities(supabase)
        if not validated_opportunities:
            print("No more validated opportunities for brainstorming.")
            break
        
        brainstorm_func = partial(brainstorm_and_store_solutions, supabase, gemini_pro_model)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            print(f"Brainstorming for batch of {len(validated_opportunities)} opportunities in parallel...")
            list(executor.map(brainstorm_func, validated_opportunities))
    stage_times["5_Solution_Brainstorming"] = time.time() - stage_times.get("4_Validation", start_time)

    # --- STAGE 6: Generate documents for all planned opportunities in parallel ---
    print("\n--- STAGE 6: DOCUMENT GENERATION (IN PARALLEL) ---")
    while True:
        opportunities_for_planning = get_opportunities_for_planning(supabase)
        if not opportunities_for_planning:
            print("No more opportunities ready for planning.")
            break
        
        planning_func = partial(generate_planning_documents, supabase, gemini_pro_model)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            print(f"Generating documents for batch of {len(opportunities_for_planning)} opportunities in parallel...")
            list(executor.map(planning_func, opportunities_for_planning))
    stage_times["6_Document_Generation"] = time.time() - stage_times.get("5_Solution_Brainstorming", start_time)

    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n--- PicoPitch Orchestrator run complete. ---")
    print("\n--- PERFORMANCE SUMMARY ---")
    for stage, duration in stage_times.items():
        print(f"  - Stage {stage}: {duration:.2f} seconds")
    print(f"  - TOTAL RUN TIME: {total_time:.2f} seconds")


if __name__ == "__main__":
    main() 