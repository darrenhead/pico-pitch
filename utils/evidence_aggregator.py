"""Evidence aggregation utilities for opportunity validation."""


def aggregate_evidence_for_opportunity(leads_data):
    """
    Aggregates evidence from multiple leads to provide market validation data.
    
    Args:
        leads_data: List of analyzed leads with their extracted problems and evidence
        
    Returns:
        Dictionary containing aggregated evidence metrics
    """
    evidence = {
        'total_posts_analyzed': len(leads_data),
        'supporting_quotes': [],
        'financial_indicators': {
            'amounts_mentioned': [],
            'willing_to_pay_counts': {'Yes': 0, 'No': 0, 'Maybe': 0, 'Unknown': 0},
            'total_cost_of_problems': []
        },
        'urgency_distribution': {'High': 0, 'Medium': 0, 'Low': 0},
        'competitor_mentions': {},
        'pain_point_frequency': 0,
        'source_links': [],
        'source_posts': []  # Enhanced source information
    }
    
    for lead in leads_data:
        analysis = lead.get('analysis', {})
        
        # Skip if no clear problem
        if analysis.get('problem_summary', '').lower() == 'no clear problem':
            continue
            
        evidence['pain_point_frequency'] += 1
        
        # Collect detailed source post information
        if lead.get('permalink'):
            source_post = {
                'reddit_url': f"https://reddit.com{lead.get('permalink', '')}",
                'permalink': lead.get('permalink', ''),
                'title': lead.get('title', 'Untitled'),
                'subreddit': lead.get('subreddit', 'unknown'),
                'author': lead.get('author', '[deleted]'),
                'is_comment': lead.get('is_comment', False),
                'problem_summary': analysis.get('problem_summary', ''),
                'urgency_level': analysis.get('urgency_level', 'Low'),
                'financial_impact': analysis.get('financial_indicators', {}).get('cost_of_problem', ''),
                'supporting_quotes': analysis.get('supporting_quotes', [])
            }
            evidence['source_posts'].append(source_post)
        
        # Collect quotes
        quotes = analysis.get('supporting_quotes', [])
        for quote in quotes:
            if isinstance(quote, dict):
                evidence['supporting_quotes'].append({
                    'text': quote.get('text', ''),
                    'context': quote.get('context', ''),
                    'source': lead.get('permalink', ''),
                    'reddit_url': f"https://reddit.com{lead.get('permalink', '')}" if lead.get('permalink') else '',
                    'author': lead.get('author', '[deleted]'),
                    'subreddit': lead.get('subreddit', 'unknown')
                })
        
        # Aggregate financial indicators
        financial = analysis.get('financial_indicators', {})
        if financial:
            amounts = financial.get('amounts_mentioned', [])
            evidence['financial_indicators']['amounts_mentioned'].extend(amounts)
            
            willing = financial.get('willing_to_pay', 'Unknown')
            if willing not in evidence['financial_indicators']['willing_to_pay_counts']:
                evidence['financial_indicators']['willing_to_pay_counts'][willing] = 0
            evidence['financial_indicators']['willing_to_pay_counts'][willing] += 1
            
            cost_of_problem = financial.get('cost_of_problem', '')
            if cost_of_problem:
                evidence['financial_indicators']['total_cost_of_problems'].append(cost_of_problem)
        
        # Count urgency levels (handle any unexpected values gracefully)
        urgency = analysis.get('urgency_level', 'Low')
        if urgency not in evidence['urgency_distribution']:
            evidence['urgency_distribution'][urgency] = 0
        evidence['urgency_distribution'][urgency] += 1
        
        # Track source links (maintaining backwards compatibility)
        if lead.get('permalink'):
            evidence['source_links'].append(lead.get('permalink'))
        
        # Extract competitor mentions (simple keyword search for now)
        text = lead.get('content', '').lower()
        competitors = ['upwork', 'toptal', 'fiverr', 'freelancer', 'guru', '99designs']
        for comp in competitors:
            if comp in text:
                evidence['competitor_mentions'][comp] = evidence['competitor_mentions'].get(comp, 0) + 1
    
    # Calculate percentages
    if evidence['total_posts_analyzed'] > 0:
        evidence['pain_point_percentage'] = round(
            (evidence['pain_point_frequency'] / evidence['total_posts_analyzed']) * 100, 1
        )
    else:
        evidence['pain_point_percentage'] = 0
    
    return evidence