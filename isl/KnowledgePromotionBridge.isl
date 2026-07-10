// KnowledgePromotionBridge.isl
// ISL v1.2 Contract for Knowledge-Promotion Integration

contract KnowledgePromotionBridge {
    rule link_to_promotion(ka : KArtifact, cpr : CPR) {
        require cpr.substrate == ka.id;
        update_status(ka, "accepted");
    }

    rule rollback_knowledge(ka : KArtifact, rbr : RBR) {
        if rbr.targetSubstrateID == ka.id -> update_status(ka, "deprecated");
    }
}
