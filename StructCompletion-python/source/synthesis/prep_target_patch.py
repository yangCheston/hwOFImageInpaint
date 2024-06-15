import numpy as np

def prep_target_patch(img, uvPixSub, option):
    imgH, imgW, Ch = img.shape

    numUvPix = uvPixSub.shape[0]

    uvPixSub = np.reshape(uvPixSub.T, (1, 2, numUvPix), order="F")

    refPatPos = option.refPatchPos[:, :2][..., None]
    trgPatchPos = (refPatPos + uvPixSub).astype(np.int32)

    trgPatch = np.zeros((option.pNumPix, Ch, numUvPix))
    for i in range(Ch):
        for j in range(numUvPix):
            trgPatch[:, i, j] = img[trgPatchPos[:, 1, j], trgPatchPos[:, 0, j], i].copy()


    return trgPatch