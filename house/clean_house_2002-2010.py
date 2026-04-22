import os
import numpy as np
import pandas as pd
from difflib import get_close_matches

CYCLES = [2002 + 2*k for k in range(5)]

COLUMN_ALIASES = {
    "cand_id": ["FEC ID#", "FEC ID", "CANDIDATE ID", "CAND_ID"],
    "state": ["STATE ABBREVIATION", "STATE ABBR", "STATE"],
    "district": ["D", "DISTRICT", "DIST"],
    "cand_name_first": ["CANDIDATE NAME (First)", "FIRST NAME"],
    "cand_name_last": ["Candidate Name (Last)", "CANDIDATE NAME (Last)", "LAST NAME"],
    "party": ["PARTY", "PARTY ABBR"],
    "votes": ["GENERAL RESULTS", "GENERAL ", "GENERAL VOTES", "GENERAL ELECTION VOTES", "VOTES"],
    "vote_share": ["GENERAL %", "VOTE SHARE"],
}

def normalize(col):
    return col.strip().upper()

def resolve_columns(df, aliases, fuzzy=True, cutoff=0.8):
    resolved = {}
    cols = list(df.columns)

    for canon, options in aliases.items():
        found = None

        for opt in options:
            if opt in cols:
                found = opt
                break

        if not found:
            for opt in options:
                matches = [c for c in cols if c.lower() == opt.lower()]
                if matches:
                    found = matches[0]
                    break

        # fuzzy fallback
        if not found and fuzzy:
            for opt in options:
                matches = get_close_matches(opt, cols, n=1, cutoff=cutoff)
                if matches:
                    found = matches[0]
                    break

        if not found:
            raise ValueError(f"Could not resolve column for {canon}")

        resolved[found] = canon

    return df.rename(columns=resolved)


def load_and_clean(cycle):

    file_path = f'./raw/house_{cycle}.csv'

    df = pd.read_csv(file_path, dtype=str, encoding="latin-1")

    df.dropna(how='all', inplace=True)

    df.columns = [normalize(c) for c in df.columns]

    print('\nshape initial: ', np.shape(df))

    df = resolve_columns(df, {k: [normalize(opt) for opt in v] for k, v in COLUMN_ALIASES.items()})

    inclusion = ['cand_id', 'votes']

    df.dropna(subset=inclusion, inplace=True)
    df = df[~df['district'].str.contains('UNEXPIRED', case=False, na=False)]
    df = df[~df['RUNOFF %'].str.contains('combined', case=False, na=False)]

    print('\nshape after filtering on general elections and dropna on essential cols:' , np.shape(df))

    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

    df['cycle'] = cycle
    df = df.apply(lambda col: col.astype(str).str.replace(r'^[\s\\/]+|[\s\\/]+$', '', regex=True) if pd.api.types.is_string_dtype(col) or col.dtype == "object" else col)
    df = df[df['cand_id'].str.startswith('H', na=False)]
    df["state"] = df["state"].str.upper().str.strip()
    df["district"] = df["district"].str.extract(r"(\d+)", expand=False).fillna("0").astype(int)
    df['party'] = df['party'].str.split(r'[(/\*]').str[0]
    df['party'] = df['party'].replace({'R':'REP', 'D':'DEM'})
    df["votes_raw"] = df["votes"].str.strip()
    df["unopposed"] = df["votes_raw"].eq("Unopposed")
    df["votes"] = pd.to_numeric(df["votes_raw"].str.replace(",", "", regex=False), errors="coerce").astype("Int64")
    df = df[df["unopposed"] | df["votes"].notna()]

    df["vote_share"] = df["vote_share"].str.replace("%", "", regex=False).astype(float)

    if df["vote_share"].max() > 1.5:
        df["vote_share"] /= 100

    df.loc[df["unopposed"], "vote_share"] = 1.0
    df.drop(columns=['votes_raw'], inplace=True)

    # derive electoral outcome: winner is the candidate with the most votes in each state-district pair

    df["outcome"] = 0
    contested = df[~df["unopposed"]]
    winner_idx = contested.groupby(["state", "district"])["votes"].idxmax()
    df.loc[winner_idx.dropna(), "outcome"] = 1
    df.loc[df["unopposed"], "outcome"] = 1

    # synthesise first/last name columns when absent
    if "cand_name_first" not in df.columns:
        df["cand_name_first"] = pd.NA
    if "cand_name_last" not in df.columns:
        df["cand_name_last"] = pd.NA

    ordered_cols = ['cand_id', 'cycle', 'state', 'district', 'cand_name_first', 'cand_name_last', 'party', 'votes', 'vote_share', 'outcome', 'unopposed']

    df = df[ordered_cols].reset_index(drop=True)

    print('\nshape after dropping write-ins, misc, and ultra low vote-share cands: ', np.shape(df))
    print()
    print()
    bad_groups(df)
    print()
    print()
    df = infer_vote_share(df)
    print()
    print()
    bad_groups(df)
    print()
    print()
    df = dedup(df)
    bad_groups(df)
    print('\nshape after dedup on fusion candidates, erroneous duplicates, etc.: ', np.shape(df))

    df.to_csv(f'clean/fec_house_results_{cycle}.csv', index=False)
    df.to_parquet(f'clean/fec_house_results_{cycle}.parquet', index=False)


def bad_groups(df):

    voteshare = df.groupby(["state", "district"])["vote_share"].sum()

    bad_groups = voteshare[(voteshare < 0.95) | (voteshare > 1.05)]

    print(bad_groups)


def infer_vote_share(df: pd.DataFrame) -> pd.DataFrame:

    contest_totals = df.groupby(["state", "district"])["votes"].transform("sum")

    missing = df["vote_share"].isna() & df["votes"].notna() & contest_totals.gt(0)

    df.loc[missing, "vote_share"] = df.loc[missing, "votes"] / contest_totals[missing]

    return df

def dedup(df):

    dup_keys = ["cycle", "state", "district", "cand_id"]

    df_unopposed = df[df["unopposed"]].copy()
    df_contested = df[~df["unopposed"]].copy()

    dupes = df_contested.duplicated(subset=dup_keys, keep=False)

    if dupes.any():
        anchor_idx = df_contested.groupby(dup_keys)["votes"].idxmax()

        df_contested = (df_contested.loc[anchor_idx].drop(columns=["votes", "vote_share"]).merge(
                df_contested.groupby(dup_keys, as_index=False)[["votes", "vote_share"]].sum(),
                on=dup_keys,
                how="left"))

    df = pd.concat([df_contested, df_unopposed], ignore_index=True)

    return df


if __name__ == '__main__':

    for cycle in CYCLES:
        try:
            print('---------------------')
            print(f'\nCycle: {cycle}')
            load_and_clean(cycle)
        except Exception as e:
            print(f'Error in {cycle}:', e)
        print('---------------------')