// CourtPromotionBridge.isl
// ISL v1.2 Contract for Court-Promotion Integration

contract CourtPromotionBridge {
    type CaseID;
    type Substration;

    rule promotion_escalation(s : Substration) {
        if active_challenges(s) > 0 -> open_court_case(s);
    }

    rule apply_court_decision(s : Substration, c : CourtDecisionRecord) {
        if c.decision == "upheld"    -> finalize_promotion(s);
        if c.decision == "overturned"-> trigger_rollback(s);
        if c.decision == "amended"   -> update_rules_and_replay(s);
        if c.decision == "remanded"  -> gather_more_evidence(s);
    }
}
