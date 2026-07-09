// RollbackIntegrityContract.isl
// ISL v1.2 Contract for Rollback & Anti-Corruption Rules

contract RollbackIntegrityContract {
    type SubstrateID;
    type EvidenceBundle;
    type ImpactReport;
    type ContinuityPlan;
    type Decision;

    artifact RollbackRecord {
        field targetSubstrateID     : SubstrateID;
        field reason                : Text;
        field evidenceBundle        : EvidenceBundle;
        field impactAnalysis        : ImpactReport;
        field quorumOrAuthorityDecision : Decision;
        field continuityPlan        : ContinuityPlan;
        field timestamp             : Time;
    }

    rule RollbackTriggers(substrateID : SubstrateID) {
        trigger on replayNonDeterminism(substrateID);
        trigger on governanceViolationPostPromotion(substrateID);
        trigger on authorityPathTampering(substrateID);
        trigger on lineageCorruption(substrateID);
        trigger on latePromotionChallenge(substrateID);
    }

    action ApplyRollback(record : RollbackRecord) {
        markRevoked(record.targetSubstrateID);
        flagDependentsAtRisk(record.targetSubstrateID);
        renderRollbackBranch(record.targetSubstrateID);
        preserveContinuity(record.continuityPlan);
    }

    rule ImmutableAudit(artifactID : ID) {
        forbid retroactiveEdit(artifactID);
        allow supersedingRecord(artifactID);
    }

    rule AuthorityPathIntegrity(path : AuthorityPath) {
        require dLAPValidate(path);
        on tampering(path) {
            triggerAutomaticRollback(path.rootSubstrate);
        }
    }

    rule ReplayIntegrity(logs : ReplayLogSet) {
        require cryptographicallySigned(logs);
        on hashMismatch(logs) {
            triggerCorruptionAlert(logs);
        }
    }

    rule ConstitutionalEmergencyMode(corruptionLevel : Severity) {
        if corruptionLevel == Severe {
            expandFederation();
            increaseQuorumThresholds();
            freezePromotion();
            tightenContinuityRules();
        }
    }
}
