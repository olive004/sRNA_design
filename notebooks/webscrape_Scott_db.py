

# %% [markdown]
# # Imports

# %%
import os
from Bio import SeqIO, Entrez
from urllib.error import HTTPError
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt


# %%
def load_seq_from_FASTA(filename, as_type="list"):
    fasta_records = SeqIO.parse(open(filename),'fasta')
    if as_type=="dict":
        sequences = {}
        for fasta_record in fasta_records:
            sequences[fasta_record.id] = str(fasta_record.seq)
        return sequences
    elif as_type=="list":
        sequences = []
        for fasta_record in fasta_records:
            sequences.append(str(fasta_record.seq))
        return sequences
    else:
        raise ValueError(f"Desired type {as_type} not supported.")


# %% [markdown]
# Download the RNA-RNA interactions file from http://www.rnainter.org/download/

# %%
fn_db = '../data/sRNA/TableS2_E_coli.xlsx'
data = pd.read_excel(fn_db, sheet_name='All_conditions')

# %%
features_rna = ["3'UTR", "5'UTR", 'intergenic_UTR', 'ncRNA', 'Novel_transcript', 'Novel_rRNA_or_tRNA_adjacent', 'non-coding RNA', 'pseudogene', 'putative_sRNA', 'RNase_P_RNA', 'rRNA', 'sRNA', 'SRP_RNA', 'tmRNA', 'transcript', 'tRNA']
data['attributes'] = data['attributes'].apply(lambda x: x.replace('Name', 'name').replace('ID=', 'name='))
data = data[data['feature'].isin(features_rna)]
data

# %%
data['attributes'] = data['attributes'].apply(lambda x: x.replace('Name', 'name'))
data['name'] = data['attributes'].apply(lambda x: x.split('name=')[1].split(';')[0])
data['strand num'] = data['strand'].apply(lambda x: 1 if x == '+' else 2)
# data['sRNA_type'] = data['attributes'].apply(lambda x: x.split('sRNA_type=')[1])
data['feature'].unique()

# %% [markdown]
# # Get sequences

# %%
from Bio import Entrez, SeqIO
import ssl

# Disable SSL verification temporarily
ssl._create_default_https_context = ssl._create_unverified_context


def get_dna_sequence(sequence_id, start, end, strand=1):
    """
    Retrieves the DNA sequence for the given sequence ID, start, and end positions.
    
    Parameters:
    sequence_id (str): The ID of the DNA sequence to retrieve.
    start (int): The starting position of the DNA sequence to retrieve.
    end (int): The ending position of the DNA sequence to retrieve.
    
    Returns:
    str: The DNA sequence for the given sequence ID, start, and end positions.
    """
    # Set your email address for Entrez access
    Entrez.email = "olivia.gallup@gmail.com"  # Add your email address
    Entrez.api_key = "8167226cf01abaa985a1c23d9b5283d22208"  # Add your NCBI API key
    
    handle = Entrez.efetch(
        db="nucleotide",
        id=sequence_id,
        rettype="fasta",
        retmode="text",
        strand=strand,
        seq_start=start,
        seq_stop=end,
    )
    record = SeqIO.read(handle, "fasta")
    
    return str(record.seq)


import logging


FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
FORMAT = "%(filename)s:%(funcName)s():%(lineno)i: %(message)s %(levelname)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


data['sequence'] = ''
batch_size = 100
for i0 in range(0, len(data), batch_size):
    i1 = min(i0 + batch_size, len(data))
    logging.error(f"Processing records {i0} to {i1}...")
    data.loc[i0:i1, 'sequence'] = data.loc[i0:i1].apply(lambda x: get_dna_sequence(x['seqID'], x['start'], x['end'], x['strand num']), axis=1)
    data.to_csv('../data/sRNA/TableS2_E_coli_with_seq.csv', index=False)
    

# data['sequence'] = data.apply(lambda x: get_dna_sequence(x['seqID'], x['start'], x['end'], x['strand num']), axis=1)

# %%
data.to_csv('../data/sRNA/TableS2_E_coli_with_seq.csv', index=False)
data

# %%



