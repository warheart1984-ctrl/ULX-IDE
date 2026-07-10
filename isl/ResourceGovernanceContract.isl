// ResourceGovernanceContract.isl
// ISL v1.2 Contract for Constitutional OS Resource Governance

contract ResourceGovernance {
    type ResourceID;

    artifact ResourceRecord {
        field id     : ResourceID;
        field type   : Text;   // "file", "model", "service"
        field owner  : Actor;
        field policy : Text;
        field time   : Time;
    }

    rule access(actor : Actor, res : ResourceRecord) {
        require dlap_valid(res.policy, actor);
    }
}
