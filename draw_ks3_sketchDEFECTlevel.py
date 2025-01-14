# In[0]: pre setting
import numpy as np
import sys 
import os
pwd = os.environ['PWD'] + '/'
#sys.path.append(os.environ['SCRIPT'])
from class0_functions1 import read_incar
from pymatgen.io.vasp.outputs import BSVasprun, Vasprun, Eigenval
from pathlib import Path
#from class1_read import read_file_values
import matplotlib.pyplot as plt 
import math

SMALLER_SIZE=14
SMALL_SIZE = 15
MEDIUM_SIZE = 18
BIGGER_SIZE = 18

plt.rc('font', size=SMALLER_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=BIGGER_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title


# In[1]: folder setting
if len(sys.argv) < 2:
        print('Error! Enter the name UNIT cell folder, to obtain CBM and VBM. (supercell is not good, because sampling may affect CBM and VBM)')
        print('${WORK1}/wurtzite_00_unit/unit.AEXX0.405\n${WORK5}/wurtzite_01_bulk/aexx0.36\n${WORK4}/diamond_01_unit/primitive_aexx0.25/bs_non-self')
        print('\n Remember to put \nSPECIFYUPDEFECTLEVEL=\nSPECIFYDOWNDEFECTLEVEL=\nSPECIFYUPCBLEVELNUM=\nSPECIFYUPVBLEVELNUM=\nSPECIFYDOWNCBLEVELNUM=\nSPECIFYDOWNVBLEVELNUM=\n and DEFECTTYPE(title) in file DEFECT')
        sys.exit()
f1=Path(sys.argv[1])
f2=Path(pwd)

mydict=read_incar(f2,incar='DEFECT')
defecttype = mydict['DEFECTTYPE']
print('defecttype=%s'%defecttype)

def cbm_vbm(folder):
        folder = Path(folder)
        run = BSVasprun(folder/"vasprun.xml", parse_projected_eigen=True)
        bs = run.get_band_structure(folder/"KPOINTS")
        info1=bs.get_cbm() # there is the kpoint related to CBM
        # {'band_index': defaultdict(<class 'list'>, {<Spin.up: 1>: [192], <Spin.down: -1>: [192]}), 'kpoint_index': [0], 'kpoint': <pymatgen.electronic_structure.bandstructure.Kpoint>, 'energy': 13.286, 'projections': {}}
        info2=bs.get_vbm() # Valence band maximum
        energyCBM=np.round(info1['energy'],4) # keyword: energy
        energyVBM=np.round(info2['energy'],4)
        #print('%senergy=%s'%(['CBM','VBM'][c_v], energy))
        print('perfect cell VBM=%s CBM=%s ' % (energyVBM,energyCBM))
        return energyCBM,energyVBM

def read_C(folder):
        folder = Path(folder)
        with open(str(folder/'freysoldt_correction_ref-bulk/sx2.sh'),'r') as f:
                lines=f.readlines()[0]
        C=float(lines.split('-C')[1].split('> sx2.fc')[0])
        return C

def read_eigenvalues(folder,defectenergyCBM,defectenergyVBM,selected_up,selected_down):
        eigen=Eigenval(folder/'EIGENVAL')
        eigen = eigen.eigenvalues # a dictionary of eigenvalues: {up:(1,Nbands,2), down:(1,Nbands,2)}
        spin_keys = list(eigen.keys()) # Not sure whether it is [up, down] or [down, up]
        spin_up_key = spin_keys[0].up  # '.up' avoids uncertainty: spin_key.up will become up key, spin_key.down will become down key
        spin_down_key = spin_keys[0].down # will give down key
        ksupstates = eigen[spin_up_key][0] # '[0]' makes it from (1,Nbands,2) to (Nbands,2)
        if spin_down_key in spin_keys:
                ksdownstates = eigen[spin_down_key][0]
        else:
                ksdownstates = ksupstates
        #ksdownstates = eigen[spin_down_key][0]
        # calculate spin of the defect
        ksupstatesocc = ksupstates[:,1]
        ksdownstatesocc = ksdownstates[:,1]
        spin = abs(np.sum(ksupstatesocc) - np.sum(ksdownstatesocc)) / 2
        
        # select out the states within the range of VBM and CBM
        graceperiodVBM = 0.1 # Plot only if both spin up and spin down states are above VBM+graceperiod and belove CBM-graceperiod
        graceperiodCBM = 0 # Plot only if both spin up and spin down states are above VBM+graceperiod and belove CBM-graceperiod
        #selected_up = (defectenergyVBM+graceperiodVBM <ksupstates[:,0])*(ksupstates[:,0]<defectenergyCBM-graceperiodCBM) + (defectenergyVBM+graceperiodVBM<ksdownstates[:,0])*(ksdownstates[:,0]<defectenergyCBM-graceperiodCBM)
        ksupstates = ksupstates[ selected_up]
        ksdownstates = ksdownstates [ selected_down]        
        print('Up states to be plotted: \n%s' % ksupstates)
        print('Down states to be plotted: \n%s' % ksdownstates)
        return ksupstates, ksdownstates, spin

def initialized_first_ks(x_dict,initial_mode=2):
        '''
        Initial_mode = 1: apply to case (1) in plot_ks
        Initial_mode = 2: apply to cases (2) in plot_ks

        return: the least number of levels to be plotted degeneratelly
        '''
        if initial_mode == 2:
                return np.max(list(x_dict.keys()))
        elif initial_mode == 1:
                return 1

def plot_panel_ks(ax, spin_states, maxx, maxy, defectenergyVBM, tol=0.5, initial_mode=2, updown=1):
        '''
        plot defect levels of a single panel, either spin up or spin down
        '''
        length = len(spin_states)
        i = 0
        if updown == 1: # spin up
                #x_dict = {1:[[1./6,2./6]], 2:[[1./18.,5./18],[5./18,8./18]]}
                x_dict = {1:[[3./14,4./14]], 2:[[1./14.,2./14],[5./14,6./14]],3:[[1./14,2./14],[3./14,4./14],[5./14,6./14]],4:[[1./48,5./48],[7./48,11./48],[13./48,17./48],[19./48,23./48]],5:[[0/48,4./48],[5./48,9./48],[10./48,14./48],[15./48,19./48],[20./48,24./48]]}
        else: # spin down
                #x_dict = {1:[[11./16,13./16]], 2:[[9./16.,11./16],[13./16,15./16]]}
                x_dict = {1:[[10./14,11./14]], 2:[[8./14.,9./14],[12./14,13./14]],3:[[8./14,9./14],[10./14,11./14],[12./14,13./14]],4:[[25./48,29./48],[31./48,35./48],[37./48,41./48],[43./48,47./48]],5:[[24/48,28./48],[29./48,33./48],[34./48,38./48],[39./48,43./48],[44./48,48./48]]}
        first_ks = initialized_first_ks(x_dict,initial_mode=initial_mode) # is plotting the first several KS levels. Plot levels in order from left to right
        # After plotting the first several, set first_ks=0. The value of first_ks is initialized to be the maximum keyword in x_dict
        while i < length: # still have length-i levels to plot
                ksenergy = spin_states[i,0] #ksenergyocc
                degenerate = max(1,first_ks) # initially first_ks=4, will plot 4 levels degenerately. Later first_ks=0, degenerate will be 1
                for j in range(i+1,length):
                        if math.isclose(spin_states[j,0],ksenergy,abs_tol=tol):
                                degenerate += 1
                if degenerate >= np.max(list(x_dict.keys())):
                        degenerate = min(np.max(list(x_dict.keys())),length-i) 
                xx = np.array(x_dict[degenerate])
                for j in range(degenerate):
                        ksenergy = spin_states[i+j,0]
                        ksenergy = ksenergy - defectenergyVBM
                        yy=np.array([ksenergy, ksenergy])
                        meanx=xx[j].mean()
                        ax.plot(xx[j],yy,'r') # use plot to draw a small segment
                        arrowratio_yposition=60
                        arrowratio_length=40
                        arrowratio_head_width=40
                        arrowratio_head_length=30
                        if spin_states[i+j,1] == 1: # occupied inside gap, draw arrow and write energy
                                if updown == 1:
                                        plt.text(xx[j,0],ksenergy+maxy/20, '%.2f'%ksenergy)
                                        ax.arrow(meanx,ksenergy-maxy/arrowratio_yposition,0,maxy/arrowratio_length,head_width=maxx/arrowratio_head_width,head_length=maxy/arrowratio_head_length,color='k')
                                else:
                                        plt.text(xx[j,0],ksenergy+maxy/30, '%.2f'%ksenergy)
                                        ax.arrow(meanx,ksenergy+maxy/arrowratio_yposition,0,-maxy/arrowratio_length,head_width=maxx/arrowratio_head_width,head_length=maxy/arrowratio_head_length,color='k')
                        elif spin_states[i+j,1] == 0: # unccupied inside gap, write energy , don't draw arrow
                                plt.text(xx[j,0],ksenergy+maxy/100, '%.2f'%ksenergy)
                        elif spin_states[i+j,1] == 10: # inside VB, don't write energy, only draw arrows
                                if updown == 1:
                                        ax.arrow(meanx,ksenergy-maxy/arrowratio_yposition,0,maxy/arrowratio_length,head_width=maxx/arrowratio_head_width,head_length=maxy/arrowratio_head_length,color='k')
                                else:
                                        ax.arrow(meanx,ksenergy+maxy/arrowratio_yposition,0,-maxy/arrowratio_length,head_width=maxx/arrowratio_head_width,head_length=maxy/arrowratio_head_length,color='k')
                        else: # inside CB, don't write energy, don't draw arrow
                                pass
                i = i+degenerate
                first_ks = 0


def plot_ks(ax,ksupstates,ksdownstates,maxx,maxy, defectenergyVBM,tol=0.5, initial_mode=2):
        '''
        (1) If energy difference is within some tolerance, they will be considered 'degenerate' and will be plotted horizontally
        (2) If the levels are only a few, should plot them in order from left to right regardless of how far their energies are
                Practically, only plot degenerally the first few levels. After the initial plotting, this plotting method is turned off.
        Choose (1) or (2) by initial_mode. See the comments in function initialized_first_ks
        '''
        plot_panel_ks(ax, ksupstates, maxx, maxy, defectenergyVBM, tol=0.5, initial_mode=initial_mode, updown=1)
        plot_panel_ks(ax, ksdownstates, maxx, maxy, defectenergyVBM, tol=0.5, initial_mode=initial_mode, updown=0)

def add_unspecified_states(ksstates,addcb,addvb,unspecifiedenergyCB,unspecifiedenergyVB):
        for i in range(addvb):
                ksstates = np.insert(ksstates,0,[[unspecifiedenergyVB,10]],axis=0)
        for i in range(addcb):
                ksstates = np.append(ksstates,[[unspecifiedenergyCB,-10]],axis=0)
        return ksstates

# energy of CBM and VBM in perfect supercells
perfenergyCBM,perfenergyVBM = cbm_vbm(f1)
# calculate VBM of defect cell by potential alignment
C=read_C(f2) # defect minus perfect
# calculate CBM of defect cell by averaging
bandgap = perfenergyCBM-perfenergyVBM
defectenergyVBM = C+perfenergyVBM
defectenergyCBM = defectenergyVBM + bandgap
print('In defect, VBM=%s, CBM=%s' % (defectenergyVBM, defectenergyCBM))

# get data: KS states
#ksupstates=np.array([3.2,4.7])
#ksdownstates=np.array([3.2,4.7])
def arraystring2list(string):
        # n-th band to be plotted, -1 to get the index of array
        return np.array(string.split()).astype(int)-1
selected_up = arraystring2list(mydict['SPECIFYUPDEFECTLEVEL'])
selected_down = arraystring2list(mydict['SPECIFYDOWNDEFECTLEVEL'])
upcb=int(mydict['SPECIFYUPCBLEVELNUM'])
upvb=int(mydict['SPECIFYUPVBLEVELNUM'])
downcb=int(mydict['SPECIFYDOWNCBLEVELNUM'])
downvb=int(mydict['SPECIFYDOWNVBLEVELNUM'])
ksupstates, ksdownstates, spin = read_eigenvalues(f2,defectenergyCBM,defectenergyVBM,selected_up,selected_down)


initial_mode=2 # 2 or 1. 2 for fixed number of initialized states, 1 for automatic

# plot setting
cbmregion = 2
vbmregion = 2

ksupstates=add_unspecified_states(ksupstates,upcb,upvb,defectenergyCBM+cbmregion/4,defectenergyVBM-vbmregion/4)
ksdownstates=add_unspecified_states(ksdownstates,downcb,downvb,defectenergyCBM+cbmregion/4,defectenergyVBM-vbmregion/4)

largestx=1
x=np.linspace(0,largestx,50)
maxy=int(bandgap+cbmregion)
yticks = np.linspace(0, maxy,maxy+1)

# plot states
ax=plt.subplot(111)
ax.fill_between(x,-vbmregion, 0, color='skyblue') #defectenergyCBM,defectenergyCBM+cbmregion)
ax.fill_between(x,bandgap,bandgap+cbmregion,color='skyblue') #'#1f77b4') # defectenergyVBM,defectenergyVBM-vbmregion)
plt.text( largestx/15,-vbmregion+0.6,'VB' )
plt.text( largestx/15, bandgap+vbmregion-1.4,'CB' )
plot_ks(ax,ksupstates,ksdownstates,largestx,bandgap, defectenergyVBM,initial_mode=initial_mode)

# plot setting
plt.axvline(x[-1]/2, color='k',ls='--')
ax.set_title('%s spin S=%s'%(defecttype, np.round(spin,2)))
ax.set_xlim([min(x), max(x)])
ax.set_ylim([-vbmregion, bandgap+cbmregion])
#ax.set_xlabel()
ax.set_ylabel('Energy [eV]')
ax.get_xaxis().set_visible(False)
ax.spines['left'].set_linewidth(3)
ax.spines['right'].set_linewidth(3)
ax.spines['top'].set_linewidth(3)
ax.spines['bottom'].set_linewidth(3)
#ax.set_xticks() # list of floats
ax.set_yticks(yticks)
#ax2=ax.twinx()
#ax2.set_yticks(yticks)


# save plot
#plt.show()
figname = '%s_ks_states.pdf' % (defecttype[1:len(defecttype)-1]).replace('\mathit','').replace('\mathrm','').replace('}','').replace('{','')
plt.tight_layout()
plt.savefig(figname,dpi=600)
print('%s is generated' % (figname))
