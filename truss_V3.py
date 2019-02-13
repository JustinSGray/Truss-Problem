import numpy as np 
from openmdao.api import ExplicitComponent, ImplicitComponent, Problem, Group, IndepVarComp, ExecComp, NonlinearBlockGS, NewtonSolver, DirectSolver, ScipyOptimizeDriver

class Beam(ImplicitComponent):

    def setup(self):
        
        self.add_input("force0", val = 1., units = "N", desc = "Force on 0th end of beam")
        self.add_input("force1", val = 1., units = "N", desc = "Force on 1st end of beam")
        self.add_input("A", val = 1., units = "m**2", desc = "Cross sectional area of the beam")
        self.add_output("beam_force", val = 1., units = "N", desc = "Force in the beam")

        self.add_output('sigma', val=1, units='MPa')

        self.declare_partials("beam_force", "force*")
        self.declare_partials("sigma", "beam_force")
        self.declare_partials("sigma", "sigma")
        self.declare_partials("sigma", "A")

    def apply_nonlinear(self, inputs, outputs, residuals):
        residuals["beam_force"] = 0
        residuals["beam_force"] += inputs["force0"]
        residuals["beam_force"] -= inputs["force1"]
        residuals['sigma'] = outputs['sigma'] - outputs['beam_force']/(1e6*inputs['A'])

    def solve_nonlinear(self, inputs, outputs):
        outputs['sigma'] =  outputs['beam_force']/(1e6*inputs['A'])

    def linearize(self, inputs, outputs, partials):
        partials["beam_force", "force0"] = 1
        partials["beam_force", "force1"] = -1
        partials["sigma", "beam_force"] = -1 / (1e6 * inputs["A"])
        partials["sigma", "sigma"] = 1
        partials["sigma", "A"] = outputs["beam_force"] / (1e6 * (inputs["A"]) ** 2)


class Node(ImplicitComponent):
 
    def initialize(self):
        self.options.declare("n_loads", default = 2, desc = "Number of loads on node")
        self.options.declare("n_external_forces", default = 0, desc = "Number of external forces on node")
        self.options.declare("n_reactions", default = 0, desc = "Number of reactions on node")

    def setup(self):

        for n in range(self.options["n_loads"] + self.options["n_reactions"]):

            n_load_out = "load{}_out".format(n)
            n_direction = "direction{}".format(n)
            self.add_output(n_load_out, units = "N", desc = "Output load on node")
            self.add_input(n_direction, units = "rad", desc = "Direction of load on node")
            
        for n in range(self.options["n_reactions"], (self.options["n_reactions"] + self.options["n_loads"])):
            n_load_in = "load{}_in".format(n)
            self.add_input(n_load_in, units = "N", desc = "Input load on node")

        for m in range(self.options["n_external_forces"]):
            m_force = "force{}_ext".format(m)
            m_direction = "direction{}_ext".format(m)
            self.add_input(m_force, units = "N", desc = "External force on node")
            self.add_input(m_direction, units = "rad", desc = "Direction of external force on node")

        # for i in range(self.options["n_loads"]):
        #     n_load_out = "load{}_out".format(i)
        #     self.declare_partials(n_load_out, "load*", method = "fd")
        #     self.declare_partials(n_load_out, "direction*", method = "fd")
        #     if (self.options["n_external_forces"] > 0):

        #         self.declare_partials(n_load_out, "force*", method = "fd")

        self.declare_partials('*', '*', method='cs')

    def apply_nonlinear(self, inputs, outputs, residuals):

        residuals["load0_out"] = 0
        residuals["load1_out"] = 0
        for n in range(self.options["n_loads"]+self.options['n_reactions']):
            
            load = "load{}_out".format(n)
            direction = "direction{}".format(n)
            residuals["load0_out"] += outputs[load] * np.cos(inputs[direction])
            residuals["load1_out"] += outputs[load] * np.sin(inputs[direction])
        
        for m in range(self.options["n_external_forces"]):
            force = "force{}_ext".format(m)
            direction = "direction{}_ext".format(m)
            residuals["load0_out"] += inputs[force] * np.cos(inputs[direction])
            residuals["load1_out"] += inputs[force] * np.sin(inputs[direction])

        
        for i in range(2,self.options["n_loads"]+self.options['n_reactions']):
            load_in = f"load{i}_in"
            load_out = f"load{i}_out"
            residuals[load_out] = outputs[load_out] - inputs[load_in]
            # print(self.pathname, load_out,  outputs[load_out] - inputs[load_in], residuals[load_out])

    # def linearize(self, inputs, outputs, partials):
        
    #     for n in range(self.options["n_loads"] + self.options["n_reactions"]):

    #         load = "load{}_out".format(n)
    #         direction = "direction{}".format(n)
    #         partials["load0_out", load] = np.cos(inputs[direction])
    #         partials["load0_out", direction] = -outputs[load] * np.sin(inputs[direction])
    #         partials["load1_out", load] = np.sin(inputs[direction])
    #         partials["load1_out", direction] = outputs[load] * np.cos(inputs[direction])

    #     for m in range(self.options["n_external_forces"]):
    #         force = "force{}_ext".format(m)
    #         direction = "direction{}_ext".format(m)
    #         partials["load0_out", force] = np.cos(inputs[direction])
    #         partials["load0_out", direction] = -inputs[force] * np.sin(inputs[direction])
    #         partials["load1_out", force] = np.sin(inputs[direction])
    #         partials["load1_out", direction] = inputs[force] * np.cos(inputs[direction])
        
    #     i = 2
    #     while (i < self.options["n_loads"]):
    #         load_out = "load{}_out".format(i)
    #         load_in = "load{}_in".format(i)
    #         direction = "direction{}".format(i)
    #         partials[load_out, load_out] = -inputs[load_in]
    #         partials[load_out, direction] = outputs[load_out]
    #         i += 1