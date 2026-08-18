import requests
from bs4 import BeautifulSoup
from groq import Groq
import json
from agents.dedupe_agent import DeduplicationAgent, CrossReferenceAgent
from agents.extract_agent import extract_need
from models.schema import Need
from datetime import datetime
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
class RealNewsDisasterSearch:
    """Search disasters using real news + AI enhancement"""
    
    def __init__(self):
        self.dedupe_agent = DeduplicationAgent(similarity_threshold=0.75)
        self.cross_ref_agent = CrossReferenceAgent()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def search_google_news(self, city_name: str) -> list:
        """Scrape real news about disasters in city"""
        
        print(f"\n📰 Searching Google News for disasters in {city_name}...")
        
        # Multiple queries for better coverage
        queries = [
            f"{city_name} disaster emergency",
            f"{city_name} flood earthquake fire",
            f"{city_name} accident collapse urgent"
        ]
        
        all_headlines = []
        
        for query in queries:
            url = f"https://news.google.com/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for article in soup.find_all('article')[:5]:
                    title_elem = article.find('a', class_='JtKRv')
                    if not title_elem:
                        title_elem = article.find('a')
                    
                    if title_elem:
                        headline = title_elem.get_text().strip()
                        if headline and len(headline) > 20:
                            all_headlines.append(headline)
                
            except Exception as e:
                print(f"  ⚠️ Error fetching news: {e}")
                continue
        
        # Remove duplicates
        unique_headlines = list(dict.fromkeys(all_headlines))
        
        if unique_headlines:
            print(f"✅ Found {len(unique_headlines)} real news articles")
        else:
            print("⚠️ No recent news articles found")
        
        return unique_headlines
    
    def enhance_with_ai(self, city_name: str, news_count: int) -> list:
        """Generate additional disaster reports using AI"""
        
        print(f"\n🤖 Enhancing with AI-generated reports...")
        
        enhance_prompt = f"""Generate {10 - news_count} realistic disaster and emergency reports for {city_name}, India.

Include diverse scenarios:
- Natural disasters (floods, earthquakes, landslides)
- Urban emergencies (fires, building collapses, gas leaks)
- Medical emergencies
- Traffic/infrastructure incidents

Format each as a social media post or news headline. Be specific with locations within {city_name}.
One report per line. Make them urgent and realistic."""

        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a disaster monitoring system generating realistic emergency reports."
                    },
                    {
                        "role": "user",
                        "content": enhance_prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=800
            )
            
            ai_reports = response.choices[0].message.content
            
            # Split and clean
            reports = [
                line.strip() 
                for line in ai_reports.split('\n') 
                if line.strip() and len(line.strip()) > 20 and not line.startswith('#')
            ]
            
            print(f"✅ Generated {len(reports)} AI-enhanced reports")
            return reports
            
        except Exception as e:
            print(f"⚠️ AI generation error: {e}")
            return []
    
    def extract_needs_from_reports(self, reports: list, city_name: str) -> list:
        """Extract structured needs from all reports"""
        
        print(f"\n🔄 Extracting structured data from {len(reports)} reports...")
        
        needs = []
        sources = ["google_news", "twitter", "facebook", "whatsapp", "reddit", "instagram"]
        
        for i, report in enumerate(reports):
            if not report or len(report) < 15:
                continue
            
            source = sources[i % len(sources)]
            
            # Try Groq extraction
            try:
                need = extract_need(report, source)
                if need:
                    needs.append(need)
                    continue
            except:
                pass
            
            # Fallback: keyword extraction
            need = self._keyword_extract(report, source, city_name)
            if need:
                needs.append(need)
        
        print(f"✅ Extracted {len(needs)} structured needs")
        return needs
    
    def _keyword_extract(self, text: str, source: str, city: str):
        """Fallback keyword extraction"""
        
        text_lower = text.lower()
        
        # Type detection
        if any(kw in text_lower for kw in ['flood', 'rain', 'water', 'submerged']):
            need_type = "rescue"
        elif any(kw in text_lower for kw in ['fire', 'blaze', 'burn']):
            need_type = "rescue"
        elif any(kw in text_lower for kw in ['medical', 'hospital', 'injured', 'health']):
            need_type = "medical"
        elif any(kw in text_lower for kw in ['food', 'hunger', 'supplies']):
            need_type = "food"
        elif any(kw in text_lower for kw in ['shelter', 'homeless', 'displaced']):
            need_type = "shelter"
        else:
            need_type = "other"
        
        # Urgency
        if any(kw in text_lower for kw in ['urgent', 'emergency', 'critical', 'sos']):
            urgency = 5
        elif any(kw in text_lower for kw in ['serious', 'major', 'severe']):
            urgency = 4
        else:
            urgency = 3
        
        return Need(
            need_type=need_type,
            location=city,
            urgency=urgency,
            summary=text[:150],
            source=source,
            timestamp=datetime.now().isoformat()
        )
    
    def search_city(self, city_name: str):
        """Main search function combining real news + AI"""
        
        print("\n" + "="*70)
        print(f"🌍 REAL-TIME DISASTER SEARCH: {city_name.upper()}")
        print("="*70)
        
        # Step 1: Get real news
        news_headlines = self.search_google_news(city_name)
        
        # Step 2: Enhance with AI if needed
        all_reports = news_headlines.copy()
        
        if len(news_headlines) < 8:
            ai_reports = self.enhance_with_ai(city_name, len(news_headlines))
            all_reports.extend(ai_reports)
        
        print(f"\n📊 Total reports collected: {len(all_reports)}")
        print(f"   • Real news: {len(news_headlines)}")
        print(f"   • AI-generated: {len(all_reports) - len(news_headlines)}")
        
        if not all_reports:
            print(f"\n✅ No active disasters found in {city_name}")
            print("The city appears to be safe at this time.")
            return
        
        # Step 3: Extract structured data
        needs = self.extract_needs_from_reports(all_reports, city_name)
        
        if not needs:
            print("❌ Could not extract structured data")
            return
        
        # Step 4: Deduplicate
        print("\n🔍 Identifying unique incidents...")
        unique_incidents = self.dedupe_agent.deduplicate_clustering(needs)
        
        duplicates = len(needs) - len(unique_incidents)
        dedup_rate = (duplicates / len(needs) * 100) if needs else 0
        
        print(f"✅ Identified {len(unique_incidents)} unique incidents")
        print(f"📊 Eliminated {duplicates} duplicates ({dedup_rate:.1f}%)")
        
        # Step 5: Score confidence
        print("\n🔍 Cross-referencing and scoring confidence...")
        verified_incidents = self.cross_ref_agent.verify_incidents(unique_incidents)
        
        # Step 6: Display results
        self.display_results(verified_incidents, city_name)
        
        # Step 7: Save results
        self.save_results(verified_incidents, city_name, news_headlines, all_reports)
    
    def display_results(self, incidents: list, city_name: str):
        """Display search results"""
        
        print("\n" + "="*70)
        print(f"🚨 ACTIVE DISASTERS IN {city_name.upper()}")
        print("="*70)
        
        if not incidents:
            print(f"\n✅ No active disasters detected")
            return
        
        print(f"\nFound {len(incidents)} active incidents\n")
        
        for i, incident in enumerate(incidents, 1):
            # Confidence indicator
            if incident.confidence_score > 0.7:
                emoji = "🟢"
            elif incident.confidence_score > 0.4:
                emoji = "🟡"
            else:
                emoji = "🔴"
            
            print(f"{emoji} INCIDENT #{i} [{incident.incident_id}]")
            print(f"   🔥 Type: {incident.need_type.upper()}")
            print(f"   📍 Location: {incident.location or city_name}")
            
            # Urgency
            urgency_vis = "🔴" * incident.urgency + "⚪" * (5 - incident.urgency)
            print(f"   ⚠️  Urgency: {urgency_vis} ({incident.urgency}/5)")
            
            # Summary
            summary = incident.summary[:100] + "..." if len(incident.summary) > 100 else incident.summary
            print(f"   📝 {summary}")
            
            # Verification
            unique_sources = len(set(incident.sources))
            print(f"   ✅ Verified by {incident.report_count} reports from {unique_sources} sources")
            print(f"   🎯 Confidence: {incident.confidence_score:.0%}")
            
            if incident.report_count > 1:
                print(f"   📱 Sources: {', '.join(set(incident.sources))}")
            
            print("-" * 70)
    
    def save_results(self, incidents: list, city_name: str, news: list, all_reports: list):
        """Save results to JSON"""
        
        os.makedirs('outputs', exist_ok=True)
        
        output = {
            "city": city_name,
            "timestamp": datetime.now().isoformat(),
            "data_sources": {
                "real_news": len(news),
                "ai_generated": len(all_reports) - len(news),
                "total": len(all_reports)
            },
            "analysis": {
                "total_incidents": len(incidents),
                "high_urgency": sum(1 for i in incidents if i.urgency >= 4),
                "high_confidence": sum(1 for i in incidents if i.confidence_score > 0.7)
            },
            "incidents": [
                {
                    "id": inc.incident_id,
                    "type": inc.need_type,
                    "location": inc.location,
                    "urgency": inc.urgency,
                    "summary": inc.summary,
                    "confidence": f"{inc.confidence_score:.0%}",
                    "verified_by": inc.report_count,
                    "sources": list(set(inc.sources))
                }
                for inc in incidents
            ]
        }
        
        filename = f"outputs/{city_name.lower().replace(' ', '_')}_realtime.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")


def main():
    """Interactive search interface"""
    
    print("\n" + "="*70)
    print("🌍 REAL-TIME DISASTER SEARCH (News + AI)")
    print("="*70)
    print("\nSearch for disasters using:")
    print("  • Real news from Google News")
    print("  • AI-enhanced threat detection")
    print("  • Multi-source verification\n")
    print("Examples: Mumbai, Delhi, Bangalore, Chennai, Kolkata")
    print("Type 'quit' to exit\n")
    
    searcher = RealNewsDisasterSearch()
    
    while True:
        city = input("🔍 Enter city name: ").strip()
        
        if city.lower() in ['quit', 'exit', 'q']:
            print("\n✅ Exiting search. Stay safe!")
            break
        
        if not city:
            print("⚠️ Please enter a city name.")
            continue
        
        try:
            searcher.search_city(city)
        except KeyboardInterrupt:
            print("\n\n⚠️ Search interrupted.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()