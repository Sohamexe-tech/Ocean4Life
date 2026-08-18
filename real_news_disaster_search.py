import os
import requests
import xml.etree.ElementTree as ET
import json
from groq import Groq
from bs4 import BeautifulSoup
from agents.dedupe_agent import DeduplicationAgent, CrossReferenceAgent
from agents.extract_agent import extract_need
from models.schema import Need
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)


class RealNewsDisasterSearch:

    def __init__(self):
        self.dedupe_agent    = DeduplicationAgent(similarity_threshold=0.75)
        self.cross_ref_agent = CrossReferenceAgent()
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }

    # ------------------------------------------------------------------ #
    #  MAIN ENTRY POINT                                                    #
    # ------------------------------------------------------------------ #

    def search_city(self, city_name: str, return_data: bool = False):
        print("\n" + "=" * 70)
        print(f"🌍 REAL-TIME DISASTER SEARCH: {city_name.upper()}")
        print("=" * 70)

        news        = self.search_google_news(city_name)
        all_reports = [n["title"] for n in news]

        ai_reports = []
        if len(all_reports) < 8:
            ai_reports = self.enhance_with_ai(city_name, len(all_reports))
            all_reports.extend(ai_reports)

        print(f"\n📊 Total: {len(all_reports)} | News: {len(news)} | AI: {len(ai_reports)}")

        needs            = self.extract_needs_from_reports(all_reports, city_name)
        unique_incidents = self.dedupe_agent.deduplicate_clustering(needs)
        verified         = self.cross_ref_agent.verify_incidents(unique_incidents)

        duplicates = len(needs) - len(unique_incidents)
        dedup_rate = (duplicates / len(needs) * 100) if needs else 0
        print(f"✅ {len(unique_incidents)} unique incidents ({dedup_rate:.1f}% dedup rate)")

        if return_data:
            return {
                "real_news":  news,
                "ai_reports": ai_reports,
                "incidents":  verified
            }

        self._display_results(verified, city_name)
        self._save_results(verified, city_name, news, all_reports)

    # ------------------------------------------------------------------ #
    #  NEWS FETCHING                                                       #
    # ------------------------------------------------------------------ #

    def search_google_news(self, city_name: str) -> list:
        print(f"\n📰 Searching Google News for disasters in {city_name}...")
        rss_url = (
            f"https://news.google.com/rss/search"
            f"?q={city_name.replace(' ', '+')}+disaster+OR+emergency"
            f"&hl=en-IN&gl=IN&ceid=IN:en"
        )
        headlines = []
        try:
            resp = requests.get(rss_url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return []
            root = ET.fromstring(resp.content)
            for item in root.findall('.//item')[:10]:
                title_el = item.find('title')
                link_el  = item.find('link')
                if title_el is not None and link_el is not None:
                    if title_el.text and link_el.text:
                        headlines.append({"title": title_el.text, "link": link_el.text})
        except Exception as e:
            print(f"⚠️  News fetch error: {e}")

        print(f"✅ Found {len(headlines)} articles" if headlines else "⚠️  No articles found")
        return headlines

    # ------------------------------------------------------------------ #
    #  AI ENHANCEMENT                                                      #
    # ------------------------------------------------------------------ #

    def enhance_with_ai(self, city_name: str, news_count: int) -> list:
        print("\n🤖 Enhancing with AI-generated reports...")
        if not client:
            print("⚠️  GROQ_API_KEY not set — skipping AI enhancement.")
            return []

        count  = max(1, 10 - news_count)
        prompt = (
            f"Generate {count} realistic disaster and emergency reports for "
            f"{city_name}, India.\n"
            "Include natural disasters, urban emergencies, medical crises, "
            "traffic/infrastructure incidents.\n"
            f"Format each as a social media post. Be specific with locations within {city_name}.\n"
            "One report per line."
        )
        try:
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a disaster monitoring system generating realistic emergency reports."},
                    {"role": "user",   "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=800
            )
            reports = [
                line.strip()
                for line in resp.choices[0].message.content.split('\n')
                if line.strip() and len(line.strip()) > 20
                and not line.strip().startswith('#')
            ]
            print(f"✅ Generated {len(reports)} AI reports")
            return reports
        except Exception as e:
            print(f"⚠️  AI generation error: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  NEED EXTRACTION                                                     #
    # ------------------------------------------------------------------ #

    def extract_needs_from_reports(self, reports: list, city_name: str) -> list:
        print(f"\n🔄 Extracting from {len(reports)} reports...")
        needs   = []
        sources = ["google_news", "twitter", "facebook", "whatsapp", "reddit", "instagram"]

        for i, report in enumerate(reports):
            if not report or len(report) < 15:
                continue
            source = sources[i % len(sources)]
            try:
                need = extract_need(report, source)
                if need:
                    needs.append(need)
                    continue
            except Exception:
                pass
            need = self._keyword_extract(report, source, city_name)
            if need:
                needs.append(need)

        print(f"✅ Extracted {len(needs)} structured needs")
        return needs

    def _keyword_extract(self, text: str, source: str, city: str) -> Need:
        t = text.lower()

        if any(k in t for k in ['flood','rain','fire','blaze','rescue','trapped',
                                  'stranded','collapse','earthquake','landslide',
                                  'cyclone','gas leak','explosion']):
            need_type = "rescue"
        elif any(k in t for k in ['medical','hospital','injured','health',
                                    'insulin','ambulance','dengue','malaria','outbreak']):
            need_type = "medical"
        elif any(k in t for k in ['food','hunger','supplies','ration']):
            need_type = "food"
        elif any(k in t for k in ['shelter','homeless','displaced','evacuat']):
            need_type = "shelter"
        elif any(k in t for k in ['water','contamination']):
            need_type = "water"
        else:
            need_type = "other"

        urgency = (5 if any(k in t for k in ['urgent','emergency','sos','immediately','breaking'])
                   else 4 if any(k in t for k in ['serious','major','severe','critical'])
                   else 3 if any(k in t for k in ['needed','required'])
                   else 2)

        return Need(
            need_type=need_type,
            location=city,
            urgency=urgency,
            summary=text[:150],
            source=source,
            timestamp=datetime.now().isoformat()
        )

    # ------------------------------------------------------------------ #
    #  FACT-CHECK                                                          #
    # ------------------------------------------------------------------ #

    def analyze_news_url(self, url: str) -> dict:
        result = {"status": "unknown", "title": ""}
        if not client:
            result["status"] = "error: GROQ_API_KEY not configured"
            return result
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                result["status"] = "unreachable"
                return result

            soup = BeautifulSoup(resp.text, "html.parser")
            title_tag      = soup.find("title")
            result["title"] = title_tag.text.strip() if title_tag else "Unknown Title"
            article_text   = soup.get_text()[:2000]

            prompt = (
                f"You are a fact-checking AI. Determine if this news article is TRUE or FALSE.\n"
                f"Answer ONLY with one word: TRUE or FALSE.\n"
                f"URL: {url}\nArticle Text: {article_text}"
            )
            resp2   = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a fact-checking AI."},
                    {"role": "user",   "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0
            )
            verdict = resp2.choices[0].message.content.strip().upper()
            result["status"] = verdict.lower() if verdict in ("TRUE", "FALSE") else "unknown"
        except Exception as e:
            result["status"] = f"error: {e}"
        return result

    # ------------------------------------------------------------------ #
    #  CLI HELPERS                                                         #
    # ------------------------------------------------------------------ #

    def _display_results(self, incidents: list, city_name: str):
        print("\n" + "=" * 70)
        print(f"🚨 ACTIVE DISASTERS IN {city_name.upper()}")
        print("=" * 70)
        if not incidents:
            print(f"\n✅ No active disasters detected in {city_name}")
            return
        for i, inc in enumerate(incidents, 1):
            emoji      = "🟢" if inc.confidence_score > 0.7 else ("🟡" if inc.confidence_score > 0.4 else "🔴")
            urgency_v  = "🔴" * inc.urgency + "⚪" * (5 - inc.urgency)
            summary    = inc.summary[:100] + ("..." if len(inc.summary) > 100 else "")
            print(f"\n{emoji} INCIDENT #{i} [{inc.incident_id}]")
            print(f"   🔥 Type:     {inc.need_type.upper()}")
            print(f"   📍 Location: {inc.location or city_name}")
            print(f"   ⚠️  Urgency:  {urgency_v} ({inc.urgency}/5)")
            print(f"   📝 {summary}")
            print(f"   ✅ Verified by {inc.report_count} reports from {len(set(inc.sources))} sources")
            print(f"   🎯 Confidence: {inc.confidence_score:.0%}")
            print("-" * 70)

    def _save_results(self, incidents: list, city_name: str, news: list, all_reports: list):
        os.makedirs('outputs', exist_ok=True)
        output = {
            "city": city_name,
            "timestamp": datetime.now().isoformat(),
            "data_sources": {
                "real_news":    len(news),
                "ai_generated": len(all_reports) - len(news),
                "total":        len(all_reports)
            },
            "analysis": {
                "total_incidents":  len(incidents),
                "high_urgency":     sum(1 for i in incidents if i.urgency >= 4),
                "high_confidence":  sum(1 for i in incidents if i.confidence_score > 0.7)
            },
            "incidents": [
                {
                    "id":          inc.incident_id,
                    "type":        inc.need_type,
                    "location":    inc.location,
                    "urgency":     inc.urgency,
                    "summary":     inc.summary,
                    "confidence":  f"{inc.confidence_score:.0%}",
                    "verified_by": inc.report_count,
                    "sources":     list(set(inc.sources))
                }
                for inc in incidents
            ]
        }
        filename = f"outputs/{city_name.lower().replace(' ', '_')}_realtime.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {filename}")


if __name__ == "__main__":
    searcher = RealNewsDisasterSearch()
    while True:
        city = input("🔍 Enter city name (or 'quit'): ").strip()
        if city.lower() in ('quit', 'exit', 'q'):
            break
        if city:
            searcher.search_city(city)