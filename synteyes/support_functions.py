# Imports
import numpy as np
import pandas as pd
import scipy.stats as stats

# Functions
def conditional_sgm(mu, cov, known_indices, known_values):
    """
    Calculate the conditional distribution of a single gaussian mixture model.

    Parameters:
    mu (np.ndarray): Mean vector of the single gaussian mixture model.
    cov (np.ndarray): Covariance matrix of the single gaussian mixture model.
    known_indices (list): Indices of the known variables.
    known_values (np.ndarray): Values of the known variables.

    Returns:
    np.ndarray: Mean vector of the conditional distribution.
    np.ndarray: Covariance matrix of the conditional distribution.
    """

    # Indices of the unknown variables
    unknown_indices = [i for i in range(len(mu)) if i not in known_indices]
    # Partition the mean vector
    mu_known = mu[known_indices]
    mu_unknown = mu[unknown_indices]

    # Partition the covariance matrix
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



def convert_to_single_synteyes(eigencornea, conv_ec, avg_ec, lens_za):
    """
    Convert the data in eigencornea domain back to the original SyntEyes format when only single eye needs to be created.

    Parameters:
    eigencornea (np.ndarray): The eigencornea data of size Nx18.
    conv_ec (np.ndarray): Matrix to reconvert eigencorneas to corneal surface Zernikes + pachy.
    avg_ec (np.ndarray): Average Zernike + pachy values (eigencorneas require zero mean).
    lens_za (np.ndarray): Anterior lens Zernike coefficients (in mm, 5th order, 5.5 mm diam).

    Returns:
    pd.dataFrame: The generated SyntEyes data.

    """
    # Create the Zerniken values from the eigencorneas
    zerniken = (
            0.001 * np.reshape(eigencornea[range(6, 18, 1)], (1, len(range(6, 18, 1)))) @ conv_ec.T
    )
    for idx in range(len(zerniken[0, :])):
        zerniken[:, idx] = np.add(zerniken[:, idx], avg_ec[:, idx])

    # SyntEyes in array form
    synteyes_array = np.append(eigencornea[range(6)], zerniken)

    # Make a dictionary from data
    synteyes = dict(CCT = synteyes_array[96])
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
                         * 10 ** 6
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

    # Add all zernike coefficients to the dictionary
    ind_lens = zernike_index(6)
    lens_za_array = np.tile(lens_za, (1, 1))
    for idx in range(lens_za_array.shape[1]):
        synteyes[str("LensAntZ(" + str(ind_lens[idx,0])+","+str(ind_lens[idx,1])+")")] = [lens_za_array[:, idx][0]]
    ind_cor = zernike_index(8)
    cor_za = np.reshape(synteyes_array[range(6, 51, 1)], (1, len(range(6, 51, 1))))
    for idx in range(cor_za.shape[1]):
        synteyes[str("CorAntZ(" + str(ind_cor[idx,0])+","+str(ind_cor[idx,1])+")")] = [cor_za[:, idx][0]]
    cor_zp = np.reshape(synteyes_array[range(51, 96, 1)], (1, len(range(51, 96, 1))))
    for idx in range(cor_zp.shape[1]):
        synteyes[str("CorPostZ(" + str(ind_cor[idx,0])+","+str(ind_cor[idx,1])+")")] = [cor_zp[:, idx][0]]

    # Convert data back to dataframe
    synteyes = pd.DataFrame.from_dict(synteyes)
    return synteyes


def create_retina_curvature(synteyes_jos, mu_retina, cov_retina):
    """
    Use the Axial Length of the SyntEyes from Jos to calculate the retina curvature.

    Parameters:
    synteyes_jos (np.ndarray): The generated SyntEyes data without retina curvature.
    mu_retina (np.ndarray): Mean vector for the retina curvature radii (in mm).
    cov_retina (np.ndarray): Covariance matrix for the retina curvature radii (in mm).

    Returns:
    pd.dataFrame: The generated SyntEyes data with retina curvature.

    """
    # Acquire the Axial Length of all the SyntEyes
    axial_lengths = np.array(synteyes_jos["AxialLength"]-synteyes_jos["RT"])         # The AL from SyntEyes includes the retina thickness while we defined it without

    # Determine the conditional distribution and create a retina with this
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

    # Reshape such that the retina can be added to the dataframe
    n = len(axial_lengths)
    cond_sgm = np.reshape(cond_sgm, (n, 3))

    # Add the retina to the dataframe
    synteyes_jos["ell_rx"] = cond_sgm[:, 0]
    synteyes_jos["ell_ry"] = cond_sgm[:, 1]
    synteyes_jos["ell_rz"] = cond_sgm[:, 2]
    return synteyes_jos

def create_mgmm_data(mu_c0,mu_c1,cov_c0,cov_c1,w_c0,w_c1,n):
    """
    Create N data points using scipy library.

    Parameters:
    mu_c0 (np.ndarray): The mean vector of the first Multivariate Gaussian Mixture Model component.
    mu_c1 (np.ndarray): The mean vector of the second Multivariate Gaussian Mixture Model component.
    cov_c0 (np.ndarray): The covariance matrix of the first Multivariate Gaussian Mixture Model component.
    cov_c1 (np.ndarray): The covariance matrix of the second Multivariate Gaussian Mixture Model component.
    w_c0 (np.ndarray): The weights of the first Multivariate Gaussian Mixture Model component.
    w_c1 (np.ndarray): The weights of the second Multivariate Gaussian Mixture Model component.
    n (int): The number of data points.

    Returns:
    np.ndarray: Dataset of N points from the Multivariate Gaussian Mixture Model.
    """
    comp0 = stats.multivariate_normal.rvs(mu_c0, cov_c0,size=n)
    comp1 = stats.multivariate_normal.rvs(mu_c1, cov_c1,size=n)
    data = w_c0*comp0 + w_c1*comp1
    return data

def nearest_psd(matrix):
    """
    Find the nearest positive semi-definite (PSD) matrix to an input matrix.

    Parameters:
    matrix (np.ndarray): The not PSD matrix.

    Returns:
    np.ndarray: The closest PSD matrix.

    """
    eigval, eigvec = np.linalg.eig(matrix)
    new_matrix = eigvec @ np.diag(np.maximum(eigval, 10 ** -6)) @ eigvec.T
    return new_matrix

def zernike_index(order):
    """
    Create a numpy array with the n, m coefficients of the SyntEyes zernike polynomial for the given order.

    Parameters:
    order (int): The order of the zernike polynomial.

    Returns:
    np.array: The n, m coefficients of the zernike polynomial.
    """
    idx = np.array([])
    for n in range(0,order+1):
        for m in range(-1*n,n+1,2):
            idx =np.append(idx,[n,m])

    idx = np.reshape(idx,(int(len(idx)/2),2))
    return idx