// ConstitutionalLifecycleEngineContract.isl
// ISL v1.2 Contract for Constitutional Lifecycle Engine (CLE)

contract ConstitutionalLifecycleEngine {
    enum LState {
        Intent,
        Evidence,
        Planning,
        Execution,
        Validation,
        Replay,
        FederatedReview,
        Quorum,
        Promotion,
        Stewardship,
        Evolution
    }

    artifact LifecycleRecord {
        field artifact_id : ArtifactID;
        field state       : LState;
        field time        : Time;
        field actor       : Actor;
        field reason      : Text;
        field payload     : Artifact;
    }

    rule to_evidence(a : ArtifactID, peb : PEB) {
        require current_lifecycle_state(a) == Intent;
        require peb.evidence != null;
        emit_lifecycle(a, Evidence, peb);
    }

    rule to_planning(a : ArtifactID, plan : PlanArtifact) {
        require current_lifecycle_state(a) == Evidence;
        emit_lifecycle(a, Planning, plan);
    }

    rule to_execution(a : ArtifactID, exec : ExecutionTrace) {
        require current_lifecycle_state(a) == Planning;
        emit_lifecycle(a, Execution, exec);
    }

    rule to_validation(a : ArtifactID, val : ValidationReport) {
        require current_lifecycle_state(a) == Execution;
        emit_lifecycle(a, Validation, val);
    }

    rule to_replay(a : ArtifactID, replay : ReplayLog) {
        require current_lifecycle_state(a) == Validation;
        emit_lifecycle(a, Replay, replay);
    }

    rule to_federated_review(a : ArtifactID, fpe : FPE) {
        require current_lifecycle_state(a) == Replay;
        emit_lifecycle(a, FederatedReview, fpe);
    }

    rule to_quorum(a : ArtifactID, votes : Set<QVR>) {
        require current_lifecycle_state(a) == FederatedReview;
        emit_lifecycle(a, Quorum, votes);
    }

    rule to_promotion(a : ArtifactID, cpr : CPR) {
        require current_lifecycle_state(a) == Quorum;
        emit_lifecycle(a, Promotion, cpr);
    }

    rule to_stewardship(a : ArtifactID, steward : StewardshipRecord) {
        require current_lifecycle_state(a) == Promotion;
        emit_lifecycle(a, Stewardship, steward);
    }

    rule to_evolution(a : ArtifactID, evo : EvolutionRecord) {
        require current_lifecycle_state(a) == Stewardship;
        emit_lifecycle(a, Evolution, evo);
    }

    action emit_lifecycle(a : ArtifactID, st : LState, payload : Artifact) {
        create LifecycleRecord {
            artifact_id = a;
            state       = st;
            time        = now();
            actor       = current_actor();
            reason      = "lifecycle transition";
            payload     = payload;
        };
    }
}
