import numpy as np
import cv2


def patch_cost_prox(srcPos, trgPos, uvDtBdPixPos, optS):

    d = srcPos - trgPos
    d = np.sqrt(np.sum(d ** 2, axis=1))

    d = d/optS.imgSize
    uvDtBdPixPos = uvDtBdPixPos.copy() / optS.imgSize
    costProx = d - uvDtBdPixPos - optS.proxThres
    costProx[costProx <= 0] = 0
    return costProx

def patch_cost_direct(uvPlaneIDData, trgPos, srcPos, modelPlane, opt):
    numUvPix = trgPos.shape[0]
    costDirect = opt.lambdaDirect * np.ones((numUvPix, 2), dtype=np.float32)

    for indPlane in range(modelPlane.numPlane):
        uvPlaneIndCur = uvPlaneIDData == indPlane
        numPlanePixCur = sum(uvPlaneIndCur)

        if indPlane == modelPlane.numPlane - 1:
            costDirect[uvPlaneIndCur, :] = opt.imgSize * opt.directThres
        else:
            rectMat = modelPlane.rectMat[indPlane]
            h7 = rectMat[2, 0]
            h8 = rectMat[2, 1]

            if numPlanePixCur != 0:
                trgPosCur = trgPos[uvPlaneIndCur, :].copy() - 1
                srcPosCur = srcPos[uvPlaneIndCur, :].copy() - 1

                for itheta in range(2):
                    rotMat = modelPlane.rotMat[indPlane][itheta]

                    rotRectMat = rotMat
                    rotRectMat[2, 0] = h7
                    rotRectMat[2, 1] = h8
                    rotRectMat = rotRectMat.T

                    trgPosCurRect = np.hstack([trgPosCur, np.ones((numPlanePixCur, 1))]).dot(rotRectMat)
                    trgPosCurRect /= trgPosCurRect[:, 2:3]

                    srcPosCurRect = np.hstack([srcPosCur, np.ones((numPlanePixCur, 1))]).dot(rotRectMat)
                    srcPosCurRect /= srcPosCurRect[:, 2:3]

                    costDirect[uvPlaneIndCur, itheta] = np.abs(srcPosCurRect[:, 1] - trgPosCurRect[:, 1])

    costDirect = np.min(costDirect, axis=1) / opt.imgSize
    costDirect[costDirect >= opt.directThres] = opt.directThres
    return costDirect

def patch_cost_plane(mLogLPlaneProb, uvPlaneIDData, trgPixSub, srcPixSub):
    H, W, numPlane = mLogLPlaneProb.shape

    srcPixSub = np.round(srcPixSub)
    uvPlaneIDData_in = uvPlaneIDData.astype(np.int32)

    return mLogLPlaneProb[trgPixSub[:, 1].astype(np.int32), trgPixSub[:, 0].astype(np.int32), uvPlaneIDData_in] + \
           mLogLPlaneProb[srcPixSub[:, 1].astype(np.int32), srcPixSub[:, 0].astype(np.int32), uvPlaneIDData_in]

def patch_cost_app(trgPatch, srcPatch, option):
    uvBias = None

    patchDist = trgPatch - srcPatch

    if option.costType == "L1":
        patchDist = np.abs(patchDist)
    else:
        patchDist = patchDist ** 2

    patchDist *= option.wPatch[..., None, None]
    costApp = np.squeeze(np.sum(np.sum(patchDist, axis=0), axis=0))

    return costApp, uvBias

def patch_cost(trgPatch, srcPatch, modelPlane, uvPlaneIDData,
                    trgPos, srcTform, srcPosMap, bdPos, option):

    numUvPix = srcPatch.shape[2]
    costPatchCand = np.zeros((numUvPix, 5), dtype=np.float32)

    costApp, uvBiasCand = patch_cost_app(trgPatch, srcPatch, option)

    srcPos = srcTform[:, 6:8]

    costPlane = patch_cost_plane(modelPlane.mLogPlaneProb, uvPlaneIDData, trgPos, srcPos)

    costDirect = patch_cost_direct(uvPlaneIDData, trgPos, srcPos, modelPlane, option)

    costProx = patch_cost_prox(srcPos, trgPos, bdPos, option)

    costPatchCand[:, 0] = costApp
    costPatchCand[:, 1] = option.lambdaPlane * costPlane
    costPatchCand[:, 3] = option.lambdaDirect * costDirect
    costPatchCand[:, 4] = option.lambdaProx * costProx

    return costPatchCand, uvBiasCand