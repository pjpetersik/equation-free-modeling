# -*- coding: utf-8 -*-
"""
Module for equation-free analysis

Delta macro und Delta parameter (like implemented now it leads to dividing by 0 close to convergence point!), error for implicit method

@author: Paul Petersik
"""
import traffic_model as tm
from types import NoneType, ListType
import numpy as np
import warnings
import gc
import pandas as pd
import os

gc.collect()
outpath = "plots/"

# =============================================================================
# =============================================================================
# # State Object
# =============================================================================
# =============================================================================
class stateObject(object):
    """
    Holds the values for the micro, macro or parameter state of a equation-free 
    model. The state values can be hold for 2 purposes.
        1. As a reference
        2. As a temporary output
    """
    def __init__(self,category,purpose,data=None):
        assert category in ("micro","macro","parameters")
        assert purpose in ("tmp","ref")
        assert type(data) in (NoneType,dict)
        
        self.__category = category
        self.__purpose = purpose
        
        if type(data) is dict:
            self.__data = data
        elif type(data) is NoneType:
            self.__data = {}
    
    def __setitem__(self,key,value):
        self.__data[key] = value
    
    def __getitem__(self,key):
        return self.__data[key]
    
    @property
    def variableDict(self):
        return self.__data
    
    @variableDict.setter
    def variableDict(self,dataDict):
        assert type(dataDict) is dict
        self.__data = dataDict
    
    @property
    def category(self):
        return self.__category
    
    @property
    def purpose(self):
        return self.__purpose
    
    def save(self,index=None):
        outputFolder = self.purpose
        if self.purpose =="tmp":
            assert index!=NoneType          
            outputFile = self.category + str(index)+".npy"
           
        elif self.purpose =="ref":
            outputFile = self.category +".npy"  
        outputPath = os.path.join(outputFolder,outputFile)
        
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)
        
        np.save(outputPath,self.__data)
    
    def load(self,index=None):
        inputFolder = self.purpose
        if self.purpose =="tmp":
            assert index!=NoneType          
            inputFile = self.category + str(index)+".npy"
           
        elif self.purpose =="ref":
            inputFile = self.category +".npy"
        
        inputPath = os.path.join(inputFolder,inputFile)
        
        inputDict = np.load(inputPath).item()
        for key in inputDict.keys():
            self.__data[key] = inputDict[key]
                
# =============================================================================
# =============================================================================
# # Equation-free model        
# =============================================================================
# =============================================================================
        
class eqfm(object): 
    def __init__(self,micro_model,micro_model_parameters,initial_micro_state,initial_macro_state):
        """
        The class equation free method 
        
        """
        assert type(micro_model_parameters) is dict
        assert type(initial_micro_state) is dict
        assert type(initial_macro_state) is dict
        
        self.__ParameterState = stateObject("parameters","tmp",data = micro_model_parameters)
        self.__MicroState = stateObject("micro","tmp",data = initial_micro_state)
        self.__MacroState = stateObject("macro","tmp",data = initial_macro_state)
        
        # generate a variable that points to the variable dictionary of the state object
        self.__micro_model_parameters = self.__ParameterState.variableDict
        self.__micro_state = self.__MicroState.variableDict
        self.__macro_state = self.__MacroState.variableDict
        
        self.micro_model = micro_model(self.micro_model_parameters)
        
        self.__RefParameterState = stateObject("parameters","ref")
        self.__RefMicroState = stateObject("micro","ref")
        self.__RefMacroState = stateObject("macro","ref")
        
        self.__ref_micro_model_parameters = self.__RefParameterState.variableDict
        self.__ref_micro_state = self.__RefMicroState.variableDict
        self.__ref_macro_state = self.__RefMacroState.variableDict

# =============================================================================
# temporary states            
# =============================================================================
    @property
    def micro_state(self):
        return self.__micro_state
    
    @micro_state.setter
    def micro_state(self,new_micro_state):
        for key in new_micro_state.keys():
            self.__micro_state[key] = new_micro_state[key]
    
    @property
    def macro_state(self):
        return self.__macro_state
    
    @macro_state.setter
    def macro_state(self,new_macro_state):
        for key in new_macro_state.keys():
            self.__macro_state[key] = new_macro_state[key]
    
    @property
    def micro_model_parameters(self):
        return self.__micro_model_parameters
    
    @micro_model_parameters.setter
    def micro_model_parameters(self,new_micro_model_parameter):
        for key in new_micro_model_parameter.keys():
            self.__micro_model_parameters[key] = new_micro_model_parameter[key]
# =============================================================================
# reference states
# =============================================================================
    @property
    def ref_micro_state(self):
        return self.__ref_micro_state
    
    @ref_micro_state.setter
    def ref_micro_state(self,new_micro_state):
        for key in new_micro_state.keys():
            self.__ref_micro_state[key] = new_micro_state[key]
    
    @property
    def ref_macro_state(self):
        return self.__ref_macro_state
    
    @ref_macro_state.setter
    def ref_macro_state(self,new_macro_state):
        for key in new_macro_state.keys():
            self.__ref_macro_state[key] = new_macro_state[key]
    
    @property
    def ref_micro_model_parameters(self):
        return self.__ref_micro_model_parameters
    
    @ref_micro_model_parameters.setter
    def ref_micro_model_parameters(self,new_micro_model_parameter):
        for key in new_micro_model_parameter.keys():
            self.__ref_micro_model_parameters[key] = new_micro_model_parameter[key]
        
# =============================================================================
# operators
# =============================================================================
    
    def setEqfmOperators(self,lifitng_operator,evolution_operator,restriction_operator):
        """
        Set the three Operators for the equation-free method
        """
        self.evolution_operator = evolution_operator
        self.restriction_operator = restriction_operator
        self.lifting_operator = lifitng_operator
    
    def setEqfmParameters(self,tskip,delta,implicit = False):
        print "Set parameters for the Equation-free method"
        self.delta = delta
        self.tskip = tskip
        self.implicit = implicit
          
    def lift(self,new_macro_state,new_model_parameters=None):
        """ Lift the macroscopic state into a microscopic state
        """
        
        self.micro_state = self.lifting_operator(self,new_macro_state, new_model_parameters)
        self.macro_state = self.restriction_operator(self,self.micro_state)
    
    def evolve(self,integration_time):
        """ Evolve the microscopic state
        """
        self.micro_state = self.evolution_operator(self,integration_time)
    
    def restrict(self):
        """ Restrict the microscopic state. Hence, get the corresponding macroscopic state
        """
        self.macro_state = self.restriction_operator(self,self.micro_state)

# =============================================================================
# Reference state methods        
# =============================================================================
    
    def compute_reference(self,integration_time):
        """ Compute a reference microscopic state
        """
        print "compute reference"
        self.ref_micro_model_parameters = self.micro_model_parameters
        self.ref_micro_state = self.evolution_operator(self,integration_time,reference=True)
        self.ref_macro_state = self.restriction_operator(self,self.ref_micro_state)
        
        return self.ref_macro_state
    
    def save_reference(self):
        """
        Save fixed points to a NPY file
        """
        print "save reference"
        assert id(self.__RefParameterState.variableDict) == id(self.ref_micro_model_parameters)
        assert id(self.__RefMicroState.variableDict) == id(self.ref_micro_state)
        assert id(self.__RefMacroState.variableDict) == id(self.ref_macro_state)
        
        self.__RefParameterState.save()
        self.__RefMicroState.save()
        self.__RefMacroState.save()
        
    def load_reference(self):
        
        self.__RefParameterState.load()
        self.__RefMicroState.load()
        self.__RefMacroState.load()
        
# =============================================================================
# EQFM Methods
# =============================================================================
    def explicit_time_stepper(self,macro_state_init):
        """
        compute time stepper explicitly
        """
        self.lift(macro_state_init)
        self.evolve(self.tskip)
        self.restrict()
        macro_state_tksip = self.macro_state.copy()
        
        self.evolve(self.delta)
        self.restrict()
        macro_state_tksip_plus_delta = self.macro_state.copy()
        explicit_macro_time_stepper = {}
            
        for key in self.macro_state.keys():
            explicit_macro_time_stepper[key] = macro_state_tksip_plus_delta[key] - macro_state_tksip[key]  
        
        return macro_state_tksip, macro_state_tksip_plus_delta, explicit_macro_time_stepper
    
    def implicit_time_stepper(self,macro_state_init):
        """
        compute time stepper implicitly
        :param start_macro_state: initial macroscopic state to start evolution of the micro model
        :param target_macro_state: target macroscopic state for which an initial macroscopic state
        should be found 
        """
        self.lift(macro_state_init)
        self.evolve(self.tskip+self.delta)
        self.restrict()
        target_macro_state = self.macro_state.copy()
        
        # first guess for prediction of macroscopic timestepper
        macro_state_delta = target_macro_state.copy()
        macro_state_delta2 = target_macro_state.copy()
        
        error=np.inf
        while abs(error)>self.dmacro:   
            self.lift(macro_state_delta)
            self.evolve(self.tskip)
            self.restrict()
            macro_state_tksip = self.macro_state
        
            error = macro_state_tksip[self.bif_macro_state] - target_macro_state[self.bif_macro_state]
             
            macro_state_delta2[self.bif_macro_state] = macro_state_delta[self.bif_macro_state] + self.dmacro
            
            self.lift(macro_state_delta2)
            self.evolve(self.tskip)
            self.restrict()
            macro_state_tksip2 = self.macro_state

            error2 =  macro_state_tksip2[self.bif_macro_state] - target_macro_state[self.bif_macro_state]
            
            derivative_error = (error2-error) / self.dmacro
                
            macro_state_delta[self.bif_macro_state] = macro_state_delta[self.bif_macro_state]  - error/derivative_error
            
        implicit_macro_time_stepper = {}
        for key in self.macro_state.keys():
            implicit_macro_time_stepper[key] = (macro_state_delta[key] -  macro_state_init[key])
        
        return macro_state_init, macro_state_delta, implicit_macro_time_stepper

    def compute_macro_time_stepper(self,macro_state_init):
        """
        macroscopic timestepper
        """        
        if not self.implicit:
            return self.explicit_time_stepper(macro_state_init)
        
        elif self.implicit:
            return self.implicit_time_stepper(macro_state_init)            
            
    
    def compute_macro_time_derivative(self,macro_time_stepper):
        """
        time derivative of macroscopic state evolution
        """
        return macro_time_stepper[self.bif_macro_state]/self.delta
    
    def projective_integration(self,Delta_t,iterations,macro_state_init = None,implicit=False,dmacro = 0.1, verbose=False):
        """ coarse time stepper using extrapolation of the macropscopic state
        from the microscopic model"""
        self.dmacro = dmacro

        if type(macro_state_init) != NoneType:
            self.macro_state  = macro_state_init
        
        if Delta_t<0 and (self.tskip + Delta_t)>0:
            warnings.warn("backwards integration might be ineffective because tksip>Delta_t",Warning)
        
        for i in range(iterations):
            self.macro_state = self.project_macro_state(self.macro_state,Delta_t,implicit)
            if verbose:
                print self.macro_state 
        
    def project_macro_state(self,macro_state_init,Delta_t,implicit=False):
        """
        projective integration
        """
        macro_state_tksip, macro_state_tksip_plus_delta, macro_time_stepper = self.compute_macro_time_stepper(macro_state_init)
        F = self.compute_macro_time_derivative(macro_time_stepper)
        
        projected_macro_state = {}
        if Delta_t>0:
            for key in self.__macro_state.keys():
                projected_macro_state[key] = macro_state_tksip_plus_delta[key] + Delta_t * F[key]
        
        if Delta_t<0:
            for key in self.__macro_state.keys():
                projected_macro_state[key] = macro_state_tksip[key] + Delta_t * F[key]
        
        return projected_macro_state
    
    def time_derivative(self,macro_state_init,model_parameters):
        """
        Computes F, the time derivative of macroscopic state
        """
        self.micro_model_parameters = model_parameters.copy()
        
        macro_time_stepper = self.compute_macro_time_stepper(macro_state_init)[2]
        F = self.compute_macro_time_derivative(macro_time_stepper)
        return F
        
    def partial_derivatives_F(self, F, macro_state_init, model_parameters):
        """
        Computes partial derivatives of F (the time derivative of macroscopic state)
        """
        # perturbed macro state
        macro_state_pert = macro_state_init.copy()
        macro_state_pert[self.bif_macro_state] = macro_state_init[self.bif_macro_state] + self.dmacro

        macro_time_stepper = self.compute_macro_time_stepper(macro_state_pert)[2]
        Fdmacro = self.compute_macro_time_derivative(macro_time_stepper)
        
        # perturbed model parameters
        self.micro_model_parameters[self.bif_parameter] = self.micro_model_parameters[self.bif_parameter] + self.dparameter 
        
        macro_time_stepper = self.compute_macro_time_stepper(macro_state_init)[2]
        Fdpara = self.compute_macro_time_derivative(macro_time_stepper)
        
        F_macro = (Fdmacro - F) / self.dmacro 
        F_parameter = (Fdpara - F) /self.dparameter
        
        # set back model parameter
        self.micro_model_parameters = model_parameters.copy()
        
        return F_macro, F_parameter
    
    def predictor_step(self,macro_state0,macro_state1,parameter0,parameter1):
        """
        Predictor step for finding a fixed point
        """
        print "predictor step"
        w = np.zeros(2)
        
        w[0] = macro_state1[self.bif_macro_state] - macro_state0[self.bif_macro_state]
        w[1] = parameter1[self.bif_parameter] - parameter0[self.bif_parameter]
        w_norm = w/np.linalg.norm(w)
        
        predicted_macro_state = macro_state1.copy()
        predicted_model_parameter = self.micro_model_parameters.copy()
        
        s_applied = self.s
        
        if type(self.s) == ListType:
            alpha = abs(np.arctan(w_norm[0]/w_norm[1] * self.ref_ratio))
            s_applied = (self.smin - self.smax) * np.sin(alpha) + self.smax
            print "s: " + str(round(s_applied,2))
            
        predicted_macro_state[self.bif_macro_state]  = macro_state1[self.bif_macro_state] + s_applied * w_norm[0]
        predicted_model_parameter[self.bif_parameter] = parameter1[self.bif_parameter] + s_applied * w_norm[1]
        
        return predicted_macro_state, predicted_model_parameter, w
    
    def corrector_step(self,predicted_macro_state,predicted_model_parameters,w):
        """
        corrector step for finding a fixed point
        """
        # time derivative, F, and parital derivatives of F
        F = self.time_derivative(predicted_macro_state, predicted_model_parameters)
        F_macro, F_parameter = self.partial_derivatives_F(F, predicted_macro_state,predicted_model_parameters)
        
        # Jacobian
        J = np.matrix([[F_macro,F_parameter],[w[0],w[1]]])

        # inverse Jacobian
        Jinv = np.linalg.inv(J)

        correct =  Jinv * np.matrix([F,0]).T
        correct, = np.array(correct.T)
        
        corrected_macro_state = predicted_macro_state.copy()
        corrected_model_parameter = predicted_model_parameters.copy()
        
        corrected_macro_state[self.bif_macro_state] = predicted_macro_state[self.bif_macro_state] - self.nu * correct[0]
        corrected_model_parameter[self.bif_parameter] = predicted_model_parameters[self.bif_parameter] - self.nu * correct[1]
                
        return corrected_macro_state, corrected_model_parameter
        
    def bifurcation_analysis(self, bifurcation_parameter, bifurcation_macro_state, n_fixed_points,dmacro = 0.1,dparameter = 0.1, s=1., parameter_direction = 3.,nu=1.,rerun=False,save_for_rerun=True):
        """ 
        :param bifurcation_parameter: Model parameter for the bifurcation analysis
        :param bifurcation_macro_state: Macroscopic state in which the bifurcation analysis should be performed
        :param n_fixed_points: Number of fixed points to be found
        :param dmacro: finite difference in the macroscopic state for computation of derivatives
        :param dparameter: finite difference in the model parameter for computation of derivatives
        :param s: extrapolation factor for finding predicting the next fixed point
        :param nu: the fraction for which the Newton step in the corrector step is applied (default nu=1 is a full newton step)
        :param rerun: start a bifurcation analysis with saved reference  and beginning  at the last saved fixed point
            
        :type bifurcation_parameter: string
        :type bifurcation_macro_state: string
        :type n:fixed_points: int
        :type dmacro: float
        :type dparameter: float
        :type s: float
        :type nu: float
        :type rerun: bool
        """
        self.bif_parameter = bifurcation_parameter
        self.bif_macro_state = bifurcation_macro_state
        self.n_fixed_points = n_fixed_points
        self.dmacro = dmacro
        self.dparameter = dparameter
        self.nu = nu
        self.s = s
        
        if type(s)==ListType and len(s)==2:
            self.smin = s[0]
            self.smax = s[1]
        
        parameter0 = self.micro_model_parameters.copy()
        parameter1 = self.micro_model_parameters.copy()
        parameter1[self.bif_parameter] += parameter_direction

        self.fixed_points = {}
        self.fixed_points[self.bif_parameter] = np.zeros(n_fixed_points)
        self.fixed_points[self.bif_parameter][:] = np.nan
        self.fixed_points[self.bif_macro_state] = np.zeros(n_fixed_points)
        self.fixed_points[self.bif_macro_state][:] = np.nan
        
        i_start = 0
        if rerun:
            print "LOAD FIXED POINTS FOR RERUN"
            self.load_reference()
            self.load_fixed_points()
            
            i_last = np.max(np.argwhere(np.isfinite(self.fixed_points[self.bif_macro_state])))
            i_start = i_last + 1
            if i_last>0:
                self.__MacroState.load(index=i_last-1)
                macro_state0 = self.macro_state.copy()
                
                self.__MacroState.load(index=i_last)
                macro_state1 = self.macro_state.copy()
                
                self.__ParameterState.load(index=i_last-1)
                parameter0 = self.micro_model_parameters.copy()
                
                self.__ParameterState.load(index=i_last)
                parameter1 = self.micro_model_parameters.copy()
                
            else:
                 warnings.warn("No enough fixed point found. Start bifurcation analysis from reference state",Warning)
        else:
            print "======COMPUTE 1ST STARTING FIXED POINT ============"
            macro_state0 = self.compute_reference(50)
            self._print_bif_state(macro_state0,self.micro_model_parameters)
            
            print "======COMPUTE 2ND STARTING FIXED POINT ============"
            self.micro_model_parameters = parameter1
            macro_state1 = self.compute_reference(50)
            self._print_bif_state(macro_state1,self.micro_model_parameters)
            
            self.save_reference()
        
        # get ratio between reference macro state variable and model parameter
        self.ref_ratio = self.ref_micro_model_parameters[self.bif_parameter]/self.ref_macro_state[self.bif_macro_state]
        
        # set parameter back to unperturbed
        self.micro_model_parameters = parameter0.copy()
        
        for i in range(i_start,n_fixed_points):
            print "======FIND FIXED POINT NR. "+str(i) + " ============"
            macro_state_fixed_point, parameter_fixed_point = self.find_fixed_point(macro_state0,macro_state1,parameter0,parameter1)
            
            self.macro_state = macro_state_fixed_point.copy()
            self.micro_model_parameters = parameter_fixed_point.copy()
            
            self.fixed_points[self.bif_macro_state][i] = macro_state_fixed_point[self.bif_macro_state]
            self.fixed_points[self.bif_parameter][i] = parameter_fixed_point[self.bif_parameter]
            
            self._print_bif_state(macro_state_fixed_point,self.micro_model_parameters)
            self.save_fixed_points()
            
            if save_for_rerun:
                self.__MacroState.save(index=i)
                self.__ParameterState.save(index=i)
            
            macro_state0 = macro_state1.copy()
            macro_state1 = macro_state_fixed_point.copy()
            
            parameter0 = parameter1.copy()
            parameter1 = parameter_fixed_point.copy()
        
    def find_fixed_point(self,macro_state0,macro_state1,parameter0,parameter1):
        """
        Find fixed point using a predictor corrector scheme
        
        :param macro_state0, macro_state1: the two previous macro states with 
        macro_state1 the macroscopic state of the last found fixed point
        
        :type macro_state0, macro_state1: dict
        """
        
        # predictor step
        predicted_macro_state, predicted_model_parameter, w = self.predictor_step(macro_state0,macro_state1,parameter0,parameter1)
        
        self._print_bif_state(predicted_macro_state,predicted_model_parameter)
        
        difference = np.inf
        while  difference>0.01:
            corrected_macro_state, corrected_model_parameter = self.corrector_step(predicted_macro_state,predicted_model_parameter,w)
            
            difference = abs(corrected_macro_state[self.bif_macro_state] - predicted_macro_state[self.bif_macro_state])
            print "Difference after correction: " + str(round(difference,2))
            
            predicted_macro_state = corrected_macro_state.copy()
            predicted_macro_state[self.bif_macro_state] = corrected_macro_state[self.bif_macro_state].copy()
            
            predicted_model_parameter = corrected_model_parameter.copy()
            
        return predicted_macro_state, predicted_model_parameter
    
    def save_fixed_points(self):
        """
        Save fixed points to a csv file
        """
        fixed_point_df = pd.DataFrame(data=self.fixed_points)
        fixed_point_df.to_csv("fixed_points.csv")
    
    def load_fixed_points(self):
        fixed_point_df = pd.read_csv("fixed_points.csv")
        
        self.fixed_points[self.bif_macro_state] = fixed_point_df[self.bif_macro_state]
        self.fixed_points[self.bif_parameter] = fixed_point_df[self.bif_parameter]        
    
    def _print_bif_state(self,macro_state,model_parameter):
        """
        print macroscopic state and parameter of the bifurcation macroscopic state and 
        the model parameter
        """
        print "Macroscopic state:"+ str(macro_state[self.bif_macro_state])
        print "Parameter value:"+ str(model_parameter[self.bif_parameter])  
        
        
    @staticmethod
    def state(variable_names,dimension):
        variable_dict = {}
        for i in range(len(variable_names)):
            variable_dict[variable_names[i]] = np.zeros(dimension)
        return variable_dict  