import re


def count_ARN_motifs(seq: str) -> int:
    seq = seq.upper()
    pattern = re.compile(r"A[AG][ACGT]")
    return sum(1 for _ in pattern.finditer(seq))


def count_AAN_motifs(seq: str) -> int:
    seq = seq.upper()
    pattern = re.compile(r"AA[ACGT]")
    return sum(1 for _ in pattern.finditer(seq))


def drop_subheader(df):
    df = df.T.reset_index(drop=True).set_index(0).T
    df = df[df.index.notna()]
    df = df.loc[:, df.notna().any()]
    return df