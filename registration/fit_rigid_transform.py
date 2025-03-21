import numpy as np

def fit_rigid_transform(A:np.array, B:np.array) -> np.array:
    """
    Calculates the best-fit transform that maps points A onto points B.
    Input:
        A: Nxm numpy array of source points
        B: Nxm numpy array of destination points
    Output:
        T: (m+1)x(m+1) homogeneous transformation matrix
    """
    
    # Check if A and B have same dimensions
    assert A.shape == B.shape
    
    # Get number of dimensions
    m = A.shape[1]
    
    # Translate points to their centroids
    centroid_A = np.mean(A, axis=0)
    centroid_B = np.mean(B, axis=0)
    AA = A - centroid_A
    BB = B - centroid_B
    
    # Rotation matrix
    H = np.dot(AA.T, BB)
    U, S, Vt = np.linalg.svd(H)
    R = np.dot(Vt.T, U.T)
    
    # Special reflection case
    if np.linalg.det(R) < 0:
        Vt[m-1,:] *= -1
        R = np.dot(Vt.T, U.T)
    
    # Translation
    t = centroid_B.reshape(-1,1) - np.dot(R, centroid_A.reshape(-1,1))
    
    # Homogeneous transformation
    T = np.eye(m+1)
    T[:m, :m] = R
    T[:m, -1] = t.ravel()
    
    return T
