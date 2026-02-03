from models import ExtractedSignals, RiskAssessment

class RiskEngine:
    def compute_risk(self, signals: ExtractedSignals) -> RiskAssessment:
        score = 0.0
        triggered = []

        if signals.urgency_detected:
            score += 0.4
            triggered.append("Urgency Detected")
        
        if signals.sensitive_info_request:
            score += 0.5
            triggered.append("Sensitive Info Request")
            
        if signals.suspicious_links:
            score += 0.3
            triggered.append("Suspicious Links")
            
        # Cap score at 1.0
        final_score = min(score, 1.0)
        
        return RiskAssessment(
            rule_risk_score=final_score,
            triggered_rules=triggered
        )
