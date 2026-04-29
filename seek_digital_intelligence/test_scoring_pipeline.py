#!/usr/bin/env python
"""
Local demo: Run the lead scoring pipeline on sample data
Shows what lead_score and lead_tier each spider's output gets.
"""

import sys
import json
from datetime import datetime, timezone

# Add project to path
sys.path.insert(0, '/Users/cosmin/spiders/seek_digital_intelligence')

from seek_intelligence.items import BusinessItem
from seek_intelligence.processors.pipeline import LeadScoringPipeline


def demo_scoring():
    """Demonstrate the scoring pipeline on sample businesses."""
    
    pipeline = LeadScoringPipeline()
    
    # Sample businesses to score
    sample_leads = [
        {
            "name": "Restaurant Casa Veche",
            "industry": "restaurante",
            "city": "Iasi",
            "phone": "+40232123456",
            "website_url": "https://casaveche.ro",
            "has_website": True,
            "website_year": 2019,
            "is_mobile_ok": False,
            "has_ssl": True,
            "cms_detected": "WordPress",
            "has_facebook": True,
            "has_instagram": True,
            "has_google_biz": True,
            "review_count": 87,
            "avg_rating": 4.5,
            "source": "pagini_aurii",
        },
        {
            "name": "Salon Frumusete Elena",
            "industry": "saloane-infrumusetare",
            "city": "Iasi",
            "phone": "+40232654321",
            "website_url": None,
            "has_website": False,
            "website_year": None,
            "is_mobile_ok": None,
            "has_ssl": None,
            "cms_detected": None,
            "has_facebook": True,
            "has_instagram": True,
            "has_google_biz": False,
            "review_count": 34,
            "avg_rating": 4.8,
            "source": "pagini_aurii",
        },
        {
            "name": "Cabinet Medical Dr Popescu",
            "industry": "cabinete-medicale",
            "city": "Cluj",
            "phone": "+40264555888",
            "website_url": "https://drmedicalpopescu.ro",
            "has_website": True,
            "website_year": 2015,
            "is_mobile_ok": True,
            "has_ssl": True,
            "cms_detected": "WordPress",
            "has_facebook": False,
            "has_instagram": False,
            "has_google_biz": True,
            "review_count": 156,
            "avg_rating": 4.9,
            "source": "pagini_aurii",
        },
        {
            "name": "Agentie Fasade Renovari",
            "industry": "constructii",
            "city": "Bucuresti",
            "phone": "+40217654321",
            "website_url": None,
            "has_website": False,
            "website_year": None,
            "is_mobile_ok": None,
            "has_ssl": None,
            "cms_detected": None,
            "has_facebook": True,
            "has_instagram": False,
            "has_google_biz": False,
            "review_count": 12,
            "avg_rating": 4.2,
            "running_ads": True,  # Marked from facebook_ads spider
            "source": "pagini_aurii",
        },
    ]
    
    print("=" * 80)
    print("LEAD SCORING PIPELINE — SAMPLE OUTPUT")
    print("=" * 80)
    print()
    
    results = []
    for lead_data in sample_leads:
        item = BusinessItem()
        for key, value in lead_data.items():
            item[key] = value
        item["scraped_at"] = datetime.now(timezone.utc).isoformat()
        
        # Process through pipeline
        scored_item = pipeline.process_item(item, None)
        results.append(dict(scored_item))
        
        # Display result
        print(f"Business: {scored_item['name']}")
        print(f"  Industry: {scored_item['industry']} | City: {scored_item['city']}")
        print(f"  Website: {'✓' if scored_item.get('has_website') else '✗'}")
        print(f"  Reviews: {scored_item.get('review_count', 0)} (avg {scored_item.get('avg_rating', 0):.1f}★)")
        print(f"  Social: Facebook {('✓' if scored_item.get('has_facebook') else '✗')} | Instagram {('✓' if scored_item.get('has_instagram') else '✗')}")
        print(f"  Running Ads: {'✓' if scored_item.get('running_ads') else '✗'}")
        print()
        print(f"  SCORE: {scored_item['lead_score']}/100")
        print(f"  TIER:  {scored_item['lead_tier'].upper()}")
        print()
        if 'score_breakdown' in scored_item:
            print(f"  Scoring breakdown:")
            for signal, points in scored_item['score_breakdown'].items():
                if points > 0:
                    print(f"    + {signal}: {points} pts")
        print()
        print("-" * 80)
        print()
    
    # Export as JSON
    output_file = "/Users/cosmin/spiders/seek_digital_intelligence/sample_scored_leads.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"✓ Sample scored leads exported to: {output_file}")
    print()
    
    # Summary statistics
    hot_count = sum(1 for r in results if r.get('lead_tier') == 'hot')
    warm_count = sum(1 for r in results if r.get('lead_tier') == 'warm')
    cold_count = sum(1 for r in results if r.get('lead_tier') == 'cold')
    
    print("SUMMARY:")
    print(f"  🔥 HOT (50+):   {hot_count} leads")
    print(f"  🟠 WARM (25-49): {warm_count} leads")
    print(f"  ❄️  COLD (<25):   {cold_count} leads")
    print()


if __name__ == "__main__":
    demo_scoring()
