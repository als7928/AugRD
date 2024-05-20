from rd.base_classes import ODEblock
import torch
from rd.utils import get_rw_adj


class ConstantODEblock(ODEblock):
  def __init__(self, odefunc, regularization_fns, opt, data, device, t=torch.tensor([0, 1])):
    super(ConstantODEblock, self).__init__(odefunc, regularization_fns, opt, data, device, t)

    self.device = device
    self.odefunc = odefunc(opt['hidden_dim'], opt['hidden_dim'], opt, data, device)

    if (opt['method'] == 'symplectic_euler' or opt['method'] == 'leapfrog'):
      from odeint_geometric import odeint
    elif opt['adjoint']:
      from torchdiffeq import odeint_adjoint as odeint
    else:
      from torchdiffeq import odeint

    self.train_integrator = odeint
    self.test_integrator = odeint
    self.set_tol()

  def forward(self, x, edge_index): 
    edge_index, edge_weight = get_rw_adj(edge_index, edge_weight=None, norm_dim=1,
                                          fill_value=0,
                                          num_nodes=x.shape[0],
                                          dtype=x.dtype)
      
    self.odefunc.edge_index = edge_index.to(self.device)
    self.odefunc.edge_weight = edge_weight.to(self.device)
    self.reg_odefunc.odefunc.edge_index, self.reg_odefunc.odefunc.edge_weight = self.odefunc.edge_index, self.odefunc.edge_weight
    
    t = self.t.type_as(x)

    integrator = self.train_integrator if self.training else self.test_integrator

    reg_states = tuple(torch.zeros(x.size(0)).to(x) for i in range(self.nreg))

    func = self.reg_odefunc if self.training and self.nreg > 0 else self.odefunc
    state = (x,) + reg_states if self.training and self.nreg > 0 else x

    if self.opt["adjoint"] and self.training:
      state_dt = integrator(
        func, state, t,
        method=self.opt['method'],
        options=dict(step_size=self.opt['step_size'], max_iters=self.opt['max_iters']),
        adjoint_method=self.opt['adjoint_method'],
        adjoint_options=dict(step_size=self.opt['adjoint_step_size'], max_iters=self.opt['max_iters']),
        atol=self.atol,
        rtol=self.rtol,
        adjoint_atol=self.atol_adjoint,
        adjoint_rtol=self.rtol_adjoint)

    else:
      state_dt = integrator(
        func, state, t,
        method=self.opt['method'],
        options=dict(step_size=self.opt['step_size'], max_iters=self.opt['max_iters']),
        atol=self.atol,
        rtol=self.rtol)
    if self.training and self.nreg > 0:
      z = state_dt[0][1]
      reg_states = tuple(st[1] for st in state_dt[1:])
      return z, reg_states
    else:
      self.odefunc.inter_step = state_dt
      # print(state_dt[:,0,0])
      z = state_dt[-1]
      return z

  def __repr__(self):
    return self.__class__.__name__ + '( Time Interval ' + str(self.t[0].item()) + ' -> ' + str(self.t[1].item()) \
           + ")"
