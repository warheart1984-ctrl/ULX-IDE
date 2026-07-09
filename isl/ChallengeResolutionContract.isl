// ChallengeResolutionContract.isl
// ISL v1.2 Contract for Promotion Challenge Resolution

contract ChallengeResolutionContract {
    type Voter;
    type Node;
    type Substration;
    type EvidenceRef;
    type Decision;

    artifact PromotionChallengeRecord {
        field challengerID          : Voter | Node;
        field violationDescription  : Text;
        field evidenceRefs          : List<EvidenceRef>;
        field requestedRemediation  : Text;
        field constitutionalJustification : Text;
        field timestamp             : Time;
    }

    rule NoFinalizationWithActiveChallenges(substration s) {
        require activeChallenges(s) == 0;
    }

    action UpholdPromotion(substration s, challenge : PromotionChallengeRecord) {
        updateEvidence(s, challenge.evidenceRefs);
        rerunReplay(s);
        revalidateGovernance(s);
        require challengerSignOff(challenge) 
            or quorumOverride(s, challenge);
        resolveChallenge(challenge, "upheld");
    }

    action DenyPromotion(substration s, challenge : PromotionChallengeRecord) {
        abortPromotion(s);
        markExploratory(s);
        updateCPRStatus(s, "Denied via Challenge");
        resolveChallenge(challenge, "denied");
    }

    action Escalate(substration s, challenge : PromotionChallengeRecord) {
        escalateToHigherAuthority(s, challenge);
        require specialQuorum(s, challenge);
        optionally triggerEmergencyContinuity(s);
        resolveChallenge(challenge, "escalated");
    }
}
