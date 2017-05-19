# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import logging
from signac.common.validate import cfg as signac_cfg
from signac.common.configobj.validate import Validator
from signac.common.configobj.validate import VdtValueError


logger = logging.getLogger(__name__)

#TODO: make a validator on a per scheduler type basis.
cfg = signac_cfg + """
[flow]
modules=list()
[[environment]]
[[[__many__]]]
_class = string()
type = string()
mpicmd = string()
pattern = string()
"""
