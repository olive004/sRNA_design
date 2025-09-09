import re


def count_ARN_motifs(seq: str) -> int:
    seq = seq.upper()
    pattern = re.compile(r"A[AG][ACGT]")
    return sum(1 for _ in pattern.finditer(seq))


def count_AAN_motifs(seq: str) -> int:
    seq = seq.upper()
    pattern = re.compile(r"AA[ACGT]")
    return sum(1 for _ in pattern.finditer(seq))


def count_ARNn(seq: str) -> int:
    """
    Return the length (in repeats) of the longest consecutive 'ATN' run,
    where N∈{A,C,G,T}. Case-insensitive.
    """
    s = seq.upper()
    pattern = re.compile(r'(?:A[AG][ACGT])+')
    return max((len(m.group()) // 3 for m in pattern.finditer(s)), default=0)


def test_count_ARNn():
    assert count_ARNn("AAGAAGAT") == 2
    assert count_ARNn("ccAGgAtNAGGxx") == 1
    assert count_ARNn("AGGAGGA") == 2
    assert count_ARNn("AAAA") == 1
    assert count_ARNn("AATAGCAGGGAGG") == 3


def drop_subheader(df):
    df = df.T.reset_index(drop=True).set_index(0).T
    df = df[df.index.notna()]
    df = df.loc[:, df.notna().any()]
    return df


def main():
    test_count_ARNn()
    
    
if __name__ == "__main__":
    main()