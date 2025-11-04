import re
import pandas as pd
import numpy as np


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


def load_df_Reis(excel_file, sheet_name_proteins: str):
    df = pd.concat([excel_file.parse(sheet_name_proteins, index_col=0),
                    excel_file.parse('RBS Calculator v2.1', index_col=0)], axis=1)
    df = df.loc[:, ~df.T.duplicated()]
    df = df.rename(columns={'PROT.MEAN': 'Mean protein (fluo)'})
    df['Dataset source'] = sheet_name_proteins
    df['log Mean protein (fluo)'] = np.log10(df['Mean protein (fluo)'])
    # df_aux = excel_file.parse(name_sheets[1], index_col=0)
    # df['used_mRNA_sequence'] = df_aux['used_mRNA_sequence']
    df_aux = excel_file.parse('RBS Calculator v2.0', index_col=0)
    df['used_mRNA_sequence'] = df_aux['used_mRNA_sequence']
    df['predicted_5pUTR_2.0'] = df_aux['predicted_5pUTR']
    df['predicted_CDS_2.0'] = df_aux['predicted_CDS']
    df['TIR'] = df_aux['TIR']
    df['log(TIR)'] = np.log10(df['TIR'])
    df['Actual protein / predicted TIR'] = np.log10(df['Mean protein (fluo)']) / np.log10(df['TIR'])
    # del df_aux
    
    df = df[df['used_mRNA_sequence'].apply(lambda x: type(x) == str)]
    df = df[df['predicted_5pUTR_2.0'].apply(lambda x: type(x) == str)]

    # df['ARN count'] = df['used_mRNA_sequence'].apply(count_ARN_motifs)
    # df['AAN count'] = df['used_mRNA_sequence'].apply(count_AAN_motifs)
    df = df[~df['5pUTR'].isna()]

    def calc_ARNs(df, seq_key: str, name_bracket: str):
        df[f"ARN count ({name_bracket})"] = df[seq_key].apply(count_ARN_motifs)
        df[f"AAN count ({name_bracket})"] = df[seq_key].apply(count_AAN_motifs)
        df[f"ARNn count ({name_bracket})"] = df[seq_key].apply(count_ARNn)
        df[f"A-rich % ({name_bracket})"] = df[seq_key].apply(count_A_richness)
        df[f"(A)n count ({name_bracket})"] = df[seq_key].apply(count_An)
        df[f"(A)n count norm ({name_bracket})"] = df[seq_key].apply(count_An_norm)
        return df
    
    df = calc_ARNs(df, 'used_mRNA_sequence', 'mRNA')
    df = calc_ARNs(df, '5pUTR', "5' UTR")
    if 'RBS' in df: df = calc_ARNs(df, 'RBS', "RBS")
    df = calc_ARNs(df, 'SEQUENCE', "seq")

    df["log(yError)"] = np.log10(df["yError"])  # avoid log(0)

    print("\nShape of dataframe:", df.shape)
    
    return df


def main():
    test_count_ARNn()
    
    
if __name__ == "__main__":
    main()