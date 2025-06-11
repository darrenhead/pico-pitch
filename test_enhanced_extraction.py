#!/usr/bin/env python3
"""
Test script to demonstrate enhanced extraction with evidence capture.
"""

import json
import concurrent.futures
from functools import partial
from gemini_interaction_agent import (
    get_gemini_client, 
    analyze_lead_with_enhanced_extraction,
    aggregate_evidence_for_opportunity
)

# Test data simulating Reddit posts about technical hiring challenges
test_leads = [
    {
        'reddit_id': 'test001',
        'permalink': '/r/startups/comments/test001',
        'subreddit': 'startups',
        'is_comment': False,
        'content': '''
        I just burned through $75k on a "senior developer" who couldn't even 
        set up basic authentication. I'm desperate - we're 4 months behind 
        schedule and investors are asking questions. Would gladly pay $10k/month 
        for someone who actually knows what they're doing. This is a nightmare.
        '''
    },
    {
        'reddit_id': 'test002',
        'permalink': '/r/entrepreneur/comments/test002',
        'subreddit': 'entrepreneur',
        'is_comment': False,
        'content': '''
        Non-technical founder here. Just discovered our CTO has been outsourcing
        all the work to cheap freelancers while billing us $150/hour. We've spent
        $120k and have nothing but spaghetti code. How do you even vet technical
        people when you don't understand code yourself?
        '''
    },
    {
        'reddit_id': 'test003',
        'permalink': '/r/startups/comments/test003',
        'subreddit': 'startups',
        'is_comment': True,
        'content': '''
        Same thing happened to me! Lost $50k to a "blockchain expert" who
        disappeared after 2 months. The worst part is I can't even tell if
        the code he left is any good. Considering hiring a technical advisor
        just to help me hire developers. This is so frustrating!
        '''
    }
]

def process_single_lead(model, lead, index):
    """Process a single lead and return results."""
    print(f"\n📄 Processing Lead {index+1}:")
    print(f"   Source: {lead['subreddit']} - {'Comment' if lead['is_comment'] else 'Post'}")
    print(f"   Preview: {lead['content'][:100]}...")
    
    # Run enhanced extraction
    result = analyze_lead_with_enhanced_extraction(model, lead)
    
    # Display results
    print(f"\n   ✅ Extracted Problem: {result.get('problem_summary', 'N/A')}")
    print(f"   📊 Urgency Level: {result.get('urgency_level', 'N/A')}")
    
    # Show quotes
    quotes = result.get('supporting_quotes', [])
    if quotes:
        print(f"   💬 Key Quote: \"{quotes[0].get('text', 'N/A')}\"")
    
    # Show financial indicators
    financial = result.get('financial_indicators', {})
    amounts = financial.get('amounts_mentioned', [])
    if amounts:
        print(f"   💰 Money Mentioned: {', '.join(amounts)}")
    
    print(f"   🔗 Source: https://reddit.com{lead['permalink']}")
    
    return {
        'permalink': lead['permalink'],
        'content': lead['content'],
        'analysis': result
    }

def test_enhanced_extraction():
    """Test the enhanced extraction on sample leads."""
    print("🚀 Testing Enhanced Extraction with Evidence Capture (PARALLELIZED)\n")
    print("=" * 60)
    
    # Initialize Gemini
    model = get_gemini_client()
    
    # Create partial function with model
    process_func = partial(process_single_lead, model)
    
    # Process leads in parallel
    analyzed_leads = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tasks
        futures = [executor.submit(process_func, lead, i) for i, lead in enumerate(test_leads)]
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                analyzed_leads.append(result)
            except Exception as e:
                print(f"Error processing lead: {e}")
    
    # Sort results to maintain order (optional)
    analyzed_leads.sort(key=lambda x: x['permalink'])
    
    # Test evidence aggregation
    print("\n" + "=" * 60)
    print("\n📊 Aggregating Evidence Across All Leads:\n")
    
    evidence = aggregate_evidence_for_opportunity(analyzed_leads)
    
    print(f"Total Posts Analyzed: {evidence['total_posts_analyzed']}")
    print(f"Posts with Clear Pain Points: {evidence['pain_point_frequency']} ({evidence['pain_point_percentage']}%)")
    
    print(f"\nUrgency Distribution:")
    for level, count in evidence['urgency_distribution'].items():
        print(f"  - {level}: {count} posts")
    
    print(f"\nWillingness to Pay:")
    for response, count in evidence['financial_indicators']['willing_to_pay_counts'].items():
        if count > 0:
            print(f"  - {response}: {count} posts")
    
    if evidence['financial_indicators']['amounts_mentioned']:
        print(f"\nFinancial Impact Mentioned:")
        for amount in set(evidence['financial_indicators']['amounts_mentioned']):
            print(f"  - {amount}")
    
    if evidence['supporting_quotes']:
        print(f"\n📝 Sample Supporting Quotes ({len(evidence['supporting_quotes'])} total):")
        for quote in evidence['supporting_quotes'][:2]:
            print(f"\n  \"{quote['text']}\"")
            print(f"  Source: {quote['source']}")
    
    # Save results for inspection
    with open('test_extraction_results.json', 'w') as f:
        json.dump({
            'analyzed_leads': analyzed_leads,
            'aggregated_evidence': evidence
        }, f, indent=2)
    
    print("\n✅ Test complete! Results saved to test_extraction_results.json")
    print("⚡ Parallel processing made this much faster!")

if __name__ == '__main__':
    test_enhanced_extraction() 