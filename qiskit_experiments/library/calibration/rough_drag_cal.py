# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Rough drag calibration experiment."""

from typing import Iterable, List, Optional

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.providers.backend import Backend

from qiskit_experiments.framework import ExperimentData
from qiskit_experiments.calibration_management import (
    BaseCalibrationExperiment,
    BackendCalibrations,
)
from qiskit_experiments.calibration_management.update_library import BaseUpdater
from qiskit_experiments.library.characterization.drag import RoughDrag


class RoughDragCal(BaseCalibrationExperiment, RoughDrag):
    """A calibration version of the Drag experiment.

    # section: see_also
        qiskit_experiments.library.characterization.rough_drag.RoughDrag
    """

    def __init__(
        self,
        qubit: int,
        calibrations: BackendCalibrations,
        backend: Optional[Backend] = None,
        schedule_name: str = "x",
        betas: Iterable[float] = None,
        cal_parameter_name: Optional[str] = "β",
        auto_update: bool = True,
        group: str = "default",
    ):
        r"""see class :class:`RoughDrag` for details.

        Args:
            qubit: The qubit for which to run the rough drag calibration.
            calibrations: The calibrations instance with the schedules.
            backend: Optional, the backend to run the experiment on.
            schedule_name: The name of the schedule to calibrate. Defaults to "x".
            betas: A list of drag parameter values to scan. If None is given 51 betas ranging
                from -5 to 5 will be scanned.
            cal_parameter_name: The name of the parameter in the schedule to update.
                Defaults to "β".
            auto_update: Whether or not to automatically update the calibrations. By
                default this variable is set to True.
            group: The group of calibration parameters to use. The default value is "default".
        """
        schedule = calibrations.get_schedule(
            schedule_name, qubit, assign_params={cal_parameter_name: Parameter("β")}, group=group
        )

        super().__init__(
            calibrations,
            qubit,
            schedule=schedule,
            betas=betas,
            backend=backend,
            schedule_name=schedule_name,
            cal_parameter_name=cal_parameter_name,
            auto_update=auto_update,
        )

    def _add_cal_metadata(self, circuits: List[QuantumCircuit]):
        """Add metadata to the circuit to make the experiment data more self contained.

        The following keys are added to each circuit's metadata:
            cal_param_value: The value of the previous calibrated beta.
            cal_param_name: The name of the parameter in the calibrations.
            cal_schedule: The name of the schedule in the calibrations.
            cal_group: The calibration group to which the parameter belongs.
        """

        prev_beta = self._cals.get_parameter_value(
            self._param_name, self.physical_qubits, self._sched_name, self.experiment_options.group
        )

        for circuit in circuits:
            circuit.metadata["cal_param_value"] = prev_beta
            circuit.metadata["cal_param_name"] = self._param_name
            circuit.metadata["cal_schedule"] = self._sched_name
            circuit.metadata["cal_group"] = self.experiment_options.group

    def update_calibrations(self, experiment_data: ExperimentData):
        """Update the beta using the value directly reported from the fit.

        See :class:`DragCalAnalysis` for details on the fit.
        """

        new_beta = BaseUpdater.get_value(
            experiment_data, "beta", self.experiment_options.result_index
        )

        BaseUpdater.add_parameter_value(
            self._cals,
            experiment_data,
            new_beta,
            self._param_name,
            self._sched_name,
            self.experiment_options.group,
        )