// CSchedulingContract.isl
// ISL v1.2 Contract for Constitutional OS Scheduling

contract CScheduling {
    type PID;

    artifact ScheduleDecision {
        field pid      : PID;
        field priority : Int;
        field reason   : Text;
        field time     : Time;
    }

    rule schedule(pr : ProcessRecord) {
        let p = compute_priority(pr);
        create ScheduleDecision {
            pid      = pr.pid;
            priority = p;
            reason   = "constitutional scheduling";
        };
    }
}
