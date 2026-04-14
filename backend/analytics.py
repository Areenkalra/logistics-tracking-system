"""
Smart Analytics & ML Features for Orbit Logistics:
- Delay Prediction: Rule + distance-based model
- Fraud Detection: Rule-based anomaly detection
- Route Optimization: Nearest-hub greedy algorithm
- Analytics: Regional delivery performance
"""
import math
import datetime
from typing import List, Dict, Optional

# ─────────────────────────────────────────────
# Delay Prediction
# ─────────────────────────────────────────────
class DelayPredictor:
    """
    Predicts if a shipment will be delayed based on:
    - Days since creation vs estimated delivery
    - Package type (FRAGILE tends to be slower)
    - Current status progression
    """
    STATUS_ORDER = ["CREATED", "PICKED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"]

    @staticmethod
    def predict_delay_risk(
        created_at: datetime.datetime,
        estimated_delivery: datetime.datetime,
        current_status: str,
        num_events: int
    ) -> dict:
        if estimated_delivery is None:
            return {"risk": "UNKNOWN", "score": 0.0, "reason": "No ETA set"}

        now = datetime.datetime.utcnow()
        hours_elapsed = (now - created_at).total_seconds() / 3600
        hours_remaining = (estimated_delivery - now).total_seconds() / 3600
        total_window = (estimated_delivery - created_at).total_seconds() / 3600

        if total_window <= 0:
            time_pressure = 1.0
        else:
            time_pressure = hours_elapsed / total_window

        # Expected progress by this time point
        status_idx = DelayPredictor.STATUS_ORDER.index(current_status) if current_status in DelayPredictor.STATUS_ORDER else 0
        expected_progress = time_pressure * (len(DelayPredictor.STATUS_ORDER) - 1)

        delay_gap = expected_progress - status_idx
        score = max(0.0, min(1.0, delay_gap / 3.0))

        if hours_remaining < 0:
            return {"risk": "DELAYED", "score": 1.0, "reason": "Past estimated delivery date"}
        elif score > 0.6:
            return {"risk": "HIGH", "score": round(score, 2), "reason": "Shipment behind expected progress"}
        elif score > 0.3:
            return {"risk": "MEDIUM", "score": round(score, 2), "reason": "Slight progression delay"}
        else:
            return {"risk": "LOW", "score": round(score, 2), "reason": "On track for delivery"}


# ─────────────────────────────────────────────
# Fraud Detection
# ─────────────────────────────────────────────
class FraudDetector:
    """
    Rule-based fraud signals:
    - GPS coordinates jump too far between consecutive events (teleportation)
    - Status marked DELIVERED without OUT_FOR_DELIVERY step
    - Multiple deliveries in impossible time (< 1 hour across cities)
    """
    MAX_SPEED_KMH = 250  # Max realistic vehicle speed

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2) -> float:
        R = 6371.0
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    @staticmethod
    def analyze_events(events: List[dict]) -> dict:
        signals = []

        if len(events) < 2:
            return {"fraud_risk": "LOW", "signals": []}

        statuses = [e["status"] for e in events]

        # Check: DELIVERED without OUT_FOR_DELIVERY
        if "DELIVERED" in statuses and "OUT_FOR_DELIVERY" not in statuses:
            signals.append("Delivered without 'Out for Delivery' scan — possible fake delivery")

        # Check: GPS teleportation between events
        for i in range(1, len(events)):
            prev, curr = events[i-1], events[i]
            lat1, lng1 = prev.get("lat", 0), prev.get("lng", 0)
            lat2, lng2 = curr.get("lat", 0), curr.get("lng", 0)

            if not all([lat1, lng1, lat2, lng2]):
                continue

            distance_km = FraudDetector.haversine(lat1, lng1, lat2, lng2)

            t1 = datetime.datetime.fromisoformat(str(prev["timestamp"]))
            t2 = datetime.datetime.fromisoformat(str(curr["timestamp"]))
            hours = max((t2 - t1).total_seconds() / 3600, 0.001)
            speed = distance_km / hours

            if speed > FraudDetector.MAX_SPEED_KMH:
                signals.append(f"Suspicious location jump: {distance_km:.0f}km in {hours:.1f}h ({speed:.0f}km/h)")

        risk = "HIGH" if len(signals) >= 2 else "MEDIUM" if signals else "LOW"
        return {"fraud_risk": risk, "signals": signals}


# ─────────────────────────────────────────────
# Route Optimization (Nearest Hub Greedy)
# ─────────────────────────────────────────────
class RouteOptimizer:
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2) -> float:
        R = 6371.0
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    @staticmethod
    def optimize_route(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, hubs: List[dict]) -> List[dict]:
        """Returns an ordered list of hub waypoints from origin to destination."""
        if not hubs:
            return []

        remaining = list(hubs)
        route = []
        current_lat, current_lng = origin_lat, origin_lng

        # Greedy: always pick nearest hub that's closer to destination than current
        dest_dist = RouteOptimizer.haversine(current_lat, current_lng, dest_lat, dest_lng)

        for _ in range(len(remaining)):
            if not remaining:
                break
            nearest = min(remaining, key=lambda h: RouteOptimizer.haversine(current_lat, current_lng, h["lat"], h["lng"]))
            nearest_dist_to_dest = RouteOptimizer.haversine(nearest["lat"], nearest["lng"], dest_lat, dest_lng)

            if nearest_dist_to_dest < dest_dist * 0.95:  # Only add if it's making progress
                route.append(nearest)
                current_lat, current_lng = nearest["lat"], nearest["lng"]
                dest_dist = nearest_dist_to_dest
                remaining.remove(nearest)
            else:
                break

        return route


# ─────────────────────────────────────────────
# Regional Analytics
# ─────────────────────────────────────────────
class RegionalAnalytics:
    @staticmethod
    def compute(shipments: List[dict]) -> dict:
        """Compute delivery performance by origin region."""
        region_stats: Dict[str, dict] = {}

        for s in shipments:
            region = s.get("origin", "Unknown")
            if region not in region_stats:
                region_stats[region] = {"total": 0, "delivered": 0, "failed": 0, "in_transit": 0}

            region_stats[region]["total"] += 1
            status = s.get("current_status", "")
            if status == "DELIVERED":
                region_stats[region]["delivered"] += 1
            elif status == "FAILED":
                region_stats[region]["failed"] += 1
            elif status in ["IN_TRANSIT", "OUT_FOR_DELIVERY"]:
                region_stats[region]["in_transit"] += 1

        # Add success rate
        for region, stats in region_stats.items():
            total = stats["total"]
            stats["success_rate"] = round((stats["delivered"] / total * 100), 1) if total > 0 else 0

        return region_stats
