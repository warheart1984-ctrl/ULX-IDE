// ConstitutionalCourtContract.isl
// ISL v1.2 Contract for Constitutional Courts (Meta-Governance)

contract ConstitutionalCourt {
    type CaseID;
    type Substration;
    type CourtNode;

    field court_arena : Set<CourtNode>;

    artifact CourtDecisionRecord {
        field case_id      : CaseID;
        field substrate    : Substration;
        field decision     : Text;   // "upheld", "overturned", "amended", "remanded"
        field justification: Text;
        field time         : Time;
    }

    rule jurisdiction(s : Substration) {
        require s in governed_scope();
    }
}
