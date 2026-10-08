"""Three operations on reviewed, single-output, reference-unit-normalized data.

This API computes a supplied model, not proof that the model is complete or valid
for the kettle. The project runner must check data provenance and scope first.
"""
import warnings
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import MatrixRankWarning, spsolve


def construct(processes, flow_keys, cf):
    """Build A/B/C. Inputs already use provider reference units per own output.

    Process: {id, inputs: {provider_id: amount}, elementary: {flow_key: amount}}.
    Flow keys must preserve UUID/version/unit/direction/compartment/location.
    Every flow requires a CF, including explicitly reviewed zeros. Normalization
    and provenance are adapter/review responsibilities, never inferred here.
    """
    ids = [p['id'] for p in processes]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('Processes must be nonempty and have unique IDs')
    if len(flow_keys) != len(set(flow_keys)):
        raise ValueError('Duplicate elementary flow keys')
    pi, fi = {k: i for i, k in enumerate(ids)}, {k: i for i, k in enumerate(flow_keys)}
    ar, ac, av = list(range(len(ids))), list(range(len(ids))), [1.] * len(ids)
    br, bc, bv = [], [], []
    for j, p in enumerate(processes):
        for provider, amount in p.get('inputs', {}).items():
            if provider not in pi:
                raise ValueError(f'Unresolved provider: {provider}')
            if not np.isfinite(amount) or amount < 0:
                raise ValueError('Invalid input quantity')
            ar.append(pi[provider]); ac.append(j); av.append(-amount)
        for flow, amount in p.get('elementary', {}).items():
            if flow not in fi:
                raise ValueError(f'Unknown elementary flow: {flow}')
            if not np.isfinite(amount) or amount < 0:
                raise ValueError('Signed credits require a reviewed model extension')
            br.append(fi[flow]); bc.append(j); bv.append(amount)
    missing = set(flow_keys) - set(cf)
    if missing:
        raise ValueError(f'Missing characterization decisions: {sorted(missing)}')
    c = np.array([[cf[k] for k in flow_keys]], dtype=float)
    if not np.isfinite(c).all():
        raise ValueError('Nonfinite characterization factor')
    a = coo_matrix((av, (ar, ac)), shape=(len(ids), len(ids))).tocsc()
    b = coo_matrix((bv, (br, bc)), shape=(len(flow_keys), len(ids))).tocsc()
    return a, b, c


def calculate(a, b, c, demand):
    f = np.asarray(demand, dtype=float)
    if a.shape[0] != a.shape[1] or f.shape != (a.shape[0],):
        raise ValueError('A must be square and f must match its product rows')
    if b.shape[1] != a.shape[1] or c.ndim != 2 or c.shape[1] != b.shape[0]:
        raise ValueError('Incompatible B/C dimensions')
    if not np.isfinite(f).all() or (f < 0).any():
        raise ValueError('Demand must be finite and nonnegative')
    if any(not np.isfinite(x.data).all() for x in [a, b]) or not np.isfinite(c).all():
        raise ValueError('Nonfinite matrix values')
    with warnings.catch_warnings():
        warnings.simplefilter('error', MatrixRankWarning)
        try:
            s = spsolve(a, f)
        except MatrixRankWarning as exc:
            raise ValueError('Singular technosphere') from exc
    if not np.isfinite(s).all() or (s < -1e-10).any():
        raise ValueError('Invalid activity solution')
    if not np.allclose(a @ s, f, rtol=1e-9, atol=1e-10):
        raise ValueError('Technosphere residual failure')
    g = np.asarray(b @ s)
    h = c @ g
    if not np.isfinite(g).all() or not np.isfinite(h).all():
        raise ValueError('Nonfinite inventory or impact')
    return {'s': s, 'g': g, 'h': h}


def contributions(a, b, c, groups, total_demand):
    demands = [np.asarray(d, dtype=float) for d in groups.values()]
    if not demands or not np.allclose(np.sum(demands, axis=0), total_demand, rtol=1e-9, atol=1e-10):
        raise ValueError('Contribution demands do not reconcile with total demand')
    parts = {k: calculate(a, b, c, d)['h'] for k, d in groups.items()}
    if not np.allclose(sum(parts.values()), calculate(a, b, c, total_demand)['h']):
        raise ValueError('Contribution impacts do not reconcile')
    return parts
