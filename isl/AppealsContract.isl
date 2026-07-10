// AppealsContract.isl
// ISL v1.2 Contract for Promotion Appeals to Constitutional Courts

contract PromotionAppeals {
    type CaseID;
    type PCR_CH;

    artifact AppealRecord {
        field case_id   : CaseID;
        field challenge : PCR_CH;
        field reason    : Text;
        field time      : Time;
    }

    rule escalate(ch : PCR_CH) {
        create AppealRecord {
            case_id   = new_case_id();
            challenge = ch;
            reason    = "escalated from promotion";
        };
    }
}
