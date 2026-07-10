// KnowledgeArtifactContract.isl
// ISL v1.2 Contract for Constitutional Knowledge Layer

contract KnowledgeArtifact {
    type KnowledgeID;

    artifact KArtifact {
        field id      : KnowledgeID;
        field content : Text;
        field type    : Text;   // "model", "theory", "policy", "claim"
        field source  : Text;
        field status  : Text;   // "hypothesis", "proposed", "accepted", "deprecated"
        field time    : Time;
    }
}
