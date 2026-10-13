import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from services.common.db import db

PROFILE_NAMES = [
    "SSH/Credential Brute Forcers",
    "Broad Port Scanners",
    "High-Frequency Distributed Bots",
    "Targeted Exploit Probers"
]

def run_kmeans_clustering(k: int = 4) -> Dict[str, Any]:
    """
    Applies K-Means clustering on per-IP behavior features:
    - targeted_ports_count
    - usernames_tried_count
    - request_rate
    - threat_score
    """
    profiles = db.execute_query("""
        SELECT ip, total_events, targeted_ports_count, usernames_tried_count,
               request_rate, threat_score, country, country_code, asn
        FROM ip_profiles
        ORDER BY total_events DESC
    """)

    if not profiles or len(profiles) < 3:
        return {
            "status": "insufficient_data",
            "message": "Need at least 3 active IP profiles to run K-Means clustering.",
            "total_ips": len(profiles) if profiles else 0,
            "clusters": [],
            "scatter_points": []
        }

    # Prepare feature matrix: [targeted_ports, usernames_tried, request_rate, threat_score]
    data = []
    ips = []
    for p in profiles:
        ports = float(p.get("targeted_ports_count") or 1)
        users = float(p.get("usernames_tried_count") or 0)
        rate = float(p.get("request_rate") or 1.0)
        score = float(p.get("threat_score") or 20)
        data.append([ports, users, rate, score])
        ips.append(p)

    X = np.array(data)
    actual_k = min(k, len(X))

    if SKLEARN_AVAILABLE:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        kmeans = KMeans(n_clusters=actual_k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        centers_unscaled = scaler.inverse_transform(kmeans.cluster_centers_)
    else:
        # Fallback simple deterministic binning if sklearn not present
        labels = [(int(row[3]) // 25) % actual_k for row in X]
        centers_unscaled = [[np.mean(X[:, c]) for c in range(4)] for _ in range(actual_k)]

    # Characterize and name clusters based on centers
    # Feature 0: ports, 1: usernames, 2: request_rate, 3: threat_score
    cluster_meta = []
    for c_idx in range(actual_k):
        center = centers_unscaled[c_idx] if len(centers_unscaled) > c_idx else [1, 1, 1, 50]
        avg_ports = round(float(center[0]), 1)
        avg_users = round(float(center[1]), 1)
        avg_rate = round(float(center[2]), 1)
        avg_score = round(float(center[3]), 1)

        # Dynamic name selection based on dominant behavioral trait
        if avg_users >= 5 or (avg_users > avg_ports and avg_users >= 2):
            profile_name = "SSH/Credential Brute Forcers"
            description = "High volume of authentication attempts across standard services."
            risk_level = "High"
        elif avg_ports >= 4:
            profile_name = "Broad Port Scanners"
            description = "Sweeps multiple destination ports searching for perimeter vulnerabilities."
            risk_level = "Medium"
        elif avg_rate >= 15 or avg_score >= 80:
            profile_name = "High-Frequency Distributed Bots"
            description = "Rapid, continuous bursts of requests likely part of a synchronized botnet."
            risk_level = "Critical"
        else:
            profile_name = "Targeted Exploit Probers"
            description = "Low-and-slow reconnaissance targeting isolated endpoint vulnerabilities."
            risk_level = "Medium"

        cluster_meta.append({
            "cluster_id": c_idx,
            "profile_name": profile_name,
            "description": description,
            "risk_level": risk_level,
            "center": {
                "avg_targeted_ports": avg_ports,
                "avg_usernames_tried": avg_users,
                "avg_request_rate": avg_rate,
                "avg_threat_score": avg_score
            },
            "member_count": 0,
            "top_ips": []
        })

    # Prepare scatter data and update database profiles
    scatter_points = []
    for idx, (p, label) in enumerate(zip(ips, labels)):
        c_label = int(label)
        c_name = cluster_meta[c_label]["profile_name"]
        cluster_meta[c_label]["member_count"] += 1
        
        if len(cluster_meta[c_label]["top_ips"]) < 5:
            cluster_meta[c_label]["top_ips"].append({
                "ip": p["ip"],
                "country": p.get("country", "Unknown"),
                "threat_score": p.get("threat_score", 0)
            })

        scatter_points.append({
            "ip": p["ip"],
            "cluster_id": c_label,
            "profile_name": c_name,
            "x": round(float(p.get("request_rate") or 1.0), 2),     # Request Rate
            "y": int(p.get("targeted_ports_count") or 1),            # Targeted Ports
            "size": max(5, int(p.get("usernames_tried_count") or 1) * 2), # Username attempts
            "threat_score": int(p.get("threat_score") or 20),
            "country": p.get("country", "Unknown")
        })

        # Save assigned cluster to database
        try:
            db.execute_commit(
                "UPDATE ip_profiles SET cluster_label = ?, cluster_name = ? WHERE ip = ?",
                (c_label, c_name, p["ip"])
            )
        except Exception as e:
            logger.error(f"Failed to update cluster for IP {p['ip']}: {e}")

    return {
        "status": "success",
        "total_ips": len(ips),
        "k_clusters": actual_k,
        "clusters": cluster_meta,
        "scatter_points": scatter_points
    }
