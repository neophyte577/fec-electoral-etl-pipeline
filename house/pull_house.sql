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
),

candidate_master_all as (
    select 2004 as cycle, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2004 t
    union all select 2006, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2006 t
    union all select 2008, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2008 t
    union all select 2010, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2010 t
    union all select 2012, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2012 t
    union all select 2014, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2014 t
    union all select 2016, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2016 t
    union all select 2018, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2018 t
    union all select 2020, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2020 t
    union all select 2022, t.cand_id, t.cand_pcc, t.cand_office from FEC.RAW.CANDIDATE_MASTER_2022 t
),

house_pcc as (
    select
        cand_id,
        cycle,
        cand_pcc
    from candidate_master_all
    where cand_office = 'H'
      and cand_pcc is not null
),

individual_contributions_all as (
    select 2004 as cycle, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2004 t
    union all select 2006, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2006 t
    union all select 2008, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2008 t
    union all select 2010, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2010 t
    union all select 2012, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2012 t
    union all select 2014, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2014 t
    union all select 2016, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2016 t
    union all select 2018, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2018 t
    union all select 2020, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2020 t
    union all select 2022, t.cmte_id, t.transaction_amt, t.memo_cd from FEC.RAW.INDIVIDUAL_CONTRIBUTIONS_2022 t
),

indiv_agg as (
    select
        hp.cand_id,
        hp.cycle,
        sum(ic.transaction_amt) as itemized_indiv_amount
    from house_pcc hp
    join individual_contributions_all ic
      on hp.cand_pcc = ic.cmte_id
     and hp.cycle = ic.cycle
    where ic.transaction_amt is not null
      and coalesce(ic.memo_cd, '') <> 'X'
    group by 1, 2
),

committee_contributions_all as (
    select 2004 as cycle, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2004 t
    union all select 2006, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2006 t
    union all select 2008, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2008 t
    union all select 2010, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2010 t
    union all select 2012, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2012 t
    union all select 2014, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2014 t
    union all select 2016, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2016 t
    union all select 2018, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2018 t
    union all select 2020, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2020 t
    union all select 2022, t.cand_id, t.transaction_tp, t.transaction_amt, t.memo_cd from FEC.RAW.COMMITTEE_CONTRIBUTIONS_2022 t
),

direct_outside_agg as (
    select
        cand_id,
        cycle,
        sum(case when transaction_tp = '24E' then transaction_amt else 0 end) as direct_ind_exp_support,
        sum(case when transaction_tp = '24A' then transaction_amt else 0 end) as direct_ind_exp_oppose,
        sum(case when transaction_tp = '24F' then transaction_amt else 0 end) as direct_comm_support,
        sum(case when transaction_tp = '24N' then transaction_amt else 0 end) as direct_comm_oppose,
        sum(case when transaction_tp = '24C' then transaction_amt else 0 end) as party_coord_exp
    from committee_contributions_all
    where cand_id is not null
      and transaction_amt is not null
      and transaction_tp in ('24A', '24C', '24E', '24F', '24N')
    group by 1, 2
),

race_candidates as (
    select distinct
        cand_id,
        cycle,
        state,
        district
    from race_spine
),

outside_agg as (
    select
        rc.cand_id,
        rc.cycle,
        coalesce(d.direct_ind_exp_support, 0)
            + coalesce(sum(d_opp.direct_ind_exp_oppose), 0) as ind_exp_support,
        coalesce(d.direct_ind_exp_oppose, 0)
            + coalesce(sum(d_opp.direct_ind_exp_support), 0) as ind_exp_oppose,
        coalesce(d.direct_comm_support, 0)
            + coalesce(sum(d_opp.direct_comm_oppose), 0) as comm_support,
        coalesce(d.direct_comm_oppose, 0)
            + coalesce(sum(d_opp.direct_comm_support), 0) as comm_oppose,
        coalesce(d.party_coord_exp, 0) as party_coord_exp
    from race_candidates rc
    left join direct_outside_agg d
      on rc.cand_id = d.cand_id
     and rc.cycle = d.cycle
    left join race_candidates rc_opp
      on rc.cycle = rc_opp.cycle
     and rc.state = rc_opp.state
     and rc.district = rc_opp.district
     and rc.cand_id <> rc_opp.cand_id
    left join direct_outside_agg d_opp
      on rc_opp.cand_id = d_opp.cand_id
     and rc_opp.cycle = d_opp.cycle
    group by
        rc.cand_id,
        rc.cycle,
        d.direct_ind_exp_support,
        d.direct_ind_exp_oppose,
        d.direct_comm_support,
        d.direct_comm_oppose,
        d.party_coord_exp
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
    cs.pol_pty_contrib,

    ia.itemized_indiv_amount,
    case when ia.itemized_indiv_amount is null then 1 else 0 end as itemized_indiv_missing,
    coalesce(ia.itemized_indiv_amount, 0) as itemized_indiv_amount_model,
    ia.itemized_indiv_amount / nullif(cs.ttl_indiv_contrib, 0) as itemized_indiv_share_of_indiv,
    coalesce(ia.itemized_indiv_amount, 0) / nullif(cs.ttl_indiv_contrib, 0) as itemized_indiv_share_of_indiv_model,

    coalesce(oa.ind_exp_support, 0) as ind_exp_support,
    coalesce(oa.ind_exp_oppose, 0) as ind_exp_oppose,
    coalesce(oa.comm_support, 0) as comm_support,
    coalesce(oa.comm_oppose, 0) as comm_oppose,
    coalesce(oa.party_coord_exp, 0) as party_coord_exp

from race_spine rs
inner join candidate_summary_all cs
    on rs.cand_id = cs.cand_id
   and rs.cycle = cs.cycle
left join indiv_agg ia
    on rs.cand_id = ia.cand_id
   and rs.cycle = ia.cycle
left join outside_agg oa
    on rs.cand_id = oa.cand_id
   and rs.cycle = oa.cycle

order by rs.cycle, rs.state, rs.district, rs.results_party, rs.cand_id;