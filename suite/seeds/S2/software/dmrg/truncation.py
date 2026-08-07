"""DMRG density-matrix truncation driver."""


def truncate(rho, cutoff):
    """Keep density-matrix eigenvalues above the cutoff."""
    return [w for w in rho if w > cutoff]
