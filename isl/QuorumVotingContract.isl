// QuorumVotingContract.isl
// ISL v1.2 Contract for Constitutional Quorum Voting

contract QuorumVotingContract {
    type Voter;
    type ReplayContext;
    type GovernanceContext;

    enum VoteType {
        Approve,
        Reject,
        Challenge,
        Abstain
    }

    field Q_Set : Set<Voter>;
    field participationThreshold : Float;   // e.g. 0.70
    field approvalThreshold      : Float;   // e.g. 0.66

    artifact QuorumVoteRecord {
        field voterID              : Voter;
        field voteType             : VoteType;
        field justification        : Text;
        field replayContext        : ReplayContext;
        field governanceContext    : GovernanceContext;
        field timestamp            : Time;
    }

    rule QuorumSatisfied(votes : Set<QuorumVoteRecord>) {
        let participants = distinctVoters(votes);
        let participationRatio = size(participants) / size(Q_Set);

        require participationRatio >= participationThreshold;

        let approvals = countVotes(votes, VoteType.Approve);
        let approvalRatio = approvals / size(participants);

        require approvalRatio >= approvalThreshold;
    }
}
