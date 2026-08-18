from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np
from models.schema import Need, UniqueIncident
from typing import List
import hashlib


class DeduplicationAgent:
    def __init__(self, similarity_threshold=0.75):
        self.similarity_threshold = similarity_threshold

    def _text_similarity(self, text1: str, text2: str) -> float:
        try:
            matrix = TfidfVectorizer().fit_transform([text1, text2]).toarray()
            return cosine_similarity([matrix[0]], [matrix[1]])[0][0]
        except Exception:
            return 0.0

    def deduplicate_clustering(self, needs: List[Need]) -> List[UniqueIncident]:
        if not needs:
            return []
        if len(needs) < 2:
            return self.deduplicate_simple(needs)

        try:
            corpus   = [n.summary for n in needs]
            matrix   = TfidfVectorizer().fit_transform(corpus).toarray()

            clustering = DBSCAN(
                eps=1 - self.similarity_threshold,
                min_samples=1,
                metric='cosine'
            ).fit(matrix)

            clusters = {}
            for idx, label in enumerate(clustering.labels_):
                clusters.setdefault(label, []).append(needs[idx])

            unique_incidents = []
            for cluster_needs in clusters.values():
                primary = cluster_needs[0]
                unique_incidents.append(UniqueIncident(
                    incident_id      = self._generate_id(primary),
                    need_type        = primary.need_type,
                    location         = primary.location,
                    urgency          = max(n.urgency for n in cluster_needs),
                    summary          = primary.summary,
                    report_count     = len(cluster_needs),
                    sources          = [n.source for n in cluster_needs],
                    original_reports = cluster_needs
                ))
            return unique_incidents

        except Exception:
            return self.deduplicate_simple(needs)

    def deduplicate_simple(self, needs: List[Need]) -> List[UniqueIncident]:
        unique_incidents = []
        for need in needs:
            matched = False
            for incident in unique_incidents:
                sim = self._text_similarity(
                    need.summary,
                    incident.original_reports[0].summary
                )
                if sim >= self.similarity_threshold:
                    incident.original_reports.append(need)
                    incident.report_count += 1
                    incident.sources.append(need.source)
                    matched = True
                    break
            if not matched:
                unique_incidents.append(UniqueIncident(
                    incident_id      = self._generate_id(need),
                    need_type        = need.need_type,
                    location         = need.location,
                    urgency          = need.urgency,
                    summary          = need.summary,
                    sources          = [need.source],
                    original_reports = [need]
                ))
        return unique_incidents

    def _generate_id(self, need: Need) -> str:
        content = f"{need.need_type}_{need.location}_{need.summary[:50]}"
        return f"INC_{hashlib.md5(content.encode()).hexdigest()[:8].upper()}"


class CrossReferenceAgent:
    def calculate_confidence(self, incident: UniqueIncident) -> float:
        score  = min(incident.report_count / 5.0, 0.5)
        score += min(len(set(incident.sources)) / 3.0, 0.3)
        if incident.report_count > 1:
            variance = np.var([n.urgency for n in incident.original_reports])
            score += 0.2 if variance < 0.5 else (0.1 if variance < 1.0 else 0)
        else:
            score += 0.1
        return min(score, 1.0)

    def verify_incidents(self, incidents: List[UniqueIncident]) -> List[UniqueIncident]:
        for incident in incidents:
            incident.confidence_score = self.calculate_confidence(incident)
        incidents.sort(key=lambda x: x.confidence_score, reverse=True)
        return incidents
