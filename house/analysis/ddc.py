import numpy as np
import pandas as pd


def _numeric_series(df, obj, name):
    values = obj(df) if callable(obj) else df[obj]
    return pd.to_numeric(values, errors="coerce").rename(name)


def _as_mask(df, rule):
    values = rule(df) if callable(rule) else rule

    if isinstance(values, pd.Series):
        mask = values.reindex(df.index)
    else:
        mask = pd.Series(values, index=df.index)

    return mask.fillna(False).astype(bool)


def _prepare_frame(df, x, y, base_mask=None, dropna=True):
    work = pd.DataFrame({
        "X": _numeric_series(df, x, "X"),
        "Y": _numeric_series(df, y, "Y"),
    }, index=df.index)

    if base_mask is None:
        keep = pd.Series(True, index=df.index)
    else:
        keep = _as_mask(df, base_mask)

    if dropna:
        keep = keep & work[["X", "Y"]].notna().all(axis=1)

    return df.loc[keep], work.loc[keep]


def _ols_from_xy(x, y):
    mu_x = x.mean()
    mu_y = y.mean()
    mu_x2 = (x ** 2).mean()
    mu_xy = (x * y).mean()

    var_x = mu_x2 - mu_x ** 2

    if np.isclose(var_x, 0):
        raise ValueError("Uh-oh, the finite-population variance of X is zero. Do something else.")

    beta = (mu_xy - mu_x * mu_y) / var_x
    alpha = mu_y - beta * mu_x

    return {
        "mu_x": mu_x,
        "mu_y": mu_y,
        "mu_x2": mu_x2,
        "mu_xy": mu_xy,
        "var_x": var_x,
        "alpha": alpha,
        "beta": beta,
    }


def _moment_row(g, mask, regime, moment):
    g = np.asarray(g, dtype=float)
    r = np.asarray(mask, dtype=bool)
    R = r.astype(float)

    N = len(g)
    n = int(r.sum())

    if n == 0:
        raise ValueError(f"WRONG. Regime '{regime}' contains no observations.")

    f = n / N
    mu_P = g.mean()
    mu_A = g[r].mean()
    delta = mu_A - mu_P
    sigma = g.std(ddof=0)

    rho = np.nan
    meng_delta = np.nan
    identity_error = np.nan
    z_srs = np.nan
    ddi = np.nan
    realized_deff = np.nan

    if 0 < f < 1 and sigma > 0:
        cov_rg = ((R - f) * (g - mu_P)).mean()
        rho = cov_rg / (np.sqrt(f * (1 - f)) * sigma)
        meng_delta = rho * np.sqrt((1 - f) / f) * sigma
        identity_error = delta - meng_delta
        z_srs = rho * np.sqrt(N - 1)
        ddi = rho ** 2
        realized_deff = (N - 1) * rho ** 2

    return {
        "regime": regime,
        "moment": moment,
        "N": N,
        "n": n,
        "f": f,
        "mu_P": mu_P,
        "mu_A": mu_A,
        "delta": delta,
        "sigma_P": sigma,
        "rho": rho,
        "meng_delta": meng_delta,
        "identity_error": identity_error,
        "z_srs": z_srs,
        "ddi": ddi,
        "realized_deff": realized_deff,
    }


def _beta_diagnostic_row(x, y, mask, regime, pop, samp, approx_gap):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    r = np.asarray(mask, dtype=bool)
    R = r.astype(float)

    N = len(x)
    n = int(r.sum())
    f = n / N

    mu_x = pop["mu_x"]
    mu_y = pop["mu_y"]
    beta_P = pop["beta"]
    var_x = pop["var_x"]

    psi = ((x - mu_x) * (y - mu_y) - beta_P * (x - mu_x) ** 2) / var_x

    psi_P = psi.mean()
    psi_A = psi[r].mean()
    delta_psi = psi_A - psi_P
    sigma_psi = psi.std(ddof=0)
    actual_gap = samp["beta"] - pop["beta"]

    rho_psi = np.nan
    meng_delta_psi = np.nan
    identity_error_psi = np.nan
    se_srs_psi = np.nan
    z_beta_lin = np.nan
    z_beta_actual = np.nan
    z_beta_remainder = np.nan
    beta_remainder = actual_gap - delta_psi
    actual_by_linear = np.nan
    linear_to_actual = np.nan

    if 0 < f < 1 and sigma_psi > 0:
        cov_rpsi = ((R - f) * (psi - psi_P)).mean()
        rho_psi = cov_rpsi / (np.sqrt(f * (1 - f)) * sigma_psi)
        meng_delta_psi = rho_psi * np.sqrt((1 - f) / f) * sigma_psi
        identity_error_psi = delta_psi - meng_delta_psi
        se_srs_psi = np.sqrt((1 - f) / (f * (N - 1))) * sigma_psi
        z_beta_lin = delta_psi / se_srs_psi
        z_beta_actual = actual_gap / se_srs_psi
        z_beta_remainder = beta_remainder / se_srs_psi

    if not np.isclose(delta_psi, 0):
        actual_by_linear = actual_gap / delta_psi

    if not np.isclose(actual_gap, 0):
        linear_to_actual = delta_psi / actual_gap

    return {
        "regime": regime,
        "N": N,
        "n": n,
        "f": f,
        "beta_P": pop["beta"],
        "beta_A": samp["beta"],
        "actual_gap": actual_gap,
        "linearized_gap": delta_psi,
        "approx_gap": approx_gap,
        "beta_remainder": beta_remainder,
        "psi_P": psi_P,
        "psi_A": psi_A,
        "delta_psi": delta_psi,
        "sigma_psi": sigma_psi,
        "rho_psi": rho_psi,
        "meng_delta_psi": meng_delta_psi,
        "identity_error_psi": identity_error_psi,
        "se_srs_psi": se_srs_psi,
        "z_beta_lin": z_beta_lin,
        "z_beta_actual": z_beta_actual,
        "z_beta_remainder": z_beta_remainder,
        "actual_by_linear": actual_by_linear,
        "linear_to_actual": linear_to_actual,
    }


def _simple_audit_arrays(x, y, mask, regime):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.asarray(mask, dtype=bool)

    N = len(x)
    n = int(mask.sum())
    f = n / N

    if n == 0:
        raise ValueError(f"WRONG. Regime '{regime}' contains no observations.")

    pop = _ols_from_xy(x, y)
    samp = _ols_from_xy(x[mask], y[mask])

    moment_values = {
        "X": x,
        "Y": y,
        "X^2": x ** 2,
        "XY": x * y,
    }

    moment_table = pd.DataFrame([
        _moment_row(values, mask, regime, moment)
        for moment, values in moment_values.items()
    ])

    deltas = moment_table.set_index("moment")["delta"]

    delta_x = deltas["X"]
    delta_y = deltas["Y"]
    delta_x2 = deltas["X^2"]
    delta_xy = deltas["XY"]

    mu_x = pop["mu_x"]
    mu_y = pop["mu_y"]
    beta_P = pop["beta"]
    var_x = pop["var_x"]

    contributions = {
        "XY": delta_xy / var_x,
        "X": ((2 * beta_P * mu_x - mu_y) * delta_x) / var_x,
        "Y": (-mu_x * delta_y) / var_x,
        "X^2": (-beta_P * delta_x2) / var_x,
    }

    approx_gap = sum(contributions.values())
    actual_gap = samp["beta"] - pop["beta"]
    approx_error = actual_gap - approx_gap

    contribution_table = pd.DataFrame([
        {
            "regime": regime,
            "component": component,
            "delta": {
                "X": delta_x,
                "Y": delta_y,
                "X^2": delta_x2,
                "XY": delta_xy,
            }[component],
            "contribution": value,
            "share_of_approx": value / approx_gap if not np.isclose(approx_gap, 0) else np.nan,
        }
        for component, value in contributions.items()
    ])

    coef_row = {
        "regime": regime,
        "N": N,
        "n": n,
        "f": f,
        "alpha_P": pop["alpha"],
        "beta_P": pop["beta"],
        "alpha_A": samp["alpha"],
        "beta_A": samp["beta"],
        "actual_gap": actual_gap,
        "approx_gap": approx_gap,
        "approx_error": approx_error,
        "abs_approx_error": abs(approx_error),
        "rel_approx_error": approx_error / actual_gap if not np.isclose(actual_gap, 0) else np.nan,
        "var_x_P": pop["var_x"],
        "max_abs_rho": moment_table["rho"].abs().max(),
        "max_abs_z_srs": moment_table["z_srs"].abs().max(),
        "max_realized_deff": moment_table["realized_deff"].max(),
    }

    # z_beta_lin  = Meng standardized first-order coefficient defect
    # z_beta_actual = Meng standardized actual coefficient gap
    # z_beta_remainder = standardized nonlinear/local approximation failure

    beta_diag_row = _beta_diagnostic_row(
        x=x,
        y=y,
        mask=mask,
        regime=regime,
        pop=pop,
        samp=samp,
        approx_gap=approx_gap,
    )

    return coef_row, moment_table, contribution_table, beta_diag_row


def audit_regimes(df, x, y, regimes, base_mask=None, dropna=True):
    source, work = _prepare_frame(df, x=x, y=y, base_mask=base_mask, dropna=dropna)

    x_values = work["X"].to_numpy()
    y_values = work["Y"].to_numpy()

    coef_rows = []
    beta_diag_rows = []
    moment_tables = []
    contribution_tables = []

    for regime, rule in regimes.items():
        mask = _as_mask(source, rule).to_numpy()

        coef_row, moment_table, contribution_table, beta_diag_row = _simple_audit_arrays(
            x_values,
            y_values,
            mask,
            regime,
        )

        coef_rows.append(coef_row)
        beta_diag_rows.append(beta_diag_row)
        moment_tables.append(moment_table)
        contribution_tables.append(contribution_table)

    coef_table = pd.DataFrame(coef_rows)
    moment_table = pd.concat(moment_tables, ignore_index=True)
    contribution_table = pd.concat(contribution_tables, ignore_index=True)
    beta_diag_table = pd.DataFrame(beta_diag_rows)

    return coef_table, moment_table, contribution_table, beta_diag_table


def wide_moment_table(moment_table, value="rho"):
    out = moment_table.pivot(index="regime", columns="moment", values=value).reset_index()
    out.columns.name = value
    return out


def wide_contribution_table(contribution_table):
    return contribution_table.pivot(index="regime", columns="component", values="contribution").reset_index() 

def rounded(df, digits=4):
    out = df.copy()

    for col in out.select_dtypes(include="number").columns:
        out[col] = out[col].round(digits)

    return out


def _calibration_features(source, x_values, y_values, terms):
    terms = list(terms)

    if not terms:
        return np.empty((len(x_values), 0))

    feature_map = {
        "X": x_values,
        "Y": y_values,
        "X^2": x_values ** 2,
        "X2": x_values ** 2,
        "XY": x_values * y_values,
    }

    cols = []

    for term in terms:
        if term in feature_map:
            values = feature_map[term]
        elif term in source.columns:
            values = pd.to_numeric(source[term], errors="coerce").to_numpy()
        else:
            raise ValueError(f"Uhh, unknown calibration term '{term}'. Use X, Y, X^2, XY, or a numeric column in df please.")

        cols.append(np.asarray(values, dtype=float))

    H = np.column_stack(cols)

    if np.isnan(H).any():
        raise ValueError("Calibration features contain NaNs! Drop or impute these before calibration.")

    return H


def _weighted_simple_ols(x, y, w):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    w = np.asarray(w, dtype=float)
    w = w / w.sum()

    mu_x = np.sum(w * x)
    mu_y = np.sum(w * y)
    mu_x2 = np.sum(w * x ** 2)
    mu_xy = np.sum(w * x * y)

    var_x = mu_x2 - mu_x ** 2

    if np.isclose(var_x, 0):
        return np.nan, np.nan

    beta = (mu_xy - mu_x * mu_y) / var_x
    alpha = mu_y - beta * mu_x

    return alpha, beta



def _safe_scale(values, floor=1e-12):
    values = np.asarray(values, dtype=float)
    scale = values.std(axis=0, ddof=0)
    return np.where(scale > floor, scale, 1.0)


def _support_diagnostics(H, target, scale=None, tol=1e-10):
    H = np.asarray(H, dtype=float)
    target = np.asarray(target, dtype=float)

    if H.shape[1] == 0:
        return {
            "support_violation_count": 0,
            "max_support_violation": 0.0,
            "max_std_support_violation": 0.0,
            "min_support_margin": np.nan,
        }

    lo = H.min(axis=0)
    hi = H.max(axis=0)
    below = np.maximum(lo - target, 0.0)
    above = np.maximum(target - hi, 0.0)
    violation = np.maximum(below, above)

    if scale is None:
        scale = _safe_scale(H)
    else:
        scale = np.asarray(scale, dtype=float)
        scale = np.where(np.abs(scale) > 1e-12, np.abs(scale), 1.0)

    ranges = np.where((hi - lo) > 1e-12, hi - lo, np.nan)
    margins = np.minimum(target - lo, hi - target) / ranges

    return {
        "support_violation_count": int(np.sum(violation > tol)),
        "max_support_violation": float(np.max(violation)) if violation.size else 0.0,
        "max_std_support_violation": float(np.max(violation / scale)) if violation.size else 0.0,
        "min_support_margin": float(np.nanmin(margins)) if np.isfinite(margins).any() else np.nan,
    }


def _balance_diagnostics(w, H, target, scale=None):
    w = np.asarray(w, dtype=float)
    w = w / w.sum()
    H = np.asarray(H, dtype=float)
    target = np.asarray(target, dtype=float)

    if H.shape[1] == 0:
        return {
            "max_abs_balance_error": 0.0,
            "rms_balance_error": 0.0,
            "max_abs_std_balance_error": 0.0,
            "rms_std_balance_error": 0.0,
        }

    balance = w @ H - target

    if scale is None:
        scale = _safe_scale(H)
    else:
        scale = np.asarray(scale, dtype=float)
        scale = np.where(np.abs(scale) > 1e-12, np.abs(scale), 1.0)

    std_balance = balance / scale

    return {
        "max_abs_balance_error": float(np.max(np.abs(balance))),
        "rms_balance_error": float(np.sqrt(np.mean(balance ** 2))),
        "max_abs_std_balance_error": float(np.max(np.abs(std_balance))),
        "rms_std_balance_error": float(np.sqrt(np.mean(std_balance ** 2))),
    }


def _weight_diagnostics(w, H, target, scale=None, balance_tol=1e-6, std_balance_tol=1e-8):
    w = np.asarray(w, dtype=float)
    w = w / w.sum()

    n = len(w)
    min_w = float(np.min(w))
    max_w = float(np.max(w))
    ess = float(1 / np.sum(w ** 2))
    rel_w = w * n

    balance = _balance_diagnostics(w, H, target, scale=scale)
    support = _support_diagnostics(H, target, scale=scale)

    top_1 = max(1, int(np.ceil(0.01 * n)))
    top_5 = max(1, int(np.ceil(0.05 * n)))
    sorted_w = np.sort(w)[::-1]

    return {
        "balanced": bool(
            balance["max_abs_balance_error"] < balance_tol
            or balance["max_abs_std_balance_error"] < std_balance_tol
        ),
        "min_w": min_w,
        "max_w": max_w,
        "weight_ratio": max_w / min_w if min_w > 0 else np.inf,
        "ess": ess,
        "ess_ratio": ess / n,
        "weight_deff": n / ess,
        "weight_cv": float(np.std(rel_w, ddof=0)),
        "max_relative_weight": float(np.max(rel_w)),
        "top_1pct_weight_share": float(sorted_w[:top_1].sum()),
        "top_5pct_weight_share": float(sorted_w[:top_5].sum()),
        **balance,
        **support,
    }


def entropy_calibration_weights(H, target, tol=1e-9, balance_tol=1e-6, std_balance_tol=1e-8, maxiter=1000):
    from scipy.optimize import minimize, least_squares
    from scipy.special import logsumexp

    H = np.asarray(H, dtype=float)
    target = np.asarray(target, dtype=float)

    n, p = H.shape

    if p == 0:
        return np.ones(n) / n, {
            "method": "entropy",
            "converged": True,
            "optimizer_success": True,
            "balanced": True,
            "solver": "none",
            "message": "No calibration constraints supplied.",
            "iterations": np.nan,
            "dual_objective": np.nan,
        }

    center = H.mean(axis=0)
    scale = H.std(axis=0, ddof=0)
    active = scale > 1e-12

    if np.any(~active):
        inactive_error = np.max(np.abs(target[~active] - center[~active]))

        if inactive_error > balance_tol:
            return np.ones(n) / n, {"method": "entropy", "converged": False, "optimizer_success": False, "balanced": False, "solver": "none", 
                                    "message": "A constant calibration feature has a target different from its sample value.", 
                                    "iterations": np.nan, "dual_objective": np.nan}

    Z = (H[:, active] - center[active]) / scale[active]
    target_z = (target[active] - center[active]) / scale[active]

    if Z.shape[1] == 0:
        return np.ones(n) / n, {"method": "entropy", "converged": True, "optimizer_success": True, "balanced": True, "solver": "none", 
                                "message": "All calibration features constant and already balanced.", "iterations": np.nan, "dual_objective": np.nan}

    log_q = np.full(n, -np.log(n))

    def weights_from_lambda(lam):
        a = log_q + Z @ lam
        return np.exp(a - logsumexp(a))

    def objective(lam):
        a = log_q + Z @ lam
        log_norm = logsumexp(a)
        w = np.exp(a - log_norm)
        value = log_norm - lam @ target_z
        grad = Z.T @ w - target_z
        return value, grad

    def grad_only(lam):
        return objective(lam)[1]

    candidates = []

    for method in ("BFGS", "L-BFGS-B"):
        res = minimize(
            fun=lambda lam: objective(lam)[0],
            x0=np.zeros(Z.shape[1]),
            jac=lambda lam: objective(lam)[1],
            method=method,
            options={"gtol": tol, "maxiter": maxiter},
            )
        w = weights_from_lambda(res.x)
        bal = _balance_diagnostics(w, H, target, scale=scale)
        candidates.append({
            "solver": method,
            "x": res.x,
            "w": w,
            "optimizer_success": bool(res.success),
            "message": str(res.message),
            "iterations": getattr(res, "nit", np.nan),
            "dual_objective": float(objective(res.x)[0]),
            "max_abs_balance_error": bal["max_abs_balance_error"],
            "max_abs_std_balance_error": bal["max_abs_std_balance_error"],
            })

    best_x = min(candidates, key=lambda c: (c["max_abs_std_balance_error"], c["max_abs_balance_error"]))["x"]

    ls = least_squares(fun=grad_only, x0=best_x, xtol=tol, ftol=tol, gtol=tol, max_nfev=maxiter)
    w = weights_from_lambda(ls.x)
    bal = _balance_diagnostics(w, H, target, scale=scale)
    candidates.append({
        "solver": "least_squares_balance",
        "x": ls.x,
        "w": w,
        "optimizer_success": bool(ls.success),
        "message": str(ls.message),
        "iterations": getattr(ls, "nfev", np.nan),
        "dual_objective": float(objective(ls.x)[0]),
        "max_abs_balance_error": bal["max_abs_balance_error"],
        "max_abs_std_balance_error": bal["max_abs_std_balance_error"],
        })

    best = min(candidates, key=lambda c: (c["max_abs_std_balance_error"], c["max_abs_balance_error"]))
    w = best["w"]
    bal = _balance_diagnostics(w, H, target, scale=scale)
    balanced = bool(
        bal["max_abs_balance_error"] < balance_tol
        or bal["max_abs_std_balance_error"] < std_balance_tol
    )

    return w, {"method": "entropy", "converged": balanced, "optimizer_success": bool(best["optimizer_success"]), "balanced": balanced, "solver": best["solver"], 
               "message": best["message"], "iterations": best["iterations"], "dual_objective": best["dual_objective"]}

def calibration_ladder(df, x, y, regimes, base_mask=None, dropna=True, ladders=None, tol=1e-9, balance_tol=1e-6, std_balance_tol=1e-8, maxiter=1000):
    source, work = _prepare_frame(df, x=x, y=y, base_mask=base_mask, dropna=dropna)

    x_values = work["X"].to_numpy()
    y_values = work["Y"].to_numpy()

    pop = _ols_from_xy(x_values, y_values)
    beta_P = pop["beta"]

    if ladders is None:
        ladders = {"Unweighted": [], "Calibrate X": ["X"], "Calibrate X, X^2": ["X", "X^2"], "Calibrate X, Y": ["X", "Y"], 
                   "Calibrate X, Y, X^2, XY": ["X", "Y", "X^2", "XY"]}

    rows = []

    for regime, rule in regimes.items():
        mask = _as_mask(source, rule).to_numpy()

        if int(mask.sum()) == 0:
            raise ValueError(f"WRONG. Regime '{regime}' contains no observations.")

        x_A = x_values[mask]
        y_A = y_values[mask]
        source_A = source.loc[mask]

        _, beta_A = _weighted_simple_ols(x_A, y_A, np.ones(len(x_A)) / len(x_A))

        for step, terms in ladders.items():
            H_P = _calibration_features(source, x_values, y_values, terms)
            H_A = _calibration_features(source_A, x_A, y_A, terms)
            target = H_P.mean(axis=0) if terms else np.array([])
            scale = _safe_scale(H_P) if terms else np.array([])

            if step == "Unweighted" or len(terms) == 0:
                w = np.ones(len(x_A)) / len(x_A)
                info = {"method": "none", "converged": True, "optimizer_success": True, "balanced": True, "solver": "none", "message": "Uniform analytic-sample weights.",
                         "iterations": np.nan, "dual_objective": np.nan}
            else:
                w, info = entropy_calibration_weights(H_A, target, tol=tol, balance_tol=balance_tol, std_balance_tol=std_balance_tol, maxiter=maxiter)
            alpha_w, beta_w = _weighted_simple_ols(x_A, y_A, w)
            diag = _weight_diagnostics(w, H_A, target, scale=scale, balance_tol=balance_tol, std_balance_tol=std_balance_tol)

            rows.append({
                "regime": regime,
                "calibration_step": step,
                "method": info.get("method"),
                "converged": info.get("converged"),
                "balanced": diag.get("balanced"),
                "optimizer_success": info.get("optimizer_success"),
                "solver": info.get("solver"),
                "message": info.get("message"),
                "iterations": info.get("iterations", np.nan),
                "dual_objective": info.get("dual_objective", np.nan),
                "N": len(x_values),
                "n": len(x_A),
                "f": len(x_A) / len(x_values),
                "beta_P": beta_P,
                "beta_A": beta_A,
                "beta_w": beta_w,
                "gap_unweighted": beta_A - beta_P,
                "gap_weighted": beta_w - beta_P,
                "repair": (beta_A - beta_P) - (beta_w - beta_P),
                "abs_gap_reduction": abs(beta_A - beta_P) - abs(beta_w - beta_P),
                "alpha_w": alpha_w,
                "terms": ", ".join(terms),
                **diag,
            })

    return pd.DataFrame(rows)


def calibration_summary_table(calib_table):
    preferred = [
        "regime",
        "calibration_step",
        "converged",
        "balanced",
        "optimizer_success",
        "solver",
        "beta_P",
        "beta_A",
        "beta_w",
        "gap_unweighted",
        "gap_weighted",
        "abs_gap_reduction",
        "ess",
        "ess_ratio",
        "weight_deff",
        "weight_cv",
        "max_relative_weight",
        "weight_ratio",
        "top_1pct_weight_share",
        "max_abs_balance_error",
        "max_abs_std_balance_error",
        "support_violation_count",
        "max_std_support_violation",
        "min_support_margin",
    ]

    cols = [col for col in preferred if col in calib_table.columns]
    return calib_table.loc[:, cols].copy()


# prospective calibration/repair


# helpers

def _ordered_unique(values):
    return sorted(pd.Series(values).dropna().unique())


def _x_score(x, transform="log1p"):
    x = np.asarray(x, dtype=float)

    if transform is None or transform == "identity":
        return x

    if transform == "log1p":
        if np.nanmin(x) <= -1:
            raise ValueError("log1p transform requires X > -1.")
        return np.log1p(x)

    raise ValueError("Unknown transform. Use 'log1p', 'identity', or None.")


def _quantile_edges(values, n_bins=10):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if len(values) == 0:
        raise ValueError("No finite values supplied for bin construction.")

    edges = np.unique(np.quantile(values, np.linspace(0, 1, n_bins + 1)))

    if len(edges) < 2:
        raise ValueError("Unable to construct bins because the binning variable is constant.")

    edges[0] = -np.inf
    edges[-1] = np.inf

    return edges


def _bin_codes(values, edges):
    codes = pd.cut(values, bins=edges, labels=False, include_lowest=True)
    return pd.Series(codes).astype("Int64").to_numpy()


def _cycle_masks(source, cycle_col, cycle, regime_rule):
    cycle_mask = source[cycle_col].eq(cycle).to_numpy()
    regime_mask = _as_mask(source, regime_rule).to_numpy()
    return cycle_mask, cycle_mask & regime_mask


def _default_train_cycles(source, cycle_col, holdout_cycle, train_cycles):
    cycles = _ordered_unique(source[cycle_col])

    if holdout_cycle not in cycles:
        raise ValueError(f"Holdout cycle '{holdout_cycle}' not found.")

    if train_cycles is None:
        train_cycles = [cycle for cycle in cycles if cycle != holdout_cycle]
    else:
        train_cycles = list(train_cycles)

    if len(train_cycles) == 0:
        raise ValueError("At least one training cycle is required.")

    return train_cycles


def _repair_eval_row(method, holdout_cycle, train_cycles, x_P, y_P, x_A, y_A, w, H_P, H_A, terms):
    w = np.asarray(w, dtype=float)
    w = w / w.sum()

    _, beta_P = _weighted_simple_ols(x_P, y_P, np.ones(len(x_P)) / len(x_P))
    _, beta_A = _weighted_simple_ols(x_A, y_A, np.ones(len(x_A)) / len(x_A))
    alpha_w, beta_w = _weighted_simple_ols(x_A, y_A, w)

    target = H_P.mean(axis=0) if H_P.shape[1] else np.array([])
    scale = _safe_scale(H_P) if H_P.shape[1] else np.array([])
    diag = _weight_diagnostics(w, H_A, target, scale=scale)

    return {
        "method": method,
        "holdout_cycle": holdout_cycle,
        "train_cycles": ", ".join(map(str, train_cycles)),
        "n_train_cycles": len(train_cycles),
        "terms": ", ".join(terms),
        "N_holdout": len(x_P),
        "n_holdout": len(x_A),
        "f_holdout": len(x_A) / len(x_P),
        "alpha_w": alpha_w,
        "beta_P": beta_P,
        "beta_A": beta_A,
        "beta_w": beta_w,
        "gap_unweighted": beta_A - beta_P,
        "gap_weighted": beta_w - beta_P,
        "repair": (beta_A - beta_P) - (beta_w - beta_P),
        "abs_gap_reduction": abs(beta_A - beta_P) - abs(beta_w - beta_P),
        **diag,
    }


def _fit_log_multiplier_rule(H, multiplier, ridge=1e-6):
    H = np.asarray(H, dtype=float)
    multiplier = np.asarray(multiplier, dtype=float)

    keep = np.isfinite(multiplier) & (multiplier > 0)

    if H.shape[1]:
        keep = keep & np.isfinite(H).all(axis=1)

    H = H[keep]
    multiplier = multiplier[keep]

    if len(multiplier) == 0:
        raise ValueError("No valid positive multipliers available for fitting.")

    if H.shape[1] == 0:
        return {
            "intercept": float(np.mean(np.log(multiplier))),
            "coef": np.array([]),
            "center": np.array([]),
            "scale": np.array([]),
            "ridge": ridge,
        }

    center = H.mean(axis=0)
    scale = _safe_scale(H)
    Z = (H - center) / scale

    design = np.column_stack([np.ones(len(Z)), Z])
    y_log = np.log(multiplier)

    penalty = np.eye(design.shape[1]) * ridge
    penalty[0, 0] = 0.0

    lhs = design.T @ design + penalty
    rhs = design.T @ y_log

    try:
        coef_full = np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError:
        coef_full = np.linalg.lstsq(lhs, rhs, rcond=None)[0]

    fitted = design @ coef_full
    resid = y_log - fitted

    return {
        "intercept": float(coef_full[0]),
        "coef": coef_full[1:],
        "center": center,
        "scale": scale,
        "ridge": ridge,
        "rmse_log_multiplier": float(np.sqrt(np.mean(resid ** 2))),
        "mae_log_multiplier": float(np.mean(np.abs(resid))),
    }


def _predict_multiplier_weights(H, model, clip_log_multiplier=None):
    H = np.asarray(H, dtype=float)

    if H.shape[1] == 0:
        log_multiplier = np.repeat(model["intercept"], len(H))
    else:
        center = np.asarray(model["center"], dtype=float)
        scale = np.asarray(model["scale"], dtype=float)
        coef = np.asarray(model["coef"], dtype=float)

        Z = (H - center) / scale
        log_multiplier = model["intercept"] + Z @ coef

    if clip_log_multiplier is not None:
        c = abs(clip_log_multiplier)
        log_multiplier = np.clip(log_multiplier, -c, c)

    raw = np.exp(log_multiplier)

    if np.any(~np.isfinite(raw)) or np.any(raw < 0):
        raise ValueError("Predicted multipliers must be finite and nonnegative.")

    if np.isclose(raw.sum(), 0):
        raw = np.ones_like(raw)

    return raw / raw.sum()


def _training_exact_entropy_weights(
    source,
    x_values,
    y_values,
    cycle_col,
    train_cycles,
    regime,
    terms,
    tol=1e-9,
    balance_tol=1e-6,
    std_balance_tol=1e-8,
    maxiter=1000,
):
    rows = []
    fit_rows = []

    for cycle in train_cycles:
        P_mask, A_mask = _cycle_masks(source, cycle_col, cycle, regime)

        if int(P_mask.sum()) == 0:
            raise ValueError(f"Training cycle '{cycle}' has no benchmark rows.")

        if int(A_mask.sum()) == 0:
            raise ValueError(f"Training cycle '{cycle}' has no restricted rows.")

        H_P = _calibration_features(source.loc[P_mask], x_values[P_mask], y_values[P_mask], terms)
        H_A = _calibration_features(source.loc[A_mask], x_values[A_mask], y_values[A_mask], terms)
        target = H_P.mean(axis=0) if len(terms) else np.array([])

        w_exact, info = entropy_calibration_weights(
            H_A,
            target,
            tol=tol,
            balance_tol=balance_tol,
            std_balance_tol=std_balance_tol,
            maxiter=maxiter,
        )

        multiplier = w_exact * len(w_exact)

        rows.append(pd.DataFrame({
            **{term: H_A[:, j] for j, term in enumerate(terms)},
            "cycle": cycle,
            "x": x_values[A_mask],
            "y": y_values[A_mask],
            "multiplier": multiplier,
        }))

        diag = _weight_diagnostics(w_exact, H_A, target, scale=_safe_scale(H_P))

        fit_rows.append({
            "cycle": cycle,
            "N": int(P_mask.sum()),
            "n": int(A_mask.sum()),
            "f": int(A_mask.sum()) / int(P_mask.sum()),
            "converged": info.get("converged"),
            "optimizer_success": info.get("optimizer_success"),
            "solver": info.get("solver"),
            "message": info.get("message"),
            **diag,
        })

    return pd.concat(rows, ignore_index=True), pd.DataFrame(fit_rows)


# routines

def bin_mult_calibrator(
    df,
    x,
    y,
    cycle_col,
    holdout_cycle,
    regime,
    base_mask=None,
    dropna=True,
    terms=("X", "Y", "X^2", "XY"),
    train_cycles=None,
    n_bins=10,
    bin_transform="log1p",
    bin_stat="mean",
    tol=1e-9,
    balance_tol=1e-6,
    std_balance_tol=1e-8,
    maxiter=1000,
):
    source, work = _prepare_frame(df, x=x, y=y, base_mask=base_mask, dropna=dropna)

    if cycle_col not in source.columns:
        raise ValueError(f"Column '{cycle_col}' not found.")

    x_values = work["X"].to_numpy()
    y_values = work["Y"].to_numpy()
    train_cycles = _default_train_cycles(source, cycle_col, holdout_cycle, train_cycles)

    exact_table, fit_table = _training_exact_entropy_weights(
        source=source,
        x_values=x_values,
        y_values=y_values,
        cycle_col=cycle_col,
        train_cycles=train_cycles,
        regime=regime,
        terms=terms,
        tol=tol,
        balance_tol=balance_tol,
        std_balance_tol=std_balance_tol,
        maxiter=maxiter,
    )

    exact_table["z"] = _x_score(exact_table["x"].to_numpy(), transform=bin_transform)

    edges = _quantile_edges(exact_table["z"].to_numpy(), n_bins=n_bins)
    exact_table["bin"] = _bin_codes(exact_table["z"].to_numpy(), edges)

    if bin_stat == "mean":
        learned_bins = exact_table.groupby("bin", dropna=False)["multiplier"].mean()
    elif bin_stat == "median":
        learned_bins = exact_table.groupby("bin", dropna=False)["multiplier"].median()
    else:
        raise ValueError("bin_stat must be 'mean' or 'median'.")

    n_actual_bins = len(edges) - 1
    global_multiplier = float(exact_table["multiplier"].mean())
    multipliers = np.full(n_actual_bins, global_multiplier)

    for idx, value in learned_bins.items():
        if pd.notna(idx):
            multipliers[int(idx)] = float(value)

    P_holdout, A_holdout = _cycle_masks(source, cycle_col, holdout_cycle, regime)

    if int(P_holdout.sum()) == 0:
        raise ValueError(f"Holdout cycle '{holdout_cycle}' has no benchmark rows.")

    if int(A_holdout.sum()) == 0:
        raise ValueError(f"Holdout cycle '{holdout_cycle}' has no restricted rows.")

    z_holdout = _x_score(x_values[A_holdout], transform=bin_transform)
    holdout_bins = _bin_codes(z_holdout, edges)

    raw = np.array([
        multipliers[int(code)] if pd.notna(code) else global_multiplier
        for code in holdout_bins
    ], dtype=float)

    if np.any(~np.isfinite(raw)) or np.any(raw < 0):
        raise ValueError("Learned bin multipliers must be finite and nonnegative.")

    if np.isclose(raw.sum(), 0):
        raw = np.ones_like(raw)

    w_holdout = raw / raw.sum()

    H_P_holdout = _calibration_features(source.loc[P_holdout], x_values[P_holdout], y_values[P_holdout], terms)
    H_A_holdout = _calibration_features(source.loc[A_holdout], x_values[A_holdout], y_values[A_holdout], terms)

    result = _repair_eval_row(
        method=f"binned_multiplier_{bin_stat}",
        holdout_cycle=holdout_cycle,
        train_cycles=train_cycles,
        x_P=x_values[P_holdout],
        y_P=y_values[P_holdout],
        x_A=x_values[A_holdout],
        y_A=y_values[A_holdout],
        w=w_holdout,
        H_P=H_P_holdout,
        H_A=H_A_holdout,
        terms=terms,
    )

    bin_table = pd.DataFrame({
        "bin": np.arange(n_actual_bins),
        "left": edges[:-1],
        "right": edges[1:],
        "multiplier": multipliers,
    })

    return {
        "result": pd.DataFrame([result]),
        "fit_table": fit_table,
        "bin_table": bin_table,
        "exact_training_weights": exact_table,
        "holdout_weights": pd.Series(w_holdout, index=source.index[A_holdout], name="w_binned_multiplier"),
    }


def lin_mult_calibrator(
    df,
    x,
    y,
    cycle_col,
    holdout_cycle,
    regime,
    base_mask=None,
    dropna=True,
    terms=("X", "Y", "X^2", "XY"),
    train_cycles=None,
    ridge=1e-6,
    clip_log_multiplier=None,
    tol=1e-9,
    balance_tol=1e-6,
    std_balance_tol=1e-8,
    maxiter=1000,
):
    source, work = _prepare_frame(df, x=x, y=y, base_mask=base_mask, dropna=dropna)

    if cycle_col not in source.columns:
        raise ValueError(f"Column '{cycle_col}' not found.")

    x_values = work["X"].to_numpy()
    y_values = work["Y"].to_numpy()
    train_cycles = _default_train_cycles(source, cycle_col, holdout_cycle, train_cycles)

    exact_table, fit_table = _training_exact_entropy_weights(
        source=source,
        x_values=x_values,
        y_values=y_values,
        cycle_col=cycle_col,
        train_cycles=train_cycles,
        regime=regime,
        terms=terms,
        tol=tol,
        balance_tol=balance_tol,
        std_balance_tol=std_balance_tol,
        maxiter=maxiter,
    )

    H_train = exact_table.loc[:, list(terms)].to_numpy(dtype=float) if len(terms) else np.empty((len(exact_table), 0))
    multiplier_train = exact_table["multiplier"].to_numpy(dtype=float)

    model = _fit_log_multiplier_rule(
        H_train,
        multiplier_train,
        ridge=ridge,
    )

    P_holdout, A_holdout = _cycle_masks(source, cycle_col, holdout_cycle, regime)

    if int(P_holdout.sum()) == 0:
        raise ValueError(f"Holdout cycle '{holdout_cycle}' has no benchmark rows.")

    if int(A_holdout.sum()) == 0:
        raise ValueError(f"Holdout cycle '{holdout_cycle}' has no restricted rows.")

    H_P_holdout = _calibration_features(source.loc[P_holdout], x_values[P_holdout], y_values[P_holdout], terms)
    H_A_holdout = _calibration_features(source.loc[A_holdout], x_values[A_holdout], y_values[A_holdout], terms)

    w_holdout = _predict_multiplier_weights(
        H_A_holdout,
        model,
        clip_log_multiplier=clip_log_multiplier,
    )

    result = _repair_eval_row(
        method="linear_multiplier",
        holdout_cycle=holdout_cycle,
        train_cycles=train_cycles,
        x_P=x_values[P_holdout],
        y_P=y_values[P_holdout],
        x_A=x_values[A_holdout],
        y_A=y_values[A_holdout],
        w=w_holdout,
        H_P=H_P_holdout,
        H_A=H_A_holdout,
        terms=terms,
    )

    coef_table = pd.DataFrame({
        "term": ["intercept", *terms],
        "coef": np.r_[model["intercept"], model["coef"]],
    })

    fit_stats = {
        key: model[key]
        for key in ("ridge", "rmse_log_multiplier", "mae_log_multiplier")
        if key in model
    }

    return {
        "result": pd.DataFrame([result]),
        "fit_table": fit_table,
        "coef_table": coef_table,
        "fit_stats": fit_stats,
        "exact_training_weights": exact_table,
        "model": model,
        "holdout_weights": pd.Series(w_holdout, index=source.index[A_holdout], name="w_linear_multiplier"),
    }


# display

def prospective_repair_comparison(
    df,
    x,
    y,
    cycle_col,
    holdout_cycle,
    regime,
    base_mask=None,
    dropna=True,
    terms=("X", "Y", "X^2", "XY"),
    train_cycles=None,
    n_bins=10,
    bin_transform="log1p",
    bin_stat="mean",
    ridge=1e-6,
    clip_log_multiplier=None,
    tol=1e-9,
    balance_tol=1e-6,
    std_balance_tol=1e-8,
    maxiter=1000,
):
    binned = bin_mult_calibrator(
        df=df,
        x=x,
        y=y,
        cycle_col=cycle_col,
        holdout_cycle=holdout_cycle,
        regime=regime,
        base_mask=base_mask,
        dropna=dropna,
        terms=terms,
        train_cycles=train_cycles,
        n_bins=n_bins,
        bin_transform=bin_transform,
        bin_stat=bin_stat,
        tol=tol,
        balance_tol=balance_tol,
        std_balance_tol=std_balance_tol,
        maxiter=maxiter,
    )

    linear = lin_mult_calibrator(
        df=df,
        x=x,
        y=y,
        cycle_col=cycle_col,
        holdout_cycle=holdout_cycle,
        regime=regime,
        base_mask=base_mask,
        dropna=dropna,
        terms=terms,
        train_cycles=train_cycles,
        ridge=ridge,
        clip_log_multiplier=clip_log_multiplier,
        tol=tol,
        balance_tol=balance_tol,
        std_balance_tol=std_balance_tol,
        maxiter=maxiter,
    )

    result = pd.concat([binned["result"], linear["result"]], ignore_index=True)

    return {
        "result": result,
        "binned": binned,
        "linear": linear,
    }


    # display

def prospective_repair_regimes(
    df,
    x,
    y,
    regimes,
    cycle_col,
    holdout_cycle,
    base_mask=None,
    dropna=True,
    terms=("X", "Y", "X^2", "XY"),
    train_cycles=None,
    n_bins=10,
    bin_transform="identity",
    bin_stat="mean",
    ridge=1e-6,
    clip_log_multiplier=10,
    tol=1e-9,
    balance_tol=1e-6,
    std_balance_tol=1e-8,
    maxiter=1000,
):
    results = []
    details = {}

    for regime_name, regime_rule in regimes.items():
        out = prospective_repair_comparison(
            df=df,
            x=x,
            y=y,
            cycle_col=cycle_col,
            holdout_cycle=holdout_cycle,
            regime=regime_rule,
            base_mask=base_mask,
            dropna=dropna,
            terms=terms,
            train_cycles=train_cycles,
            n_bins=n_bins,
            bin_transform=bin_transform,
            bin_stat=bin_stat,
            ridge=ridge,
            clip_log_multiplier=clip_log_multiplier,
            tol=tol,
            balance_tol=balance_tol,
            std_balance_tol=std_balance_tol,
            maxiter=maxiter,
        )

        result = out["result"].copy()
        result.insert(0, "regime", regime_name)

        results.append(result)
        details[regime_name] = out

    if results:
        result_table = pd.concat(results, ignore_index=True)
    else:
        result_table = pd.DataFrame()

    return {
        "result": result_table,
        "details": details,
    }


def prospective_repair_summary(result):
    preferred = [
        "regime",
        "method",
        "holdout_cycle",
        "n_train_cycles",
        "N_holdout",
        "n_holdout",
        "f_holdout",
        "beta_P",
        "beta_A",
        "beta_w",
        "gap_unweighted",
        "gap_weighted",
        "repair",
        "abs_gap_reduction",
        "ess",
        "ess_ratio",
        "weight_deff",
        "weight_cv",
        "max_relative_weight",
        "weight_ratio",
        "top_1pct_weight_share",
        "top_5pct_weight_share",
        "max_abs_balance_error",
        "max_abs_std_balance_error",
        "rms_std_balance_error",
        "support_violation_count",
        "max_std_support_violation",
        "min_support_margin",
    ]

    cols = [col for col in preferred if col in result.columns]
    return result.loc[:, cols].copy()