import numpy as np
import pandas as pd
import scipy.stats as stats
import json
from pathlib import Path

from shiny import reactive
from shiny.express import input, render, ui


def conditional_sgm(mu, cov, known_indices, known_values):
    """Compute the conditional Gaussian distribution.

    Parameters
    ----------
    mu : np.ndarray
        Mean vector of the full Gaussian.
    cov : np.ndarray
        Covariance matrix of the full Gaussian.
    known_indices : list[int]
        Indices of variables conditioned on.
    known_values : np.ndarray | float
        Observed values for the variables in ``known_indices``.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Conditional mean vector and conditional covariance matrix.
    """
    unknown_indices = [i for i in range(len(mu)) if i not in known_indices]

    mu_known = mu[known_indices]
    mu_unknown = mu[unknown_indices]

    cov_known_known = cov[np.ix_(known_indices, known_indices)]
    cov_known_unknown = cov[np.ix_(known_indices, unknown_indices)]
    cov_unknown_known = cov[np.ix_(unknown_indices, known_indices)]
    cov_unknown_unknown = cov[np.ix_(unknown_indices, unknown_indices)]

    cov_known_known_inv = np.linalg.inv(cov_known_known)

    conditional_mean = mu_unknown + cov_unknown_known @ cov_known_known_inv @ (
        known_values - mu_known
    )
    conditional_cov = (
        cov_unknown_unknown
        - cov_unknown_known @ cov_known_known_inv @ cov_known_unknown
    )

    return conditional_mean, conditional_cov


def zernike_index(order):
    """Create Zernike polynomial (n, m) index pairs.

    Parameters
    ----------
    order : int
        Maximum radial Zernike order.

    Returns
    -------
    np.ndarray
        Array of shape ``(k, 2)`` containing ``(n, m)`` pairs.
    """
    idx = np.array([])
    for n in range(0, order + 1):
        for m in range(-1 * n, n + 1, 2):
            idx = np.append(idx, [n, m])

    idx = np.reshape(idx, (int(len(idx) / 2), 2))
    return idx


def convert_to_single_orig_synteyes(eigencornea, conv_ec, avg_ec, lens_za):
    """Convert one eigencornea sample to SyntEyes format.

    Parameters
    ----------
    eigencornea : np.ndarray
        One eigencornea sample containing biometric latent variables.
    conv_ec : np.ndarray
        Conversion matrix from eigencornea coefficients to corneal terms.
    avg_ec : np.ndarray
        Mean corneal terms added after conversion.
    lens_za : np.ndarray
        Lens Zernike coefficients.

    Returns
    -------
    pandas.DataFrame
        Single-row dataframe with SyntEyes fields.
    """
    zerniken = (
        0.001
        * np.reshape(eigencornea[range(6, 18, 1)], (1, len(range(6, 18, 1))))
        @ conv_ec.T
    )
    for idx in range(len(zerniken[0, :])):
        zerniken[:, idx] = np.add(zerniken[:, idx], avg_ec[:, idx])

    synteyes_array = np.append(eigencornea[range(6)], zerniken)

    synteyes = dict(CCT=synteyes_array[96])
    synteyes["ACD"] = synteyes_array[0]
    synteyes["LT"] = synteyes_array[1]
    synteyes["AxialLength"] = synteyes_array[2]
    synteyes["VD"] = (
        synteyes_array[2]
        - synteyes_array[0]
        - synteyes_array[1]
        - synteyes_array[96]
        - 0.2
    )
    synteyes["RT"] = 0.2
    synteyes["Rla"] = synteyes_array[3]
    synteyes["Rlp"] = synteyes_array[4]
    synteyes["Qla"] = -3.1316
    synteyes["Qlp"] = -1
    synteyes["Pupil"] = 5
    synteyes["nc"] = 1.376
    synteyes["na"] = 1.336
    synteyes["nv"] = 1.336
    synteyes["num5"] = synteyes_array[5]
    synteyes["nl"] = (
        1000
        * (
            synteyes["nv"] * (synteyes["LT"] - synteyes["Rla"])
            + synteyes["na"] * (synteyes["LT"] + synteyes["Rlp"])
        )
        + synteyes["num5"] * synteyes["Rla"] * synteyes["Rlp"]
        - np.sqrt(
            -4
            * 10**6
            * synteyes["na"]
            * synteyes["nv"]
            * synteyes["LT"]
            * (synteyes["LT"] - synteyes["Rla"] + synteyes["Rlp"])
            + (
                1000 * synteyes["nv"] * (-1 * synteyes["LT"] + synteyes["Rla"])
                + 1000 * synteyes["na"] * (-1 * synteyes["LT"] - 1 * synteyes["Rlp"])
                - synteyes["num5"] * synteyes["Rla"] * synteyes["Rlp"]
            )
            ** 2
        )
    ) / (2000 * (synteyes["LT"] - synteyes["Rla"] + synteyes["Rlp"]))

    ind_lens = zernike_index(6)
    lens_za_array = np.tile(lens_za, (1, 1))
    for idx in range(lens_za_array.shape[1]):
        lens_n = int(ind_lens[idx, 0])
        lens_m = int(ind_lens[idx, 1])
        synteyes[f"LensAntZ({lens_n},{lens_m})"] = [lens_za_array[:, idx][0]]
    ind_cor = zernike_index(8)
    cor_za = np.reshape(synteyes_array[range(6, 51, 1)], (1, len(range(6, 51, 1))))
    for idx in range(cor_za.shape[1]):
        cor_n = int(ind_cor[idx, 0])
        cor_m = int(ind_cor[idx, 1])
        synteyes[f"CorAntZ({cor_n},{cor_m})"] = [cor_za[:, idx][0]]
    cor_zp = np.reshape(synteyes_array[range(51, 96, 1)], (1, len(range(51, 96, 1))))
    for idx in range(cor_zp.shape[1]):
        cor_n = int(ind_cor[idx, 0])
        cor_m = int(ind_cor[idx, 1])
        synteyes[f"CorPostZ({cor_n},{cor_m})"] = [cor_zp[:, idx][0]]

    return pd.DataFrame.from_dict(synteyes)


def create_retina_curvature(synteyes_orig, mu_retina, cov_retina):
    """Add retinal curvature values conditioned on axial length.

    Parameters
    ----------
    synteyes_orig : pandas.DataFrame
        Generated SyntEyes dataframe without retinal curvature columns.
    mu_retina : np.ndarray
        Mean vector for the retina model.
    cov_retina : np.ndarray
        Covariance matrix for the retina model.

    Returns
    -------
    pandas.DataFrame
        Input dataframe with ``ret_rx``, ``ret_ry``, and ``ret_rz`` added.
    """
    axial_lengths = np.array(synteyes_orig["AxialLength"] - synteyes_orig["RT"])

    cond_sgm = np.array([])
    for al in axial_lengths:
        conditional_mean_sgm, conditional_cov_sgm = conditional_sgm(
            mu_retina, cov_retina, [0], al
        )
        cond_sgm = np.append(
            cond_sgm,
            stats.multivariate_normal.rvs(
                mean=conditional_mean_sgm, cov=conditional_cov_sgm, size=1
            ),
            axis=0,
        )

    n_rows = len(axial_lengths)
    cond_sgm = np.reshape(cond_sgm, (n_rows, 3))

    synteyes_orig["ret_rx"] = cond_sgm[:, 0]
    synteyes_orig["ret_ry"] = cond_sgm[:, 1]
    synteyes_orig["ret_rz"] = cond_sgm[:, 2]
    return synteyes_orig


def create_mgmm_data(mu_c0, mu_c1, cov_c0, cov_c1, w_c0, w_c1, n):
    """Sample from a weighted two-component Gaussian mixture model.

    Parameters
    ----------
    mu_c0 : np.ndarray
        Mean vector of component 0.
    mu_c1 : np.ndarray
        Mean vector of component 1.
    cov_c0 : np.ndarray
        Covariance matrix of component 0.
    cov_c1 : np.ndarray
        Covariance matrix of component 1.
    w_c0 : float
        Weight for component 0 sample.
    w_c1 : float
        Weight for component 1 sample.
    n : int
        Number of samples to generate.

    Returns
    -------
    np.ndarray
        Generated samples in latent eigencornea space.
    """
    comp0 = stats.multivariate_normal.rvs(mu_c0, cov_c0, size=n)
    comp1 = stats.multivariate_normal.rvs(mu_c1, cov_c1, size=n)
    return w_c0 * comp0 + w_c1 * comp1


def nearest_psd(matrix):
    """Project a matrix to a positive semi-definite approximation.

    Parameters
    ----------
    matrix : np.ndarray
        Input square matrix.

    Returns
    -------
    np.ndarray
        Matrix with eigenvalues clipped to a small positive threshold.
    """
    eigval, eigvec = np.linalg.eig(matrix)
    return eigvec @ np.diag(np.maximum(eigval, 10**-6)) @ eigvec.T


def generate_synteyes(n):
    eigen_data = create_mgmm_data(
        mu_orig[0],
        mu_orig[1],
        cov_orig0,
        cov_orig1,
        weights_orig[0],
        weights_orig[1],
        n,
    )

    synteyes_orig = pd.DataFrame([])
    for i in range(len(eigen_data)):
        synteyes_orig_single = convert_to_single_orig_synteyes(
            eigen_data[i], conv_ec_orig, avg_ec_orig, lens_za_orig
        )
        synteyes_orig = pd.concat(
            [synteyes_orig, synteyes_orig_single], ignore_index=True
        )

    return create_retina_curvature(synteyes_orig, MU_AL_RADII, COV_AL_RADII)


# Original Synteyes parameters
modeldata_path = Path(__file__).parent / "modeldata.json"
modeldata = json.loads(modeldata_path.read_text(encoding="utf-8"))

conv_ec_orig = np.array(modeldata["conv_ec_orig"])
avg_ec_orig = np.array(modeldata["avg_ec_orig"])
lens_za_orig = np.array(modeldata["lens_za_orig"])
weights_orig = np.array(modeldata["weights_orig"])
mu_orig = np.array(modeldata["mu_orig"])
cov_orig0 = np.array(modeldata["cov_orig0"])
cov_orig1 = np.array(modeldata["cov_orig1"])

cov_orig = np.zeros((2, np.shape(cov_orig0)[0], np.shape(cov_orig0)[1]))
cov_orig[0] = nearest_psd(cov_orig0)
cov_orig[1] = cov_orig1

# Retina model parameters
MU_AL_RADII = np.array([23.85, 11.89, 11.66, 10.55])
COV_AL_RADII = np.array(
    [
        [1.82, 0.56, 0.42, 0.81],
        [0.56, 0.36, 0.19, 0.18],
        [0.42, 0.19, 0.24, 0.16],
        [0.81, 0.18, 0.16, 0.48],
    ]
)

COLUMN_HINTS = {
    "CCT": "Pachymetry (mm)",
    "ACD": "Anterior chamber depth (mm)",
    "LT": "Lens thickness (mm)",
    "AxialLength": "Axial length (mm)",
    "VD": "Vitreous depth excluding retina (mm)",
    "RT": "Retinal thickness (fixed value 0.2 mm)",
    "Rla": "Radius of curvature for the anterior lens surface (mm)",
    "Rlp": "Radius of curvature for the posterior lens surface (mm)",
    "Qla": "Asphericity for the anterior lens surface (Navarro eye model)",
    "Qlp": "Asphericity for the posterior lens surface (Navarro eye model)",
    "Pupil": "Pupil diameter (fixed value 5 mm)",
    "Rret": "Radius of curvature of the retinal surface (Navarro eye model)",
    "nc": "Refractive index of the cornea",
    "na": "Refractive index of the aqueous",
    "nv": "Refractive index of the vitreous",
    "ret_rx": "Retinal ellipsoid radius along x (mm)",
    "ret_ry": "Retinal ellipsoid radius along y (mm)",
    "ret_rz": "Retinal ellipsoid radius along z (mm)",
}

PREFIX_HINTS = {
    "CorAntZ": "Zernikes of anterior corneal surface (mm, 8th order, 6.5 mm diameter)",
    "CorPostZ": "Zernikes of posterior corneal surface (mm, 8th order, 6.5 mm diameter)",
    "LensAntZ": "Zernikes of anterior lens surface (mm, 5th order, 5.5 mm diameter)",
}

ui.tags.style(
    "table { display: block; overflow-x: auto; }", "th, td { white-space: nowrap; }"
)
ui.tags.script(
    f"""
(() => {{
    const columnHints = {json.dumps(COLUMN_HINTS)};
    const prefixHints = {json.dumps(PREFIX_HINTS)};

    const hintForColumn = (columnName) => {{
        if (columnHints[columnName]) return columnHints[columnName];
        for (const [prefix, hint] of Object.entries(prefixHints)) {{
            if (columnName.startsWith(prefix)) return hint;
        }}
        return "";
    }};

    const applyColumnHints = () => {{
        document.querySelectorAll("table.dataframe thead th").forEach((th) => {{
            const columnName = (th.textContent || "").trim();
            if (!columnName) return;
            const hint = hintForColumn(columnName);
            if (hint) th.setAttribute("title", hint);
        }});
    }};

    document.addEventListener("DOMContentLoaded", applyColumnHints);
    new MutationObserver(applyColumnHints).observe(document.body, {{
        childList: true,
        subtree: true,
    }});
}})();
"""
)

with ui.card():
    ui.card_header("Create 3D SyntEyes")
    with ui.layout_columns(class_="align-items-end"):
        ui.input_numeric("n_eyes", "Number of 3D SyntEyes", value=10, min=1, step=1)
        ui.input_action_button("generate", "Generate SyntEyes")

        def conditional_download_button(button):
            fallback = ui.input_action_button(
                button.output_id + "_fallback", label=button.label, disabled=True
            )

            def wrapper():
                if input.generate() == 0 or input.n_eyes() == 0:
                    return fallback

                return button

            wrapper.__name__ = button.output_id + "_wrapper"

            return render.ui(wrapper)

        @conditional_download_button
        @render.download(filename="synteyes.csv", label="Download CSV")
        def download_csv():
            yield generated_data().to_csv(index=False)

        @conditional_download_button
        @render.download(filename="synteyes.json", label="Download JSON")
        def download_json():
            def _json_default(obj):
                if isinstance(obj, np.generic):
                    return obj.item()
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                raise TypeError(
                    f"Object of type {type(obj).__name__} is not JSON serializable"
                )

            records = generated_data().to_dict(orient="records")
            yield json.dumps(records, separators=(",", ":"), default=_json_default)


@reactive.calc
@reactive.event(input.generate)
def generated_data():
    n = int(input.n_eyes())
    if n < 1:
        raise ValueError("Number of SyntEyes must be at least 1")
    return generate_synteyes(n)


@reactive.calc
@reactive.event(input.generate_retina)
def generated_retina_curvature():
    al = float(input.single_axial_length())
    conditional_mean_sgm, conditional_cov_sgm = conditional_sgm(
        MU_AL_RADII, COV_AL_RADII, [0], al
    )
    rx, ry, rz = stats.multivariate_normal.rvs(
        mean=conditional_mean_sgm, cov=conditional_cov_sgm, size=1
    )
    return pd.DataFrame(
        [
            {
                "AxialLength": al,
                "ret_rx": float(rx),
                "ret_ry": float(ry),
                "ret_rz": float(rz),
            }
        ]
    )


@reactive.calc
def displayed_data():
    df = generated_data()
    if not input.compact_view():
        return df

    preferred_columns = [
        "CCT",
        "ACD",
        "LT",
        "AxialLength",
        "VD",
        "ret_rx",
        "ret_ry",
        "ret_rz",
    ]
    selected_columns = [col for col in preferred_columns if col in df.columns]
    return df[selected_columns]


with ui.card():
    with ui.card_header():
        "Result"
        with ui.toolbar(align="right"):
            ui.toolbar_input_select(
                id="compact_view",
                label="Compact view",
                choices={False: "Compact", True: "Expanded"},
                selected="Compact",
            )

    @render.ui
    def result_summary():
        if input.generate() == 0:
            return ui.markdown(
                "Enter the amount of eyes and click **Generate SyntEyes**."
            )

        df = generated_data()
        shown_df = displayed_data()
        mode_label = "compact" if input.compact_view() else "expanded"
        return ui.markdown(
            f"Generated **{len(df)}** SyntEyes with **{df.shape[1]}** total columns. "
            f"Showing **{shown_df.shape[1]}** columns in **{mode_label}** mode (first 20 rows)."
        )

    @render.table
    def result_table():
        return displayed_data().head(20)


with ui.card():
    ui.card_header("Create retina radii from axial length")
    with ui.layout_columns():
        ui.input_numeric(
            "single_axial_length",
            "Axial length of the eye [mm]",
            value=24.0,
            min=0.1,
            step=0.1,
        )
        ui.input_action_button("generate_retina", "Generate Retina Radii")

    @render.ui
    def retina_result():
        @render.table
        def retina_result_table():
            return generated_retina_curvature().round(2)

        if input.generate_retina() == 0:
            return ui.markdown(
                "Enter an axial length and click **Generate Retina Radii**."
            )

        return retina_result_table
