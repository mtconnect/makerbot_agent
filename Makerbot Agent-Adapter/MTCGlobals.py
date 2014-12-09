"""
author: Kent Vasko
company: MAYA Design
"""

# *** Samples ***
SAMPLE_ELEMENTS = ["Acceleration", "AccumulatedTime", "Amperage",
                   "Angle", "AngularAcceleration", "AngularVelocity",
                   "AxisFeedrate", "ClockTime", "Concentration",
                   "Conductivity", "Displacement",
                   "ElectricalEnergy", "Flow", "Frequency",
                   "FillLevel", "LinearForce", "Load", "Mass",
                   "PathFeedrate", "PathPosition", "PH", "Position",
                   "PowerFactor", "Pressure", "Resistence",
                   "RotaryVelocity", "SoundLevel", "Strain",
                   "Temperature", "Tilt", "Torque", "Velocity",
                   "Viscosity", "Voltage", "VoltAmpere",
                   "VoltAmpereReactive", "Wattage"
                   ]
# *** Events ***
EVENT_ELEMENTS = ["ActiveAxes", 'ActuatorState', 'Availabilty',
                  "AxisCoupling", 'Block', 'ControllerMode',
                  'CoupledAxes', 'Direction', 'DoorState',
                  'Execution', 'EmergencyStop', 'Line', 'Message',
                  'PalletId', 'PartCount', 'PartId', 'PathMode',
                  'PowerState', 'Program', 'RotaryMode',
                  'ToolAssetId', 'WorkholdingId'
                  ]

# *** Conditions ***
CONDITION_ELEMENTS = ["Normal", "Warning", "Fault", "Unavailable"]
CONDITION_TYPES = ["ACTUATOR", "COMMUNICATIONS", "HARDWARE", "LOGIC_PROGRAM", "MOTION_PROGRAM", "SYSTEM"]
