// PromotionArtifacts.isl
// ISL v1.2 Artifacts for Promotion v2.0 Constitutional Consensus Protocol

artifact PromotionEvidenceBundle {
    field intentRecord        : IntentRecord;
    field executionEvidence   : ExecutionTrace;
    field governanceEvidence  : GovernanceReport;
    field lineageEvidence     : LineageSnapshot;
    field validationEvidence  : ValidationReport;
}

artifact FederatedPromotionEnvelope {
    field replayLogs              : Map<Node, ReplayLog>;
    field governanceVerdicts      : Map<Node, GovernanceVerdict>;
    field lineageImpactReports    : Map<Node, LineageReport>;
    field constitutionalJustifications : Map<Node, Justification>;
}

artifact QuorumVoteRecord {
    field voterID              : Voter;
    field voteType             : VoteType;
    field justification        : Text;
    field replayContext        : ReplayContext;
    field governanceContext    : GovernanceContext;
    field timestamp            : Time;
}

artifact PromotionChallengeRecord {
    field challengerID          : Voter | Node;
    field violationDescription  : Text;
    field evidenceRefs          : List<EvidenceRef>;
    field requestedRemediation  : Text;
    field constitutionalJustification : Text;
    field timestamp             : Time;
}

artifact ConstitutionalPromotionRecord {
    field substrateID         : SubstrateID;
    field peb                 : PromotionEvidenceBundle;
    field fpe                 : FederatedPromotionEnvelope;
    field quorumVotes         : Set<QuorumVoteRecord>;
    field challenges          : Set<PromotionChallengeRecord>;
    field finalDecision       : PromotionDecision;
    field lineageID           : LineageID;
    field timestamp           : Time;
}

artifact RollbackRecord {
    field targetSubstrateID     : SubstrateID;
    field reason                : Text;
    field evidenceBundle        : EvidenceBundle;
    field impactAnalysis        : ImpactReport;
    field quorumOrAuthorityDecision : Decision;
    field continuityPlan        : ContinuityPlan;
    field timestamp             : Time;
}

// Together these form the Constitutional Consensus Chain (CCC-Chain)
