# This file is part of PyEMMA.
#
# Copyright (c) 2015, 2014 Computational Molecular Biology Group, Freie Universitaet Berlin (GER)
#
# PyEMMA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
import unittest
from six.moves import range

import numpy as np
import pyemma.thermo

def tower_sample(distribution):
    cdf = np.cumsum(distribution)
    rnd = np.random.rand() * cdf[-1]
    return np.searchsorted(cdf, rnd)

def generate_trajectory(transition_matrices, bias_energies, K, n_samples, x0):
    """generates a list of TRAM trajs"""

    traj = np.zeros((n_samples,2+bias_energies.shape[0]))
    x = x0
    traj[0,0] = K
    traj[0,1] = x
    traj[0,2:] = bias_energies[:,x]
    h = 1
    for s in range(n_samples-1):
        x_new = tower_sample(transition_matrices[K,x,:])
        x = x_new
        traj[h,0] = K
        traj[h,1] = x
        traj[h,2:] = bias_energies[:,x]
        h += 1
    return traj

def T_matrix(energy):
    n = energy.shape[0]
    metropolis = energy[np.newaxis, :] - energy[:, np.newaxis]
    metropolis[(metropolis < 0.0)] = 0.0
    selection = np.zeros((n,n))
    selection += np.diag(np.ones(n-1)*0.5,k=1)
    selection += np.diag(np.ones(n-1)*0.5,k=-1)
    selection[0,0] = 0.5
    selection[-1,-1] = 0.5
    metr_hast = selection * np.exp(-metropolis)
    for i in range(metr_hast.shape[0]):
        metr_hast[i, i] = 0.0
        metr_hast[i, i] = 1.0 - metr_hast[i, :].sum()
    return metr_hast


class TestTRAM(unittest.TestCase):
    def test_5_state_model(self):
        bias_energies = np.zeros((2,5))
        bias_energies[0,:] = np.array([1.0,0.0,10.0,0.0,1.0])
        bias_energies[1,:] = np.array([100.0,0.0,0.0,0.0,100.0])
        T = np.zeros((2,5,5))
        T[0,:,:] = T_matrix(bias_energies[0,:])
        T[1,:,:] = T_matrix(bias_energies[1,:])

        n_samples = 50000
        trajs = []
        trajs.append(generate_trajectory(T,bias_energies,0,n_samples,0))
        trajs.append(generate_trajectory(T,bias_energies,0,n_samples,4))
        trajs.append(generate_trajectory(T,bias_energies,1,n_samples,2))

        tram = pyemma.thermo.TRAM(lag=1)
        tram.estimate(trajs)

        log_pi_K_i = tram.biased_conf_energies.copy()
        log_pi_K_i[0,:] -= np.min(log_pi_K_i[0,:])
        log_pi_K_i[1,:] -= np.min(log_pi_K_i[1,:])
        
        #import sys
        #print>>sys.stderr, log_pi_K_i
        #print>>sys.stderr, bias_energies

        assert np.allclose(log_pi_K_i, bias_energies, atol=0.1)

if __name__ == "__main__":
    unittest.main()


