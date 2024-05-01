"""multiple equilibruim solver script for cluster."""
from desc import set_device
set_device("gpu")
from desc.basis import (
    FourierZernike_to_FourierZernike_no_N_modes,
    FourierZernike_to_PoincareZernikePolynomial,
)
from desc.equilibrium import Equilibrium
from desc.examples import get
from desc.geometry import ZernikeRZToroidalSection
from desc.objectives import ForceBalance, ObjectiveFunction
from desc.objectives.getters import get_fixed_boundary_constraints
from desc.plotting import plot_comparison
import datetime
import matplotlib.pyplot as plt
def get_eq_poin(eq):
    """Takes LCFS equilibrium and returns POINCARE section input."""
    Rb_lmn, Rb_basis = FourierZernike_to_PoincareZernikePolynomial(eq.R_lmn, eq.R_basis)
    Zb_lmn, Zb_basis = FourierZernike_to_PoincareZernikePolynomial(eq.Z_lmn, eq.Z_basis)
    Lb_lmn, Lb_basis = FourierZernike_to_FourierZernike_no_N_modes(eq.L_lmn, eq.L_basis)
    surf = ZernikeRZToroidalSection(
        R_lmn=Rb_lmn,
        modes_R=Rb_basis.modes[:, :2].astype(int),
        Z_lmn=Zb_lmn,
        modes_Z=Zb_basis.modes[:, :2].astype(int),
        spectral_indexing=eq._spectral_indexing,
    )
    eq_poin = Equilibrium(
        surface=surf,
        pressure=eq.pressure,
        iota=eq.iota,
        Psi=eq.Psi,  # flux (in Webers) within the last closed flux surface
        NFP=eq.NFP,  # number of field periods
        L=eq.L,  # radial spectral resolution
        M=eq.M,  # poloidal spectral resolution
        N=eq.N,  # toroidal spectral resolution
        L_grid=eq.L_grid,  # real space radial resolution, slightly oversampled
        M_grid=eq.M_grid,  # real space poloidal resolution, slightly oversampled
        N_grid=eq.N_grid,  # real space toroidal resolution
        sym=True,  # explicitly enforce stellarator symmetry
        bdry_mode="poincare",
        spectral_indexing=eq._spectral_indexing,
    )
    eq_poin.L_lmn = (
        Lb_lmn  # initialize the poincare eq with the lambda of the original eq
    )
    eq_poin.axis = eq_poin.get_axis()
    return eq_poin

filename = "NCSX"

eq = get(filename)
loopN = range(1,eq.N)

for n in loopN:
    k = eq.N_grid
    eq_poin = get_eq_poin(eq)
    eq_poin.change_resolution(eq_poin.L, eq_poin.M, n)
    eq_poin.N_grid = k
    constraints = get_fixed_boundary_constraints(eq=eq_poin, poincare_lambda=True)
    objective = ObjectiveFunction(ForceBalance(eq_poin))
    eq_poin.solve(
	    verbose=3,
	    ftol=1e-15,
	    objective=objective,
	    constraints=constraints,
	    maxiter= 500,
	    xtol=1e-15,
	)
plot_comparison(
eqs=[eq, eq_poin], labels=["LCFS", f"poincare BC R* Z* N={n} N_grid={k}"]
)
date = datetime.date.today()
img_name = f"yge/figure/yge-N-{date}-{filename}.pdf"
out_name = f"yge/output/yge-N-{date}-{filename}.h5"

plt.savefig(img_name, format="pdf", dpi=1200)
eq_poin.save(out_name)
