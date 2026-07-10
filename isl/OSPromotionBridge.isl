// OSPromotionBridge.isl
// ISL v1.2 Contract for OS-Promotion Integration

contract OSPromotionBridge {
    rule promote_os_component(pr : ProcessRecord, cpr : CPR) {
        require cpr.substrate == pr.pid;
        update_status(pr, "running");
    }

    rule rollback_os_component(pr : ProcessRecord, rbr : RBR) {
        if rbr.targetSubstrateID == pr.pid -> update_status(pr, "terminated");
    }
}
