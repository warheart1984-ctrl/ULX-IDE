// ConstitutionalStateEngineContract.isl
// ISL v1.2 Contract for Constitutional State Engine (CSE)

contract ConstitutionalStateEngine {
    type ArtifactID;
    type Actor;
    type AuthorityPath;
    type Evidence;
    type Payload;

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

    artifact LifecycleEvent {
        field event_id        : Text;
        field artifact_id     : ArtifactID;
        field previous_state  : LState;
        field new_state       : LState;
        field actor           : Actor;
        field authority_valid : Bool;
        field evidence_valid  : Bool;
        field payload         : Payload;
        field time            : Time;
    }

    rule validate_authority(actor : Actor, path : AuthorityPath) {
        require dlap_valid(path, actor);
    }

    rule validate_evidence(ev : Evidence) {
        require ev != null;
    }

    rule transition(a : ArtifactID, from : LState, to : LState, actor : Actor, path : AuthorityPath, ev : Evidence, p : Payload) {
        validate_authority(actor, path);
        validate_evidence(ev);

        create LifecycleEvent {
            event_id        = uuid();
            artifact_id     = a;
            previous_state  = from;
            new_state       = to;
            actor           = actor;
            authority_valid = true;
            evidence_valid  = true;
            payload         = p;
            time            = now();
        };
    }
}
