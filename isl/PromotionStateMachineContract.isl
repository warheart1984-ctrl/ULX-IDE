// PromotionStateMachineContract.isl
// ISL v1.2 Contract for Promotion v3.0 State Machine

contract PromotionStateMachine {
    enum PState {
        Exploratory,
        Candidate,
        EvidenceComplete,
        FederatedValidation,
        QuorumReview,
        ChallengeWindow,
        Promoted,
        Active,
        Deprecated,
        Revoked,
        Archived
    }

    artifact PromotionStateRecord {
        field substrate : Substrate;
        field state     : PState;
        field time      : Time;
        field actor     : Actor;
        field reason    : Text;
        field artifact  : Artifact;
    }

    rule to_candidate(s : Substrate, peb : PEB) {
        require current_state(s) == Exploratory;
        require peb.intent != null;
        emit_state(s, Candidate, peb);
    }

    rule to_evidence_complete(s : Substrate, peb : PEB) {
        require current_state(s) == Candidate;
        require peb.evidence != null;
        emit_state(s, EvidenceComplete, peb);
    }

    rule to_federated_validation(s : Substrate, fpe : FPE) {
        require current_state(s) == EvidenceComplete;
        require fpe.replay_logs != null;
        emit_state(s, FederatedValidation, fpe);
    }

    rule to_quorum_review(s : Substrate, votes : Set<QVR>) {
        require current_state(s) == FederatedValidation;
        require size(votes) > 0;
        emit_state(s, QuorumReview, votes);
    }

    rule to_challenge_window(s : Substrate, cpr : CPR) {
        require current_state(s) == QuorumReview;
        emit_state(s, ChallengeWindow, cpr);
    }

    rule to_promoted(s : Substrate, cpr : CPR) {
        require current_state(s) == ChallengeWindow;
        require no_active_challenges(s);
        emit_state(s, Promoted, cpr);
    }

    rule to_active(s : Substrate, cpr : CPR) {
        require current_state(s) == Promoted;
        emit_state(s, Active, cpr);
    }

    rule to_deprecated(s : Substrate, rbr : RBR) {
        require current_state(s) == Active;
        emit_state(s, Deprecated, rbr);
    }

    rule to_revoked(s : Substrate, rbr : RBR) {
        require current_state(s) in {Active, Deprecated};
        emit_state(s, Revoked, rbr);
    }

    rule to_archived(s : Substrate, rbr : RBR) {
        require current_state(s) == Revoked;
        emit_state(s, Archived, rbr);
    }

    action emit_state(s : Substrate, st : PState, a : Artifact) {
        create PromotionStateRecord {
            substrate = s;
            state     = st;
            time      = now();
            actor     = current_actor();
            reason    = "state transition";
            artifact  = a;
        };
    }
}
