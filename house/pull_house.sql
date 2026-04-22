with race_spine as (
    select
        er.cand_id,
        er.cycle,
        er.state,
        er.district,
        er.cand_name_first,
        er.cand_name_last,
        er.party as results_party,
        er.outcome,
        er.unopposed,
        er.votes,
        er.vote_share
    from FEC.RAW.ELECTION_RESULTS_HOUSE er
    where er.cand_id is not null
      and er.cycle between 2004 and 2022
      and er.state is not null
      and er.district is not null
),

candidate_summary_all as (
    select
        2004 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2004 t

    union all
    select
        2006 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2006 t

    union all
    select
        2008 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2008 t

    union all
    select
        2010 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2010 t

    union all
    select
        2012 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2012 t

    union all
    select
        2014 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2014 t

    union all
    select
        2016 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2016 t

    union all
    select
        2018 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2018 t

    union all
    select
        2020 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2020 t

    union all
    select
        2022 as cycle,
        t.cand_id,
        t.cand_name,
        t.cand_pty_affiliation,
        t.cand_ici,
        t.ttl_receipts,
        t.trans_from_auth,
        t.ttl_disb,
        t.trans_to_auth,
        t.coh_cop,
        t.cand_contrib,
        t.cand_loans,
        t.ttl_indiv_contrib,
        t.other_pol_cmte_contrib,
        t.pol_pty_contrib
    from FEC.RAW.CANDIDATE_SUMMARY_2022 t
)

select
    rs.cand_id,
    rs.cycle,
    rs.state,
    rs.district,

    rs.cand_name_first,
    rs.cand_name_last,
    cs.cand_name,

    rs.results_party,
    cs.cand_pty_affiliation,
    cs.cand_ici,

    rs.outcome,
    rs.unopposed,
    rs.votes,
    rs.vote_share,

    cs.ttl_receipts,
    cs.trans_from_auth,
    cs.ttl_disb,
    cs.trans_to_auth,
    cs.coh_cop,
    cs.cand_contrib,
    cs.cand_loans,
    cs.ttl_indiv_contrib,
    cs.other_pol_cmte_contrib,
    cs.pol_pty_contrib

from race_spine rs
inner join candidate_summary_all cs
    on rs.cand_id = cs.cand_id
   and rs.cycle = cs.cycle

order by rs.cycle, rs.state, rs.district, rs.results_party, rs.cand_id;