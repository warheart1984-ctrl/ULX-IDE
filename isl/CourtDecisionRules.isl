// CourtDecisionRules.isl
// ISL v1.2 Contract for Court Decision Logic

contract CourtDecisionRules {
    rule uphold(replay_ok : Bool, gov_ok : Bool, ch : PCR_CH) {
        require replay_ok;
        require gov_ok;
        if weak_challenge(ch) -> return "upheld";
    }

    rule overturn(replay_ok : Bool, gov_ok : Bool, ch : PCR_CH) {
        if strong_evidence(ch) -> return "overturned";
    }

    rule amend(ch : PCR_CH) {
        if rule_gap(ch) -> return "amended";
    }

    rule remand(ch : PCR_CH) {
        if missing_evidence(ch) -> return "remanded";
    }
}
