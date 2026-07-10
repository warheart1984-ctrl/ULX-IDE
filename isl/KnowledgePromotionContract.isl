// KnowledgePromotionContract.isl
// ISL v1.2 Contract for Knowledge Promotion

contract KnowledgePromotion {
    field min_confidence : Float;

    rule promote(ka : KArtifact, ev : Set<KEvidence>) {
        require avg(ev.confidence) >= min_confidence;
        require size(ev) > 0;
        update_status(ka, "accepted");
    }

    rule deprecate(ka : KArtifact, ev : Set<KEvidence>) {
        if strong_contradiction(ev) -> update_status(ka, "deprecated");
    }
}
