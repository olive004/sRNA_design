from varnaapi import Structure


def show_rna_structure(rna_structure, seq, resolution=3, algorithm='radiate', annotate: bool = False, highlight_kwrgs: dict = None):
    try:
        v = Structure(structure=rna_structure, sequence=seq)
        v._params['resolution'] = resolution
        v._params['algorithm'] = algorithm
        if annotate:
            v._params['autoHelices'] = True
            v._params['autoInteriorLoops'] = True
            v._params['autoTerminalLoops'] = True
        if highlight_kwrgs:
            v.add_highlight_region(**highlight_kwrgs)
        v.show()
        # v.savefig("example.png", show=True)
    except FileNotFoundError:
        print('No Java found, could not visualise')
        pass
