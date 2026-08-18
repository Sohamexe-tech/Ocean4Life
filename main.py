import os
import json
from datetime import datetime
from agents.dedupe_agent import DeduplicationAgent, CrossReferenceAgent
from agents.extract_agent import extract_need
from models.schema import Need


def load_sample_data():
    try:
        with open('data/sample_posts.txt', 'r', encoding='utf-8') as f:
            posts = [line.strip() for line in f if line.strip()]
        if not posts:
            raise ValueError("File is empty")
        return posts
    except FileNotFoundError:
        print("❌ ERROR: data/sample_posts.txt not found!")
        print("Run:  python data_collectors/realtime_simulator.py")
        exit(1)
    except Exception as e:
        print(f"❌ ERROR loading data: {e}")
        exit(1)


def extract_needs_from_posts(posts):
    needs   = []
    sources = ["twitter", "facebook", "whatsapp", "reddit", "instagram"]

    for i, post in enumerate(posts):
        source = sources[i % len(sources)]
        try:
            need = extract_need(post, source)
            if need:
                needs.append(need)
                continue
        except Exception:
            pass

        t = post.lower()

        if any(k in t for k in ['food', 'water', 'supplies', 'ration']):
            need_type = "food"
        elif any(k in t for k in ['medical', 'insulin', 'medicine', 'hospital', 'ambulance']):
            need_type = "medical"
        elif any(k in t for k in ['shelter', 'displaced', 'homeless']):
            need_type = "shelter"
        elif any(k in t for k in ['rescue', 'trapped', 'stranded', 'collapse', 'fire', 'flood']):
            need_type = "rescue"
        else:
            need_type = "other"

        location_map = {
            'andheri east': 'Andheri East, Mumbai',
            'andheri':      'Andheri East, Mumbai',
            'bandra west':  'Bandra West',
            'bandra':       'Bandra West',
            'kurla':        'Kurla Station',
            'dadar':        'Dadar',
            'thane':        'Thane',
            'borivali':     'Borivali',
            'powai':        'Powai',
            'worli':        'Worli',
            'colaba':       'Colaba',
            'malad':        'Malad',
        }
        location = next((v for k, v in location_map.items() if k in t), None)

        urgency = (5 if any(k in t for k in ['urgent', 'emergency', 'immediately', 'sos', 'breaking'])
                   else 4 if any(k in t for k in ['critical', 'serious', 'breaking'])
                   else 3 if any(k in t for k in ['needed', 'required'])
                   else 2)

        needs.append(Need(
            need_type=need_type,
            location=location,
            urgency=urgency,
            summary=post[:100],
            source=source,
            timestamp=datetime.now().isoformat()
        ))

    return needs


def save_results(verified_incidents, needs):
    try:
        os.makedirs('outputs', exist_ok=True)
        total  = len(needs)
        unique = len(verified_incidents)
        output = {
            "timestamp":          datetime.now().isoformat(),
            "total_reports":      total,
            "unique_incidents":   unique,
            "deduplication_rate": f"{((total - unique) / total * 100):.1f}%" if total else "0.0%",
            "incidents": [
                {
                    "id":           inc.incident_id,
                    "type":         inc.need_type,
                    "location":     inc.location,
                    "urgency":      inc.urgency,
                    "summary":      inc.summary,
                    "confidence":   f"{inc.confidence_score:.1%}",
                    "report_count": inc.report_count,
                    "sources":      list(set(inc.sources))
                }
                for inc in verified_incidents
            ]
        }
        with open('outputs/verified_incidents.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
        return False


def run_disaster_relief_system():
    print("\n" + "=" * 70)
    print("🚨 DISASTER RELIEF RESOURCE SCOUT")
    print("=" * 70)

    print("\n📥 Loading disaster reports...")
    posts = load_sample_data()
    print(f"✅ Loaded {len(posts)} posts")

    print("\n🔄 Processing reports...")
    needs = extract_needs_from_posts(posts)
    print(f"✅ Extracted {len(needs)} structured needs")

    if not needs:
        print("❌ No valid needs extracted.")
        return

    print("\n🔍 Identifying unique incidents...")
    dedupe_agent     = DeduplicationAgent(similarity_threshold=0.75)
    unique_incidents = dedupe_agent.deduplicate_clustering(needs)

    duplicates = len(needs) - len(unique_incidents)
    dedup_rate = (duplicates / len(needs) * 100) if needs else 0
    print(f"✅ {len(unique_incidents)} unique  |  {duplicates} duplicates removed ({dedup_rate:.1f}%)")

    print("\n🔍 Cross-referencing and scoring confidence...")
    cross_ref_agent    = CrossReferenceAgent()
    verified_incidents = cross_ref_agent.verify_incidents(unique_incidents)

    print("\n" + "=" * 70)
    print("📋 VERIFIED UNIQUE INCIDENTS  (Ranked by Confidence)")
    print("=" * 70 + "\n")

    for i, inc in enumerate(verified_incidents, 1):
        emoji     = "🟢" if inc.confidence_score > 0.7 else ("🟡" if inc.confidence_score > 0.4 else "🔴")
        urgency_s = "🔴" * inc.urgency + "⚪" * (5 - inc.urgency)
        summary   = inc.summary[:80] + ("..." if len(inc.summary) > 80 else "")
        print(f"{emoji} #{i} [{inc.incident_id}]")
        print(f"   Type:      {inc.need_type.upper()}")
        print(f"   Location:  {inc.location or 'Unknown'}")
        print(f"   Urgency:   {urgency_s} ({inc.urgency}/5)")
        print(f"   Summary:   {summary}")
        print(f"   📊 {inc.report_count} reports from {len(set(inc.sources))} sources")
        print(f"   🎯 Confidence: {inc.confidence_score:.1%}")
        if inc.report_count > 1:
            print(f"   📱 Sources: {', '.join(set(inc.sources))}")
        print("-" * 70)

    high = sum(1 for i in verified_incidents if i.confidence_score > 0.7)
    med  = sum(1 for i in verified_incidents if 0.4 <= i.confidence_score <= 0.7)
    low  = sum(1 for i in verified_incidents if i.confidence_score < 0.4)

    print("\n📈 SUMMARY")
    print(f"   Total reports:     {len(needs)}")
    print(f"   Unique incidents:  {len(unique_incidents)}")
    print(f"   Dedup rate:        {dedup_rate:.1f}%")
    print(f"   🟢 High confidence: {high}")
    print(f"   🟡 Medium:          {med}")
    print(f"   🔴 Low:             {low}")

    print("\n💾 Saving results...")
    if save_results(verified_incidents, needs):
        print("✅ Saved → outputs/verified_incidents.json")

    print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    run_disaster_relief_system()