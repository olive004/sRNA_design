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


def count_Un(seq: str) -> int:
    """
    Return the length of the longest consecutive U (or T) run.
    Case-insensitive.
    """
    s = seq.upper()
    nuc = 'U' if 'T' not in s else 'T'
    pattern = re.compile(rf'{nuc}+')
    return max((len(m.group()) for m in pattern.finditer(s)), default=0)


def count_An(seq: str) -> int:
    s = seq.upper()
    pattern = re.compile(r'A+')
    return max((len(m.group()) for m in pattern.finditer(s)), default=0)


def count_An_norm(seq: str) -> float:
    c = count_An(seq)
    return c / len(seq) if len(seq) > 0 else 0.0


def count_A_richness(seq: str) -> float:
    seq = seq.upper()
    nuc = 'A'  # 'U' if 'T' not in seq else 'T'
    return seq.count(nuc) / len(seq) if len(seq) > 0 else 0.0


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