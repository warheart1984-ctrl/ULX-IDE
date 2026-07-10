// KnowledgeEvidenceContract.isl
// ISL v1.2 Contract for Knowledge Evidence Chains

contract KnowledgeEvidence {
    type EvidenceID;

    artifact KEvidence {
        field id         : EvidenceID;
        field knowledge  : KnowledgeID;
        field data_ref   : Text;
        field method     : Text;
        field result     : Text;
        field confidence : Float;
        field time       : Time;
    }
}
