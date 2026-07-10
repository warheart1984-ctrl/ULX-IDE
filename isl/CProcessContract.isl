// CProcessContract.isl
// ISL v1.2 Contract for Constitutional OS Process Management

contract CProcess {
    type PID;

    artifact ProcessRecord {
        field pid       : PID;
        field owner     : Actor;
        field intent    : Text;
        field authority : AuthorityPath;
        field status    : Text;   // "running", "paused", "terminated"
        field time      : Time;
    }
}
