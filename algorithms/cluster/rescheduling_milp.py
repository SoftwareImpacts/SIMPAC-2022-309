# -*- coding: utf-8 -*-
"""
Created on Fri Nov 19 15:24:35 2021

@author: egu
"""

from pyomo.core import *
import pyomo.kernel as pmo

def reschedule(solver,opt_step,opt_horizon,upperlimit,lowerlimit,tolerance,evdata,rho_y,rho_eps):
    """
    This function reschedules the charging operations of a cluster by considering
    1) upper-lower limits of aggregate power consumption of the cluster
    2) pre-defined reference schedules of the individual EVs in the system.
    This is run typically when some events require deviations from previously determined schedules.

    Inputs
    ------------------------------------------------------------------------------------------------------------------
    solver      : optimization solver                                           pyomo SolverFactory object
    opt_step    : size of one time step in the optimization (seconds)           float
    opt_horizon : time step identifiers in the optimization horizon             list of integers
    upperlimit  : soft upper limit of cluster power consumption (kW series)     dict of float
    lowerlimit  : soft lower limit of cluster power consumption (kW series)     dict of float
    tolerance   : maximum allowed violation of oth upper-lower limits (kW)      float
    evdata      : EV demand parameters                                          dict
    rho_y       : penalty factor for deviation of reference schedules           float
    rho_eps     : penalty factor for violation of upper-lower soft limits       float
    ------------------------------------------------------------------------------------------------------------------

    Outputs
    ------------------------------------------------------------------------------------------------------------------
    p_schedule  : timeseries of new charging schedule                           dict
    s_schedule  : timeseries of new reference SOC trajectory                    dict
    ------------------------------------------------------------------------------------------------------------------
    """

    ###########################################################################
    ####################Constructing the optimization model####################
    model = ConcreteModel()
    model.V =Set(initialize=list(evdata['battery_cap'].keys()))  #Index set for the EVs

    #Time parameters
    model.deltaSec=opt_step                                     #Time discretization (Size of one time step in seconds)
    model.T       =Set(initialize=opt_horizon[:-1],ordered=True)#Index set for the time steps in opt horizon
    model.Tp      =Set(initialize=opt_horizon,ordered=True)     #Index set for the time steps in opt horizon for SoC

    #Power capability parameters
    model.P_EV_pos=evdata['P_EV_pos_max']       #Maximum charging power to EV battery
    model.P_EV_neg=evdata['P_EV_neg_max']       #Maximum discharging power from EV battery
    model.P_CC_up =upperlimit                   #Upper limit of the power that can be consumed by a cluster
    model.P_CC_low=lowerlimit                   #Lower limit of the power that can be consumed by a cluster (negative values indicating export limit)
    model.P_CC_vio=tolerance                    #Cluster upper-lower limit violation tolerance

    #Battery and charger parameters
    model.eff_ch  =evdata['charge_eff']         #Charging efficiency
    model.eff_ds  =evdata['discharge_eff']      #Discharging efficiency
    model.E       =evdata['battery_cap']        #Battery capacities
        
    #Demand parameters
    model.s_ini    =evdata['initial_soc']       #SoC when the optimization starts
    model.s_tar    =evdata['target_soc']        #Target SOC
    model.s_min    =evdata['minimum_soc']       #Minimum SOC
    model.s_max    =evdata['maximum_soc']       #Maximum SOC
    model.t_dep    =evdata['departure_time']    #Estimated departure of EVs

    #Penalty parameters
    model.rho_y    =rho_y
    model.rho_eps  =rho_eps
        
    #EV Variables
    model.p_ev    =Var(model.V,model.T,within=Reals)                #Net charging power of EV indexed by
    model.p_ev_pos=Var(model.V,model.T,within=NonNegativeReals)     #Charging power of EV
    model.p_ev_neg=Var(model.V,model.T,within=NonNegativeReals)     #Disharging power of EV
    model.x_ev    =Var(model.V,model.T,within=pmo.Binary)           #Whether EV is charging
    model.s       =Var(model.V,model.Tp,within=NonNegativeReals)    #EV SOC variable
    
    #System variables
    model.p_cc  =Var(model.T,within=Reals)                          #Power flows into the cluster c

    #Deviation
    model.eps   =Var(within=NonNegativeReals)                       #Deviation from aggregate conspumtion limit
    model.y     =Var(model.V,within=NonNegativeReals)               #Deviation from individual schedules

    #CONSTRAINTS
    def initialsoc(model,v):
        return model.s[v,0]==model.s_ini[v]
    model.inisoc=Constraint(model.V,rule=initialsoc)
    
    def minimumsoc(model,v,t):
        return model.s_min[v]<=model.s[v,t]
    model.minsoc_con=Constraint(model.V,model.T,rule=minimumsoc)

    def maximumsoc(model,v,t):
        return model.s_max[v]>=model.s[v,t]
    model.maxsoc_con=Constraint(model.V,model.T,rule=maximumsoc)    
    
    def storageConservation(model,v,t):    #SOC of EV batteries will change with respect to the charged power and battery energy capacity
        return model.s[v,t+1]==(model.s[v,t] + (model.p_ev_pos[v,t]-model.p_ev_neg[v,t])/model.E[v] *model.deltaSec)
    model.socconst=Constraint(model.V,model.T,rule=storageConservation)
    
    def chargepowerlimit(model,v,t):                    #Net power into EV decoupled into positive and negative parts            
        return model.p_ev[v,t]==model.p_ev_pos[v,t]-model.p_ev_neg[v,t]
    model.chrpowconst=Constraint(model.V,model.T,rule=chargepowerlimit)
        
    def combinatorics_ch(model,v,t):                    #EV indexed by v can charge only when x[v,t]==1 at t
        if t>=model.t_dep[v]:
            return model.p_ev_pos[v,t]==0
        else:
            return model.p_ev_pos[v,t]<=model.x_ev[v,t]*model.P_EV_pos[v]
    model.combconst1 =Constraint(model.V,model.T,rule=combinatorics_ch)
    
    def combinatorics_ds(model,v,t):                    #EV indexed by v can discharge only when x[v,t]==0 at t
        if t>=model.t_dep[v]:
            return model.p_ev_neg[v,t]==0
        else:        
            return model.p_ev_neg[v,t]<=(1-model.x_ev[v,t])*model.P_EV_neg[v]
    model.combconst2 =Constraint(model.V,model.T,rule=combinatorics_ds)    
            
    def ccpower(model,t):                             #Mapping EV powers to CC power
        return model.p_cc[t]==sum(model.p_ev_pos[v,t]/model.eff_ch[v]-model.p_ev_neg[v,t]*model.eff_ds[v] for v in model.V)
    model.ccpowtotal=Constraint(model.T,rule=ccpower)

    def cluster_limit_violation(model):
        return model.eps<=model.P_CC_vio
    model.viol_clust   =Constraint(rule=cluster_limit_violation)

    def cluster_upper_limit(model,t):           #Upper limit of aggregate power consumption
        return model.p_cc[t]<=model.eps+model.P_CC_up[t]
    model.ccpowcap_pos =Constraint(model.T,rule=cluster_upper_limit)
    
    def cluster_lower_limit(model,t):           #Lower limit of aggregate power consumption
        return -model.eps+model.P_CC_low[t]<=model.p_cc[t]
    model.ccpowcap_neg =Constraint(model.T,rule=cluster_lower_limit)

    def individual_pos_deviation(model,v):
        return model.s_tar[v]-model.s[v,max(opt_horizon)]<=model.y[v]
    model.indev_pos=Constraint(model.V,rule=individual_pos_deviation)

    def individual_neg_deviation(model,v):
        return -model.y[v]<=model.s_tar[v]-model.s[v,max(opt_horizon)]
    model.indev_neg=Constraint(model.V,rule=individual_neg_deviation)

    def obj_rule(model):
        return model.rho_y*(sum(model.y[v]*model.E[v]/3600 for v in model.V))+model.rho_eps*model.eps

    #OBJECTIVE FUNCTION
    """
    def obj_rule(model):  
        return model.rho_y*\
               sum((model.s_ref[v]-model.s[v,max(horizon)])*
                   (model.s_ref[v]-model.s[v,max(horizon)]) 
                   for v in model.V)\
               +model.rho_eps*model.eps
    """
    model.obj=Objective(rule=obj_rule, sense = minimize)
    
    ###########################################################################         
     
    ###########################################################################
    ######################Solving the optimization model ######################            
    result=solver.solve(model)
    ###########################################################################
    
    ###########################################################################
    ################################Saving the results#########################      
    p_schedule={}
    s_schedule={}
    for v in model.V:
        p_schedule[v]={}
        s_schedule[v]={}
        for t in opt_horizon:
            if t<max(opt_horizon):
                p_schedule[v][t]=model.p_ev[v,t]()
            s_schedule[v][t]=model.s[v,t]()
	###########################################################################
            
    return p_schedule,s_schedule

if __name__ == '__main__':

    import pandas as pd
    import numpy as np
    from pyomo.environ import SolverFactory

    PCU     = 11
    ch_eff  = 1.0
    ds_eff  = 1.0
    N       = 4
    PPL     = 0.5
    CAP     = 55 * 3600
    PC      = PPL * N * PCU
    nb_of_ts=12

    solver     = SolverFactory("cplex")
    opt_step   = 300
    opt_horizon= list(range(nb_of_ts+1))
    upperlimit = dict(enumerate(np.ones(nb_of_ts) * PC))# The cluster is allowed to import half as the installed capacity
    lowerlimit = dict(enumerate(np.zeros(nb_of_ts)))    # The cluster is not allowed to export
    tolerance  = 0

    np.random.seed(0)
    evdata = {}
    evdata['P_EV_pos_max'] = {}
    evdata['P_EV_neg_max'] = {}
    evdata['charge_eff'] = {}
    evdata['discharge_eff'] = {}
    evdata['battery_cap'] = {}
    evdata['target_soc'] = {}
    evdata['departure_time'] = {}
    evdata['initial_soc'] = {}
    evdata['minimum_soc'] = {}
    evdata['maximum_soc'] = {}
    for n in range(1,N+1):
        evid='EV'+str(n)
        evdata['P_EV_pos_max'][evid]   = PCU
        evdata['P_EV_neg_max'][evid]   = PCU
        evdata['charge_eff'][evid]     = ch_eff
        evdata['discharge_eff'][evid]  = ds_eff
        evdata['battery_cap'][evid]    = CAP
        evdata['initial_soc'][evid]    = np.random.uniform(low=0.4, high=0.8)
        evdata['target_soc'][evid]     = evdata['initial_soc'][evid] + PCU*opt_step*int(nb_of_ts/2)/CAP
        evdata['minimum_soc'][evid]    = 0.2
        evdata['maximum_soc'][evid]    = 1.0
        evdata['departure_time'][evid] = np.random.randint(low=int(nb_of_ts/2),high=int(nb_of_ts*1.5))

    rho_y       =1
    rho_eps     =1


    print("The cluster with total installed capacity of:",N * PCU)
    print()
    print("...has a power limit of:")
    limit_data=pd.DataFrame(columns=['Upper Limit','Lower Limit','Violation Tolerance'])
    limit_data['Upper Limit']=pd.Series(upperlimit)
    limit_data['Lower Limit'] = pd.Series(lowerlimit)
    limit_data.loc[:,'Violation Tolerance'] = tolerance
    print(limit_data)
    print()


    print("...optimizing the charging profiles of the EVs with charging demands:")
    demand_data=pd.DataFrame(columns=['Battery Capacity','Initial SOC','Target SOC','Estimated Departure'])
    demand_data['Battery Capacity']= pd.Series(evdata['battery_cap'])/3600
    demand_data['Initial SOC']     = pd.Series(evdata['initial_soc'])
    demand_data['Target SOC']      = pd.Series(evdata['target_soc'])
    demand_data['Estimated Departure']=pd.Series(evdata['departure_time'])
    print(demand_data)
    print()


    print("Optimized charging profiles:")
    p_ref, s_ref = reschedule(solver,opt_step,opt_horizon,upperlimit,lowerlimit,tolerance,evdata,rho_y,rho_eps)

    results={}
    for v in demand_data.index:
        results[v]=pd.DataFrame(columns=['P','S'],index=sorted(s_ref[v].keys()))
        results[v]['P']=pd.Series(p_ref[v])
        results[v]['S']=pd.Series(s_ref[v])
    print(pd.concat(results,axis=1))

