# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 10:07:32 2015

@author: Christopher J Steele (except for one that I took from stackoverflow ;-))
"""

def niiLoad(full_fileName):
    import nibabel as nb
    img=nb.load(full_fileName)
    return img.get_data(), img.affine

def niiSave(full_fileName, data, aff, data_type='float32', CLOBBER=True):
    """
    Convenience function to write nii data to file
    Input:
        - full_fileName:    you can figure that out
        - data:             numpy array
        - aff:              affine matrix
        - data_type:        numpy data type ('uint32', 'float32' etc)
        - CLOBBER:          overwrite existing file
    """
    import os
    import nibabel as nb

    img=nb.Nifti1Image(data,aff)
    if data_type is not None: #if there is a particular data_type chosen, set it
        data=data.astype(data_type)
        img.set_data_dtype(data_type)
    if not(os.path.isfile(full_fileName)) or CLOBBER:
        img.to_filename(full_fileName)
    else:
        print("This file exists and CLOBBER was set to false, file not saved.")
        print(full_fileName)

def create_dir(some_directory):
    """
    Create directory if it does not exist
    """
    import os
    if not os.path.exists(some_directory):
        os.mkdir(some_directory)
    
def natural_sort(l): 
    """
    Returns alphanumerically sorted input
    #natural sort from the interwebs (http://stackoverflow.com/questions/11150239/python-natural-sorting)        
    """
    import re

    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)

def get_com(img_data):
    """
    Return the center of mass of image data (numpy format)
    """
    import scipy.ndimage.measurements as meas
    return meas.center_of_mass(img_data)

def get_img_bounds(img_data):
    """
    Gets the min and max in the three dimensions of 3d image data and returns 
    a 3,2 matrix of values of format dim*{min,max}
    """
    import numpy as np
    bounds=np.zeros((3,2))
    # x
    for x in np.arange(img_data.shape[0]):
        if img_data[x,:,:].any(): #if there are any non-zero elements in this slice
            bounds[0,0]=x
            break
    for x in np.arange(img_data.shape[0])[::-1]:
        if img_data[x,:,:].any():
            bounds[0,1]=x
            break
    # y
    for y in np.arange(img_data.shape[1]):
        if img_data[:,y,:].any():
            bounds[1,0]=y
            break
    for y in np.arange(img_data.shape[1])[::-1]:
        if img_data[:,y,:].any():
            bounds[1,1]=y
            break
    # z
    for z in np.arange(img_data.shape[2]):
        if img_data[:,:,z].any():
            bounds[2,0]=z
            break
    for z in np.arange(img_data.shape[2])[::-1]:
        if img_data[:,:,z].any():
            bounds[2,1]=z
            break

    return bounds

def erode_mask(img_data,iterations=1,mask=None,structure=None,LIMIT_EROSION=False,min_vox_count=10):
    """
    Binary erosion of 3D image data using scipy.ndimage package
    If LIMIT_EROSION=True, will always return the smallest element mask with count>=min_vox_count
    INPUT:     
             - img_data (np image array)
             - iterations = number of iterations for erosion
             - mask = mask img (np array) for restricting erosion
			- structure = as defined by ndimage (should be 3,1 (no diags) if None)
			- LIMIT_EROSION = limits erosion to the step before the mask ended up with no voxels
			- min_vox_count = minimum number of voxels to have in the img_data and still return this version, otherwise returns previous iteration
            
    Returns mask data in same format as input
    """
    import numpy as np
    import scipy.ndimage as ndimage

    if structure is None:
        structure=ndimage.morphology.generate_binary_structure(3,1) #neighbourhood

    #img_data=ndimage.morphology.binary_opening(img_data,iterations=1,structure=structure).astype(img_data.dtype) #binary opening   
	if not LIMIT_EROSION:
	    img_data=ndimage.morphology.binary_erosion(img_data,iterations=iterations,mask=mask,structure=structure).astype(img_data.dtype) #now erode once with the given structure
    else:
		for idx in range(0,iterations):
			img_data_temp=ndimage.morphology.binary_erosion(img_data,iterations=1,mask=mask,structure=structure).astype(img_data.dtype) #now erode once with the given structure
			if np.sum(img_data_temp) >= min_vox_count:
				img_data=img_data_temp
			else:
				break
    return img_data

def generate_overlap_mask(mask1,mask2,structure=None):
    """
    Create an overlap mask where a dilated version of mask1 overlaps mask2 (logical AND operation)
    Uses ALL elements >0 for both masks, masks must be in same space
    Dilates with full connectivity (3,3) by default
    """
    import scipy.ndimage as ndi
    
    if structure is None:
        structure=ndi.morphology.generate_binary_structure(3,3)
        
    overlap_mask=ndi.morphology.binary_dilation(mask1,iterations=1,structure=structure).astype(mask1.dtype)*mask2
    overlap_mask[overlap_mask>0]=1
    return ndi.binary_closing(overlap_mask,structure=structure).astype(mask1.dtype)

def select_mask_idxs(mask_img_data,mask_subset_idx):
    """
    Returns a reduced mask_img_data that includes only those indices in mask_subset_idx
    Useful for creating boundary/exclusion masks for cortical regions that are next to the mask of interest
    """
    import numpy as np    
    #stupid and probably not fast, but it works
    reduced_mask_data=np.zeros_like(mask_img_data)
    for idx in mask_subset_idx:
        reduced_mask_data[mask_img_data==idx]=idx
    return reduced_mask_data

#def extract_stats_from_masked_image(img,mask,result='all',nonzero_stats=True,max_val=None):
#    """
#    XXX - THIS SHOULD BE CHECKED TO MAKE SURE THAT IT WORKS WITH ALL INPUTS - ASSUMPTIONS ABOUT TRANSFORMS WERE MADE XXX
#    Extract values from img at mask location
#    Images do not need to be the same resolution, though this is highly preferred
#        - resampling taken care of with nilearn tools
#        - set nonzero_stats to false to include 0s in the calculations
#        - clipped to >max_val 
#       Input:
#         - img:             3D image
#         - mask:            3D mask in same space (though not necessarily same res)
#         - result:          specification of what output you require {'all','data','mean','median','std','min','max'}
#         - nonzero_stats:   calculate without 0s, or with {True,False}
#         - max_val:         set max val for clipping (eg., for FA maps, set to 1.0)
#         
#       Output: (in data structure)
#         - data, mean, median, std, minn, maxx
#         - or all in data structure if result='all'
#    
#       e.g.,
#         - res=extract_stats_from_masked_image(img,mask)
#    """
#    
#    from nilearn.image import resample_img
#    import nibabel as nb
#    import numpy as np
#    
#    class return_results(object):
#        #output results as an object with these values
#        def __init__(self,data,mean,median,std,minn,maxx):
#            self.data=data
#            self.mean=mean
#            self.median=median
#            self.std= std
#            self.minn=minn
#            self.maxx=maxx
#        
#        def __str__(self):
#            # defines what is returned when print is called on this class
#            template_txt="""
#            len(data): {data_len}
#            mean     : {mean}
#            median   : {median}
#            std      : {std}
#            max      : {maxx}
#            min      : {minn}
#            """
#            return template_txt.format(data_len=len(self.data),mean=self.mean, median=self.median, std=self.std, maxx=self.maxx, minn=self.minn)
#        
#    daff=nb.load(img).affine
#    d=nb.load(img).get_data()
#    #print(daff)
#
#    maff=nb.load(mask).affine
#    #print(maff)
#    
#    # see if we need to resample the mask to the img
#    if not np.array_equal(np.diagonal(maff),np.diagonal(daff)):
#        mask=resample_img(mask,daff,np.shape(d),interpolation='nearest').get_data()
#    else:
#        mask=nb.load(mask).get_data()
#    
#    dx=np.ma.masked_array(d,np.ma.make_mask(np.logical_not(mask))).compressed()
#    if nonzero_stats:
#        dx=dx[dx>0]
#    if not max_val is None:
#        dx[dx>max_val]=max_val
#    
#    results=return_results(dx,np.mean(dx),np.median(dx),np.std(dx),np.min(dx),np.max(dx))
#    
#    if result=='all':
#        return results
#    elif result=='data':
#        return results.data
#    elif result=='mean':
#        return results.mean
#    elif result=='median':
#        return results.median
#    elif result=='std':
#        return results.std
#    elif result=='max':
#        return results.max
#    elif result=='min':
#        return results.min

def extract_stats_from_masked_image(img_fname,mask_fname,thresh_mask_fname=None,combined_mask_output_fname=None,thresh_val=1,\
                                    thresh_type='upper',result='all',label_subset=None,SKIP_ZERO_LABEL=True,nonzero_stats=True,\
                                    erode_vox=None,min_val=None,max_val=None,VERBOSE=False):
    """
    XXX - THIS SHOULD BE CHECKED TO MAKE SURE THAT IT WORKS WITH ALL INPUTS - ASSUMPTIONS ABOUT TRANSFORMS WERE MADE XXX
    Extract values from img at mask location
    Images do not need to be the same resolution, though this is highly preferred
        - resampling taken care of with nilearn tools
        - set nonzero_stats to false to include 0s in the calculations
        - clipped to >max_val 
       Input:
         - img_fname:                   3D image
         - mask_fname:                  3D mask in same space, single or multiple labels (though not necessarily same res)
         - thresh_mask_fname:           3D mask for thresholding, can be binary or not
         - combined_mask_output_fname:  output final binary mask to this file (for confirmation of regions etc)
         - thresh_val:                  upper value for thresholding thresh_mask_fname, values above/below this are set to 0
         - thresh_type:                 {'upper' = > thresh_val = 0,'lower' < thresh_val = 0}
         - result:                      specification of what output you require {'all','data','mean','median','std','min','max'}
         - label_subset:                list of label values to report stats on    
         - SKIP_ZERO_LABEL:             skip where label_val==0 {True,False} (usually the background label)  - XXX probably does not work properly when False :-/
         - nonzero_stats:               calculate without 0s in img_fname, or with {True,False}
         - erode_vox                    number of voxels to erode mask by (simple dilation-erosion, then erosion, None for no erosion)
         - min_val:                     set min val for clipping (eg., for FA maps, set to 0)
         - max_val:                     set max val for clipping (eg., for FA maps, set to 1.0)
         
       Output: (in data structure composed of numpy array(s))
         - data, mean, median, std, minn, maxx
         - or all in data structure if result='all'
         - note: len(data)= num vox that the values were extracted from (i.e., [len(a_idx) for a_idx in res.data])
    
       e.g.,
         - res=extract_stats_from_masked_image(img_fname,mask_fname)
    """
    
    from nilearn.image import resample_img
    import nibabel as nb
    import numpy as np
    
    class return_results(object):
        #output results as an object with these values
        def __init__(self,label_val,data,mean,median,std,minn,maxx):
            self.label_val=np.array(label_val)
            self.data=np.array(data)
            self.mean=np.array(mean)
            self.median=np.array(median)
            self.std=np.array(std)
            self.minn=np.array(minn)
            self.maxx=np.array(maxx)
        
        def __str__(self):
            # defines what is returned when print is called on this class
            template_txt="""
            label_val: {label_val}
            len(data): {data_len}
            mean     : {mean}
            median   : {median}
            std      : {std}
            maxx     : {maxx}
            minn     : {minn}
            """
            return template_txt.format(label_val=self.label_val,data_len=len(self.data),mean=self.mean, median=self.median, std=self.std, maxx=self.maxx, minn=self.minn)
    
    d_label_val=[]
    d_data=[]
    d_mean=[]
    d_median=[]
    d_std=[]
    d_min=[]
    d_max=[]
    
    daff=nb.load(img_fname).affine
    d=nb.load(img_fname).get_data()
    #print(daff)

    maff=nb.load(mask_fname).affine       
    
    # see if we need to resample the mask to the img
    if not np.array_equal(np.diagonal(maff),np.diagonal(daff)):
        mask=resample_img(mask_fname,daff,np.shape(d),interpolation='nearest').get_data()
    else:
        mask=nb.load(mask_fname).get_data()
    
    # if we have passed an additional thresholding mask, move to the same space,
    # thresh at the given thresh_val, and remove from our mask
    if thresh_mask_fname is not None:
        thresh_maff=nb.load(thresh_mask_fname).affine 
        if not np.array_equal(np.diagonal(thresh_maff),np.diagonal(daff)):
            thresh_mask=resample_img(thresh_mask_fname,daff,np.shape(d),interpolation='nearest').get_data()
        else:
            thresh_mask=nb.load(thresh_mask_fname).get_data()
        if thresh_type is 'upper':
            mask[thresh_mask>thresh_val]=0 #remove from the mask
        elif thresh_type is 'lower':
            mask[thresh_mask<thresh_val]=0 #remove from the mask
        else:
            print("set a valid thresh_type: 'upper' or 'lower'")
            return
        
    if label_subset is None:
        mask_ids=np.unique(mask)
        #print(mask)
        if SKIP_ZERO_LABEL:
            mask_ids=mask_ids[mask_ids!=0]
    else: #if we selected some label subsets then we should use them here
        mask_ids=label_subset
    
    if len(mask_ids)==1: #if we only have one, we need to make it iterable
        mask_ids=[mask_ids]
    if erode_vox is not None: #we can also erode each individual mask to get rid of some partial voluming issues (does no erosion if mask vox count falls to 0)
        single_mask=np.zeros_like(mask)
        for mask_id in mask_ids:
            single_mask[mask==mask_id]=1
            temp_mask=np.copy(single_mask)
            single_mask=erode_mask(single_mask,erode_vox)
            temp_mask[np.logical_and(mask==mask_id,single_mask==0)]=0 #to check how many vox's we will have left over
            if np.sum(temp_mask) > 0: #if we know that there is still at least one mask voxel leftover... we use the erosion
                mask[np.logical_and(mask==mask_id,single_mask==0)]=0
            else:
                print("Label id: " +str(mask_id) + ': Not enough voxels to erode!') #This intelligence has also been added to erode_mask, but leaving it explicit here
            single_mask=single_mask*0 #clear the single mask
        del single_mask

    if combined_mask_output_fname is not None:
        niiSave(combined_mask_output_fname,mask,daff,data_type='uint16')

    if VERBOSE:
        print("Mask index extraction: "),

    for mask_id in mask_ids:
        if VERBOSE:
            print(mask_id),            
        dx=np.ma.masked_array(d,np.ma.make_mask(np.logical_not(mask==mask_id))).compressed()
        #print(len(dx))
        if nonzero_stats:
            dx=dx[dx>0]
        if not max_val is None:
            dx[dx>max_val]=max_val
        if not min_val is None:
            dx[dx<min_val]=min_val
        
        #keep track of these as we loop, convert to structure later on
        d_label_val.append(mask_id)
        d_data.append(dx)
        d_mean.append(np.mean(dx))
        d_median.append(np.median(dx))
        d_std.append(np.std(dx))
        d_min.append(np.min(dx))
        d_max.append(np.max(dx))
    if VERBOSE:
        print("")
    results=return_results(d_label_val,d_data,d_mean,d_median,d_std,d_min,d_max)
    
    if result=='all':
        return results
    elif result=='data':
        return results.data
    elif result=='mean':
        return results.mean
    elif result=='median':
        return results.median
    elif result=='std':
        return results.std
    elif result=='min':
        return results.minn
    elif result=='max':
        return results.maxx

def extract_quantitative_metric(metric_files,label_files,label_df=None,label_subset_idx=None,label_tag="label_",metric='mean',\
                                thresh_mask_files=None,thresh_val=0.35,max_val=1,thresh_type='upper',erode_vox=None,zfill_num=3,\
                                DEBUG_DIR=None,VERBOSE=False):
    """
    Extracts voxel-wise data for given set of matched label_files and metric files. Returns pandas dataframe of results
    CAREFUL: IDs are currently defined as the last directory of the input metric_files element
    INPUT:
        - metric_files      - list of files for the metric that you are extracting
        - label_files       - list of label files matched to each file in metric_files (currently restricted to ID at the beginning of file name ==> ID_*)
        - label_df          - pandas dataframe of label index (index) and description (label_id)
        - label_subset_idx  - list of label indices that you want to extract data from [10, 200, 30]
        - label_tag         - string that will precede the label description in the column header
        - metric            - metric to extract {'mean','median','vox_count'}
        - thresh_mask_files - list of files for additional thresholding (again, same restrictions as label_files)
        - thresh_val        - value for threshoding
        - max_val           - maximum value for the metric (i.e., if FA, set to 1)
        - thresh_type       - {'upper' = > thresh_val = 0,'lower' < thresh_val = 0}
        - erode_vox         - number of voxels to erode mask by (simple binary erosion, None for no erosion)
        - zfill_num         - number of zeros to fill to make label index numbers line up properly
        - DEBUG_DIR         - directory to dump new thresholded and interpolated label files to
    OUTPUT:
        - df_4d             - pandas dataframe of results
    """
    
    import os
    import numpy as np
    import pandas as pd    
    
    cols=['ID','metric_file','label_file','thresh_file','thresh_val'] #used to link it to the other measures and to confirm that the masks were used in the correct order so that the values are correct  
    
    if label_subset_idx is None: #you didn't define your label indices, so we go get them for you from the 1st label file
        print("label_subset_idx was not defined")
        print("Label numbers were extracted from the first label file")
        print("label_id = 0 was removed")
        import nibabel as nb
        label_subset_idx=np.unique(nb.load(label_files[0]).get_data())
        label_subset_idx=label_subset_idx[label_subset_idx!=0]
    
    if label_df is None: #WHAT? you didn't provide a label to idx matching dataframe??
        print("label_df dataframe (label index to name mapping) was not defined")
        print("Generic label names will be calculated from the unique values in the first label file")
        for idx,label_id in enumerate(label_subset_idx):
            col_name=label_tag + str(label_id).zfill(zfill_num) + "_" + metric
            cols.append(col_name)
        df_4d=pd.DataFrame(columns=cols)
    else:  
        for idx,label_id in enumerate(label_subset_idx):
            col_name=label_tag + str(label_id).zfill(zfill_num) + "_" + label_df.loc[label_id].Label + "_" + metric
            cols.append(col_name)
        df_4d=pd.DataFrame(columns=cols)
    
    if DEBUG_DIR is not None:
        create_dir(DEBUG_DIR) #this is where the combined_mask_output is going to go so that we can check to see what we actually did to our masks
    for idx, a_file in enumerate(metric_files):
        DATA_EXISTS=True
        #grab the correct label file to go with this img data file
        
        ## XXX START THESE CHECKS COULD BE REMOVED ????
        # XXX making assumptions about how the files are named/stored that will not hold for other datasets :-/
        # by passing a list of IDs as well...?
        ID=os.path.basename(os.path.dirname(a_file)) #first get the ID, since you know how things are stored... :-/
        if VERBOSE:
            print(ID)
        else:
            print(ID),
        label_file=[s for s in label_files if ID in s] #make sure our label file is in the list that was passed
        if len(label_file)>1:
            print "OH SHIT, too many label files. This should not happen!"
            
        elif len(label_file)==0:
            print "OH SHIT, no matching label file"
            DATA_EXISTS=False
        
        if thresh_mask_files is not None:
            thresh_mask_fname=[s for s in thresh_mask_files if ID in s] #make sure our label file is in the list that was passed
            if len(thresh_mask_fname)>1:
                print "OH SHIT, too many threshold mask files. This should not happen!"
                
            elif len(thresh_mask_fname)==0:
                print "OH SHIT, no matching threshold mask file"
                DATA_EXISTS=False
        else:
            thresh_mask_fname=None
        #
        ## STOP THESE CHECKS COULD BE REMOVED
        
        if DATA_EXISTS:
            try:
                if DEBUG_DIR is not None:
                    combined_mask_output_fname=os.path.join(DEBUG_DIR,ID+"_corrected_labels.nii.gz")
                else:
                    combined_mask_output_fname=None
                
                label_file=label_file[0]
                thresh_mask_fname=thresh_mask_fname[0]
                if VERBOSE:
                    print(" metric    : " + a_file)
                    print(" label     : " + label_file)
                    print(" thresh    : " + str(thresh_mask_fname))
                    print(" thresh_val: " + str(thresh_val))
                    print(""),
                res=extract_stats_from_masked_image(a_file,label_file,thresh_mask_fname=thresh_mask_fname,\
                    combined_mask_output_fname=combined_mask_output_fname,thresh_val=thresh_val,thresh_type=thresh_type,\
                    label_subset=label_subset_idx,erode_vox=erode_vox,result='all',max_val=max_val,VERBOSE=VERBOSE)
                #now put the data into the rows:
                df_4d.loc[idx,'ID']=int(ID)
                df_4d.loc[idx,'metric_file']=a_file #this is probably not necessary, since it should always be the same
                df_4d.loc[idx,'label_file']=label_file #this is overkill, since it should always be the same
                df_4d.loc[idx,'thresh_file']=thresh_mask_fname #this is overkill, since it should always be the same
                df_4d.loc[idx,'thresh_val']=thresh_val #this is overkill, since it should always be the same
                
                if metric is 'mean':
                    df_4d.loc[idx,5::]=res.mean
                elif metric is 'median':
                    df_4d.loc[idx,5::]=res.median
                elif metric is 'vox_count':
                    df_4d.loc[idx,5::]=[len(a_idx) for a_idx in res.data] #gives num vox
                else:
                    print("Incorrect metric selected.")
                    return
            except:
                print("")
                print("##=====================================================================##")
                print("Darn! There is something wrong with this ID!")
                print("##=====================================================================##")
    print ""
    return df_4d
    

def calc_3D_flux(data,structure=None,distance_method='edt'):
    """
    Calculate the flux of 3d image data, returns flux and distance transform
    - flux calculated as average normal flux per voxel on a sphere 
    - algorithm inspired by Bouix, Siddiqi, Tannenbaum (2005)
    Input:
        - data              - numpy data matrix (binary, 1=foreground)
        - structure         - connectivity structure (generate with ndimage.morphology.generate_binary_structure, default=(3,3))
        - distance_method   - method for distance computation {'edt','fmm'}
    Output:
        - norm_struc_flux   - normalised flux for each voxel
        - data_dist         - distance map
    """
    from scipy import ndimage
    import numpy as np
    
    #distance metric
    if distance_method is 'edt':
        data_dist=ndimage.distance_transform_edt(data).astype('float32')
    elif distance_method is 'fmm':
        import skfmm #scikit-fmm
        data_dist=skfmm.distance(data).astype('float32')
        
    data_grad=np.array(np.gradient(data_dist)).astype('float32')
    data_flux=data_dist*data_grad

    norm_flux=np.sqrt(data_flux[0]**2+data_flux[1]**2+data_flux[2]**2) #calculate the flux (at normal) at each voxel, by its definition in cartesian space

    #flux for each given voxel is represented by looking to its neighbours
    if structure is None:
        structure=ndimage.morphology.generate_binary_structure(3,3)
        structure[1,1,1]=0
    
    norm_struc_flux=np.zeros_like(norm_flux)
    norm_struc_flux=ndimage.convolve(norm_flux,structure) #this is the mean flux in the neighbourhood at the normal for each voxel    
    
    return norm_struc_flux, data_dist

def skeletonise_volume(vol_fname,threshold_type='percentage',threshold_val=0.2,method='edt',CLEANUP=True):
    """
    Take an ROI, threshold it, and create 2d tract skeleton
    requires: fsl {tbss_skeleton,fslmaths}
    output:
        - _skel.nii.gz skeleton file to same directory as input
        - optional _smth intermediate file
    return:
        - full name of skeletonised file
        
    """
    
    import nibabel as nb
    import os
    import numpy as np
    import scipy.ndimage as ndimage
    import subprocess
    
    smth_tail='_smth.nii.gz'
    skel_tail='_skel.nii.gz'
    data_dist_smth_fname=os.path.join(os.path.dirname(vol_fname),os.path.basename(vol_fname).split(".")[0]+smth_tail)
    data_dist_smth_skel_fname=os.path.join(os.path.dirname(vol_fname),os.path.basename(vol_fname).split(".")[0]+skel_tail)
    
    img=nb.load(vol_fname)
    data=img.get_data()
    aff=img.affine

    #thresh
    if threshold_type is 'percentage':
        thresh=np.max(data)*threshold_val
        data[data<thresh]=0
    #binarise
        data[data>=thresh]=1
    elif threshold_type is 'value':
        thresh=threshold_val
        data[data<thresh]=0
    #binarise
        data[data>=thresh]=1
    
    #inversion is not necessary, this distance metric provides +ve vals inside the region id'd with 1s
    #data=1-data #(or data^1)
    
    #distance metric
    if method is 'edt':
        data_dist=ndimage.distance_transform_edt(data).astype('float32')
    elif method is 'fmm':
        import skfmm #scikit-fmm
        data_dist=skfmm.distance(data).astype('float32')
    #smooth
    #filter may need to change depending on input resolution
    data_dist_smth=ndimage.filters.gaussian_filter(data_dist,sigma=1)
    niiSave(data_dist_smth_fname,data_dist_smth,aff)
    
    #skeletonise
    #tbss_skeleton seems to be the most straightforward way to do this...
    # XXX no 3d skeletonisation in python?
    cmd_input=['tbss_skeleton','-i',data_dist_smth_fname,'-o',data_dist_smth_skel_fname]
    subprocess.call(cmd_input)
    #now binarise in place
    cmd_input=['fslmaths',data_dist_smth_skel_fname,'-thr',str(0),'-bin',data_dist_smth_skel_fname,'-odt','char']
    subprocess.call(cmd_input)
    
    if CLEANUP:
        cmd_input=['rm','-f',data_dist_smth_fname]
        subprocess.call(cmd_input)
        
    return data_dist_smth_skel_fname

def submit_via_qsub(template_text=None, code="# NO CODE HAS BEEN ENTERED #",\
                     name='CJS_job',nthreads=8,mem=1.75,outdir='/scratch',\
                     description="Lobule-specific tractography",SUBMIT=True):
    """
    Christopher J Steele
    Convenience function for job submission through qsub
    Creates and then submits (if SUBMIT=True) .sub files to local SGE
    Input:
        - template_text:    correctly formatted qsub template for .format replacement. None=default (str)
        - code:             code that will be executed by the SGE (str)
        - name:             job name        
        - nthreads:         number of threads to request
        - mem:              RAM per thread
        - outdir:           output (and working) directory for .o and .e files
        - description:      description that will be included in header of .sub file
        - SUBMIT:           actually submit the .sub files
        
        default template_text:
        template_text=\\\"""#!/bin/bash
        ## ====================================================================== ##
        ## 2015_09 Chris Steele
        ## {DESCRIPTION}
        ## ====================================================================== ##
        ##
        #$ -N {NAME}	    #set job name
        #$ -pe smp {NTHREADS}	#set number of threads to use
        #$ -l h_vmem={MEM}G	    #this is a per-thread amount of virtual memory, I think...
        #$ -l h_stack=8M 	    #required to allow multiple threads to work correctly
        #$ -V 			        #inherit user env from submitting shell
        #$ -wd {OUTDIR} 	    #set working directory so that .o files end up here (maybe superseded?)
        #$ -o {OUTDIR} 	        #set output directory so that .o files end up here
        #$ -j yes		        #merge .e and .o files into one
        {CODE}
        \\\"""
    """
    import os
    import stat
    import subprocess

    if template_text is None:
        ## define the template and script to create, save, and run qsub files
        ## yes, this is the one that I used...
        template_text="""#!/bin/bash
## ====================================================================== ##
## 2015_09 Chris Steele
## {DESCRIPTION}
## ====================================================================== ##
##
#$ -N {NAME}	    #set job name
#$ -pe smp {NTHREADS}	#set number of threads to use
#$ -l h_vmem={MEM}G	    #this is a per-thread amount of virtual memory, I think...
#$ -l h_stack=8M 	    #required to allow multiple threads to work correctly
#$ -V 			        #inherit user env from submitting shell
#$ -wd {OUTDIR} 	    #set working directory so that .o files end up here (maybe superseded?)
#$ -o {OUTDIR} 	        #set output directory so that .o files end up here
#$ -j yes		        #merge .e and .o files into one

{CODE}
"""
    
    subFullName=os.path.join(outdir,'XXX_'+name+'.sub')
    open(subFullName,'wb').write(template_text.format(NAME=name,NTHREADS=nthreads,MEM=mem,OUTDIR=outdir,\
                                                      DESCRIPTION=description,CODE=code))
    st = os.stat(subFullName)
    os.chmod(subFullName,st.st_mode | stat.S_IEXEC) #make executable
    if SUBMIT:
        subprocess.call(['qsub',subFullName])

def qcheck(user='stechr',delay=5*60):
    """
    Check if que is clear for user at delay intervals (s)
    """
    import time
    import subprocess
    
    print(time.strftime("%Y_%m_%d %H:%M:%S"))
    print "=== start time ===",
    start=time.time()
    print(start)
    try:
        while len(subprocess.check_output(['qstat', '-u', user,'|','grep',user],shell=True))>0:
            print ". ",
            #print(len(subprocess.check_output(['qstat', '-u', 'tachr'],shell=True)))
            time.sleep(delay)
    except:
        pass
    
    print "=== end time ===",
    print(time.time())
    print(time.strftime("%Y_%m_%d %H:%M:%S"))
    duration=time.time()-start
    print("Duration: " + str(duration) + " (s)")

def print_file_array(in_file_array):
    """
    Convenience function to print file names from array to stdout
    """
    import os
    print(os.path.dirname(in_file_array[0]))
    for line in in_file_array:
        print(os.path.basename(line))

def tract_seg3(files,out_basename='',segmentation_index=None, CLOBBER=False, BY_SLICE=False):
    """
    2015_09
    Christopher J Steele
    Winner takes all segmentation of tract density images (.nii/.nii.gz)
    
    Input:
        - files:                list of tract density files for segmentation (with full pathname)
        - out_basename:         basename for output
        - segmentation_index:   option to map default 1-based indexing (where the first input file is label 1)
                                to custom index. Input must be a numpy array of len(files), and map to their order in files
        - CLOBBER:              over-write or not {True,False}
        - BY_SLICE:             perform segmentation slice by slice (in 3rd dimension) to reduce memory requirements
                                (note that this unzips each .nii.gz file once to reduce overhead, and zips when finished)
    """
    # improved version, processes by slice quickly after unzipping the input .gz files
    # will also work on raw .nii files, but will zip them at the end :)
    
    import os
    import numpy as np
    import nibabel as nb
    import subprocess

    print('You have input {num} files for segmentation'.format(num=len(files)))
    print('Your segmentation index is: {seg}'.format(seg=segmentation_index))    
    print_file_array(files)
    print("Output basename: " + out_basename)

    if os.path.dirname(out_basename) == '': #if they didn't bother to set a path, same as input
        out_dir=os.path.dirname(files[0])
    else:
        out_dir=os.path.dirname(out_basename)

    seg_idx_fname = os.path.join(out_dir,out_basename) + '_seg_idx.nii.gz'
    seg_tot_fname = os.path.join(out_dir,out_basename) + '_seg_tot.nii.gz'
    seg_prt_fname = os.path.join(out_dir,out_basename) + '_seg_prt.nii.gz'
    seg_pct_fname = os.path.join(out_dir,out_basename) + '_seg_pct.nii.gz'
    
    if not(os.path.isfile(seg_idx_fname)) or CLOBBER: #if the idx file exists, don't bother doing this again
        if not BY_SLICE:
            data_list = [nb.load(fn).get_data()[...,np.newaxis] for fn in files] #load all of the files
            combined = np.concatenate(data_list, axis=-1) #concatenate all of the input data
                        
            combined = np.concatenate((np.zeros_like(data_list[0]),combined),axis=-1) #add a volume of zeros to padd axis and make calculations work correctly
            print("Data shape (all combined): " + str(np.shape(combined)))
            
            del data_list #remove from memory, hopefully...
            
            ##%% hard segmentation (tract w/ largest number of streamlines in each voxel wins)
            # uses argmax to return the index of the volume that has the largest value (adds 1 to be 1-based)
            hard_seg=combined.argmax(axis=-1) #now we have a 1-based segmentation (largest number in each voxel)
            hard_seg[combined.std(axis=-1) == 0] = 0 #where there is no difference between volumes, this should be the mask, set to 0
            
            
            ##%% create soft segmentation to show strength of the dominant tract in each voxel
            seg_part = np.zeros_like(hard_seg)
            seg_temp = np.zeros_like(hard_seg)
            seg_total = combined.sum(axis=-1)
            
            idx=1
            for seg in files:
                seg_temp = combined[:,:,:,idx] #get value at this voxel for this tract seg (-1 for 0-based index of volumes)
                seg_part[hard_seg==idx] = seg_temp[hard_seg==idx] #1-based index of segmentation
                idx +=1
            
            #recode simple 1-based index into user-defined index
            if segmentation_index is not None:
                #check that we have the correct number of index values
                hard_seg_indexed = np.zeros_like(hard_seg)
                if len(files) == len(segmentation_index):
                    idx=1
                    for seg_val in segmentation_index:
                        hard_seg_indexed[hard_seg==idx]=seg_val
                        idx+=1
                else:
                    print ""
                    print("====== YOU DID NOT ENTER THE CORRECT NUMBER OF VALUES FOR segmentation_index ======")
                    return
                
                np.copyto(hard_seg,hard_seg_indexed)
                del hard_seg_indexed #be free, my memory!
            
            #seg_pct = seg_part/seg_total
            seg_pct = np.where(seg_total > 0, seg_part.astype(np.float32)/seg_total.astype(np.float32),0) #where there is no std (regions with no tracts) return 0, otherwise do the division
            #seg_pct[seg_pct==float('-Inf')] = 999
            
            #convert so that each segmentation goes from above its segmented to number to just below +1
            #.001 added to make sure that segmentations where tracts are 100% do not push into the next segmentation (not necessary depending on how the images are displayed)
            #1st is 1-1.999, 2nd is 2-3.... (though the values should always be above the integer b/c of the segmentation
            #seg_pct=np.add(seg_pct,hard_seg) #add them and subtract a value, now the values are percentages of the segmentations for each number
            
            """
            # XXX This no longer works because we are assigning different index values to our segmentation
            # new way: double them to provide more space, 
            #-1 sets the zero point at one below double the idx
            # add the pct to modulate accordingly
            # now idx 1 goes from 1-2 (0-100%) and 2 from 3-4... 5-6,7-8,9-10
            """
            #seg_pct2=(hard_seg.astype(np.float32)*2-1)+seg_pct
            #seg_pct2[seg_pct2==-1]=0 #remove those -1s in the regions that used to be 0
            
            ##%%save
            aff = nb.load(files[0]).affine
            header = nb.load(files[0]).header
            
            new_nii = nb.Nifti1Image(hard_seg.astype('uint32'), aff, header)
            new_nii.set_data_dtype('uint32')
            new_nii.to_filename(seg_idx_fname)
            
            new_nii = nb.Nifti1Image(seg_total.astype('uint32'), aff, header)
            new_nii.set_data_dtype('uint32')
            new_nii.to_filename(seg_tot_fname)
            
            new_nii = nb.Nifti1Image(seg_part.astype('uint32'), aff, header)
            new_nii.set_data_dtype('uint32')
            new_nii.to_filename(seg_prt_fname)
            
            """
            # this should give us a combined segmentation and % of seg that is from the one that won, but
            # it does not currently work for all cases, so now just reports the percentage winner in each voxel 
            # without any indication of who won the segmentation
            # XXX change to pct2 when it works :)
            """
            new_nii = nb.Nifti1Image(seg_pct, aff, header)
            new_nii.set_data_dtype('float32') #since our base file is where we get the datatype, set explicitly to float here
            new_nii.to_filename(seg_pct_fname)
            
            print("All segmentation files have been written")
                
        else: #we are going to process this for each slice separately to see what our mem usage looks like
            print("Processing images slice by slice to conserve memory")
            
            # first we uncompress all of the data
            for gz_file in files:
                cmd=['gunzip',gz_file]
                subprocess.call(cmd)
            
            files_nii=[fn.strip('.gz') for fn in files]
            files=files_nii
            
            data_shape = nb.load(files[0]).shape
            
            hard_seg_full = np.zeros(data_shape)
            seg_part_full = np.zeros(data_shape)
            seg_total_full = np.zeros(data_shape)
            seg_pct_full = np.zeros_like(hard_seg_full)


            print("Data shape (single image): " + str(data_shape))
            print("Slice: "),
            
            #loop over the last axis
            for slice_idx in np.arange(0,data_shape[-1]):
                print(slice_idx),
                
                data_list = [nb.load(fn).get_data()[:,:,slice_idx,np.newaxis] for fn in files] #load all of the files
                combined = np.concatenate(data_list, axis=-1) #concatenate all of the input data
                combined = np.concatenate((np.zeros_like(data_list[0]),combined),axis=-1) #add a volume of zeros to padd axis and make calculations work correctly
                if np.any(combined): #if all voxels ==0, skip this slice entirely
                    ##%% hard segmentation (tract w/ largest number of streamlines in each voxel wins)
                    # uses argmax to return the index of the volume that has the largest value (adds 1 to be 1-based)
                    hard_seg=combined.argmax(axis=-1) 
                    #now we have a 1-based segmentation (largest number in each voxel), where number corresponds to input file order
                    hard_seg[combined.std(axis=-1) == 0] = 0 #where there is no difference between volumes, this should be the mask, set to 0
                    
                    hard_seg_full[:,:,slice_idx]=hard_seg
                    
                    ##%% create soft segmentation to show strength of the dominant tract in each voxel
                    seg_total_full[:,:,slice_idx]=combined.sum(axis=-1)                
                    
                    # declare empty matrices for this loop for partial and temp for calculating the partial (num of winning seg) file
                    seg_part=np.zeros_like(hard_seg)
                    seg_temp=np.zeros_like(hard_seg)
                    
                    idx=1
                    for seg in files:
                        seg_temp = combined[:,:,idx] #get value at this voxel for this tract seg (-1 for 0-based index of volumes)
                        seg_part[hard_seg==idx] = seg_temp[hard_seg==idx] #1-based index of segmentation
                        idx +=1
                    
                    seg_part_full[:,:,slice_idx]=seg_part
                    
                    #recode simple 1-based index into user-defined index for hard_seg
                    if segmentation_index is not None:
                        #check that we have the correct number of index values
                        hard_seg_indexed = np.zeros_like(hard_seg)
                        if len(files) == len(segmentation_index):
                            idx=1
                            for seg_val in segmentation_index:
                                hard_seg_indexed[hard_seg==idx]=seg_val
                                idx+=1
                        else:
                            print ""
                            print("====== YOU DID NOT ENTER THE CORRECT NUMBER OF VALUES FOR segmentation_index ======")
                            return None
                        
                        np.copyto(hard_seg_full[:,:,slice_idx],hard_seg_indexed)
                        del hard_seg_indexed #be free, my memory!
                    seg_pct_full[:,:,slice_idx]=np.where(seg_total_full[:,:,slice_idx] > 0, seg_part.astype(np.float32)/seg_total_full[:,:,slice_idx].astype(np.float32),0) #where there is no std (regions with no tracts) return 0, otherwise do the division              
          
            ##%%save
            aff = nb.load(files[0]).affine
            header = nb.load(files[0]).header
            
            new_nii = nb.Nifti1Image(hard_seg_full.astype('uint32'), aff, header)
            new_nii.set_data_dtype('uint32')
            new_nii.to_filename(seg_idx_fname)
            
            new_nii = nb.Nifti1Image(seg_total_full.astype('uint32'), aff, header)
            new_nii.set_data_dtype('uint32')
            new_nii.to_filename(seg_tot_fname)
            
            new_nii = nb.Nifti1Image(seg_part_full.astype('uint32'), aff, header)
            new_nii.set_data_dtype('uint32')
            new_nii.to_filename(seg_prt_fname)
            
            """
            # this should give us a combined segmentation and % of seg that is from the one that won, but
            # it does not currently work for all cases, so now just reports the percentage winner in each voxel 
            # without any indication of who won the segmentation
            # XXX change to pct2 when it works :)
            """
            new_nii = nb.Nifti1Image(seg_pct_full, aff, header)
            new_nii.set_data_dtype('float32') #since our base file is where we get the datatype, set explicitly to float here
            new_nii.to_filename(seg_pct_fname)
            
            #lets compress those files back to what they were, so everyone is happy with how much space they take
            for nii_file in files:
                cmd=['gzip',nii_file]
                subprocess.call(cmd)
                
            print("")
            print("All segmentation files have been written")
            #return hard_seg_full, seg_part_full, seg_total_full, seg_pct_full, combined
        print("")
    else:
        print("The index file already exists and I am not going to overwrite it because you didn't tell me to CLOBBER it! (" + seg_idx_fname + ")")

def sanitize_bvals(bvals,target_bvals=[0,1000,2000,3000]):
    """
    Remove small variation in bvals and bring them to their closest target bvals
    """
    for idx,bval in enumerate(bvals):
        bvals[idx]=min(target_bvals, key=lambda x:abs(x-bval))
    return bvals


###OLD  
#def dki_prep_data_bvals_bvecs(data_fname,bvals_file,bvecs_file,bval_max_cutoff=2500,CLOBBER=False):    
#    """
#    Selects only the data and bvals/bvecs that are below the bval_max_cutoff, writes to files in input dir
#    Useful for the dipy version
#    """
#    import os
#    import numpy as np
#    import subprocess
#    
#    bvals=np.loadtxt(bvals_file)
#    bvecs=np.loadtxt(bvecs_file)
#    vol_list=str([i for i,v in enumerate(bvals) if v < bval_max_cutoff]).strip('[]').replace(" ","") #strip the []s and remove spaces
#    out_fname=data_fname.split(".nii")[0] + "_bvals_under" +str(bval_max_cutoff) + ".nii.gz"
#    bvals_fname=bvals_file.split(".")[0]+ "_bvals_under"+str(bval_max_cutoff)
#    bvecs_fname=bvecs_file.split(".")[0]+ "_bvals_under"+str(bval_max_cutoff)
#    
#    if not(os.path.isfile(out_fname)) or CLOBBER:
#        cmd_input=['fslselectvols','-i',data_fname,'-o',out_fname,'--vols='+vol_list]
#        np.savetxt(bvals_fname,bvals[bvals<bval_max_cutoff])
#        np.savetxt(bvecs_fname,bvecs[:,bvals<bval_max_cutoff])
#        #print(cmd_input)
#        subprocess.call(cmd_input)
#    else:
#        print("File exists, not overwriting.")
#    return out_fname, bvals[bvals<bval_max_cutoff], bvecs[:,bvals<bval_max_cutoff]

def dki_dke_prep_data_bvals_bvecs(data_fname,bvals_file,bvecs_file,out_dir=None,bval_max_cutoff=2500,target_bvals=[0,1000,2000,3000],ROTATE_OUTPUT=True,CLOBBER=False,RUN_LOCALLY=False):    
    """
    Selects only the data and bvals/bvecs that are below the bval_max_cutoff, writes to files in input dir
    Automatically sanitizes your bvals for you, you don't get a choice here
    """
    import os
    import numpy as np
    import subprocess
    
    if out_dir is None:
        out_dir=os.path.dirname(data_fname)
        
    bvals=np.loadtxt(bvals_file)
    bvals=sanitize_bvals(bvals,target_bvals=target_bvals)
    bvecs=np.loadtxt(bvecs_file)
    vol_list=str([i for i,v in enumerate(bvals) if v < bval_max_cutoff]).strip('[]').replace(" ","") #strip the []s and remove spaces so that we can have correct format for command line
    bvals_fname=os.path.basename(bvals_file).split(".")[0]+ "_bvals_under"+str(bval_max_cutoff)
    bvals_fname=os.path.join(out_dir,bvals_fname)
    
    fname_list=[] #keeps track of the bval files that we have written, so we can merge them
    bvecs_fnames=[]
    bvals_used=[]
    
    bvals_orig=bvals
    bvecs_orig=bvecs
    cmd_txt=[]
    for bval in target_bvals: #split the file into its bvals, saves, merges, uses .nii
        if bval <= bval_max_cutoff:
            out_fname=os.path.join(out_dir,os.path.basename(data_fname).split(".nii")[0] + "_bval" +str(bval) + ".nii.gz")
            vol_list=str([i for i,v in enumerate(bvals) if v == bval]).strip('[]').replace(" ","")
            cmd_input=['fslselectvols','-i',data_fname,'-o',out_fname,'--vols='+vol_list]
            print ""
            print " ".join(cmd_input)
            cmd_txt.append(cmd_input)
            if not os.path.isfile(out_fname) or CLOBBER:
                if RUN_LOCALLY:
                    subprocess.call(cmd_input)
            if bval==0: #we mean this value if we are working with b=0 file
                cmd_input=['fslmaths',out_fname,'-Tmean',out_fname]
                print " ".join(cmd_input)
                cmd_txt.append(cmd_input)
                if RUN_LOCALLY:
                    subprocess.call(cmd_input) #no CLOBBER check here, since we actually want to overwrite this file
            else: #non-b0 images should have their own bvecs files
                bvecs_fname=os.path.basename(bvecs_file).split(".")[0]+ "_bval" +str(bval)
                bvecs_fname=os.path.join(out_dir,bvecs_fname)
                bvecs=bvecs_orig[:,bvals_orig==bval]
                if ROTATE_OUTPUT:
                    bvecs=bvecs.T
                np.savetxt(bvecs_fname,bvecs,fmt="%5.10f")
                
                bvecs_fnames.append(bvecs_fname)
            bvals_used.append(str(bval))
            fname_list.append(out_fname)
    out_fname=os.path.join(out_dir,os.path.basename(data_fname).split(".nii")[0] + "_dke_bvals_to_" +str(bval_max_cutoff) + ".nii") #fsl only outputs GZ, so the name here is more for the input to the DKE, which only accepts .nii :-(
    cmd_input=['fslmerge','-t',out_fname]
    for fname in fname_list:
        cmd_input=cmd_input + [fname]
    print ""
    print " ".join(cmd_input)
    cmd_txt.append(cmd_input)
    if not os.path.isfile(out_fname) or CLOBBER:
        if RUN_LOCALLY:
            subprocess.call(cmd_input)
    cmd_input=['gunzip',out_fname+'.gz']
    cmd_txt.append(cmd_input)
    if not os.path.isfile(out_fname) or CLOBBER:
        if RUN_LOCALLY:
            subprocess.call(cmd_input)
    return [out_fname,bvals_used,bvecs_fnames,cmd_txt] #all returned as strings XXX COULD ALSO ADD numdirs (per b-value) and vox_dim
    

def run_diffusion_kurtosis_estimator(sub_root_dir, ID, data_fname, bvals_file, bvecs_file, out_dir=None,bval_max_cutoff=2500, template_file='HCP_dke_commandLine_parameters_TEMPLATE.dat',SUBMIT=True,CLOBBER=False):
    """
    Run the command-line diffusion kurtosis estimator
    Input:
        - sub_root_dir  - subject root directory
        - ID            - subject ID (off of root dir) (string)
        - data_fname    - 4d diffusion data (raw)
        - bvals_file    - b-values file
        - bvecs_file    - b-vectors file
        - out_dir       - directory where you want the output to go (full)
        - TEMPLATE      - template file for dke, provided by the group
    dki_dke_prep_data_bvals_bvecs(data_fname='/data/chamal/projects/steele/working/HCP_CB_DWI/source/dwi/100307/data.nii.gz',bvals_file='/data/chamal/projects/steele/working/HCP_CB_DWI/source/dwi/100307/bvals',bvecs_file='/data/chamal/projects/steele/working/HCP_CB_DWI/source/dwi/100307/bvecs',out_dir='/data/chamal/projects/steele/working/HCP_CB_DWI/processing/DKI/100307')
    """
    import os
    import numpy as np
    import nibabel as nb
    
    if out_dir is None:
        out_dir=os.path.join(sub_root_dir,ID)
    
    TEMPLATE=open(template_file).read()
    full_fname=os.path.join(sub_root_dir,ID,data_fname)
    
    #this next part takes some time, since it divides up the diffusion shells writes them to disk (with bvecs)
    fnames = dki_dke_prep_data_bvals_bvecs(data_fname=full_fname,bvals_file=bvals_file,bvecs_file=bvecs_file,out_dir=out_dir,bval_max_cutoff=bval_max_cutoff,CLOBBER=CLOBBER,RUN_LOCALLY=False)
    
    num_diff_dirs=90 # this is also generated below and used to compare it? divide the dirs? in the bvec files?
    sample_bvecs=np.loadtxt(fnames[2][0])
    num_diff_dirs_2=max(np.shape(sample_bvecs))

    if not num_diff_dirs == num_diff_dirs_2:
        print("##=========================================================================##")
        print("Oh damn, things are not going well!")
        print("The number of diffusion directions do not appear to be correct for the HCP")
        print("Be sad. :-( ")
        print("##=========================================================================##")
        return
    dke_data_fname=os.path.basename(fnames[0])
    v=nb.load(full_fname).get_header()['pixdim'][1:4]
    vox_dims=" ".join(map(str,v)) #map to string, then convert to the format that we need
    print(dke_data_fname)
    bvals_used = " ".join(fnames[1]) #list of bvals used
    bvecs_fnames = ", ".join(["'{0}'".format(os.path.basename(fname)) for fname in fnames[2]]) #list of filenames of bvecs

    sub_root_out_dir=out_dir.strip(ID) #because this script is annoying...
    dke_params_dat_fullname=os.path.join(out_dir,"XXX_"+ID+'_DKE_parameters.dat')
    TEMPLATE=TEMPLATE.format(SUB_ROOT_DIR=sub_root_out_dir, ID=ID, DKE_DATA_FNAME=dke_data_fname, BVALS_USED=bvals_used,BVECS_FNAMES=bvecs_fnames, NUM_DIFF_DIRS=num_diff_dirs,VOX_DIMS=vox_dims)
    open(dke_params_dat_fullname,'wb').write(TEMPLATE)
    
    #now start the module for what we need or assume that it is running, and run the script    
    jname="DKE_" + ID + "_CJS"
    code="""module load DKE/2015.10.28\nrun_dke.sh /opt/quarantine/DKE/2015.10.28/build/v717 {PARAMS}
    """.format(PARAMS=dke_params_dat_fullname)
    cmd_txt=fnames[3]
    cmd_txt=[" ".join(cmd) for cmd in cmd_txt] #to create a list of strings instead of list of lists
    code="\n\n".join(cmd_txt)+"\n\n"+code
    print(os.path.join(sub_root_dir,ID))
    #this job requires over 18GB for the HCP data
    submit_via_qsub(code=code,description="Diffusion kurtosis estimation",name=jname,outdir=out_dir,nthreads=6,mem=4.0,SUBMIT=SUBMIT)








